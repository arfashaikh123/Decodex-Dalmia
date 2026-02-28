import pandas as pd
import numpy as np

FILE_PATH = "d:/ARFA PROJECTS/Decodex Dalmia/DecodeX_VoltRide_Dataset.xlsx"

def load_data():
    xls = pd.ExcelFile(FILE_PATH)
    rides = pd.read_excel(xls, 'Ride_Level_Data')
    drivers = pd.read_excel(xls, 'Driver_Data')
    demand = pd.read_excel(xls, 'Zone_Hour_Demand')
    charging = pd.read_excel(xls, 'Charging_Stations')
    return rides, drivers, demand, charging

def analyze_demand_supply(rides, f):
    f.write("\n--- Task 1: Demand-Supply Stress Mapping ---\n")
    # Group by City, Zone, Hour
    # Calculate Completion Rate and Avg Surge
    
    # Ensure Ride_Status is clean
    rides['Is_Completed'] = rides['Ride_Status'] == 'Completed'
    
    # Date Range
    f.write(f"Date Range: {rides['Date'].min()} to {rides['Date'].max()}\n")
    
    summary = rides.groupby(['City', 'Pickup_Zone', 'Hour']).agg(
        Total_Requests=('Ride_ID', 'count'),
        Completed_Rides=('Is_Completed', 'sum'),
        Avg_Surge=('Surge_Multiplier', 'mean'),
        Avg_Battery=('EV_Battery_%', 'mean')
    ).reset_index()
    
    summary['Completion_Rate'] = summary['Completed_Rides'] / summary['Total_Requests']
    
    # Filter for significant volume to avoid noise (lowered to 3)
    risk_candidates = summary[summary['Total_Requests'] >= 3].sort_values(by='Completion_Rate', ascending=True)
    
    f.write("Top 5 Risky City-Zone-Time Windows (Lowest Completion Rate):\n")
    f.write(risk_candidates.head(5).to_string())
    
    # Also look for high surge
    high_surge = summary[summary['Total_Requests'] >= 3].sort_values(by='Avg_Surge', ascending=False)
    f.write("\n\nTop 5 High Surge City-Zone-Time Windows:\n")
    f.write(high_surge.head(5).to_string())

def analyze_cancellations(rides, f):
    f.write("\n\n--- Task 2: Cancellation Driver Decomposition ---\n")
    cancelled = rides[rides['Ride_Status'] == 'Cancelled'].copy()
    
    f.write("Cancellation by Reason:\n")
    counts = cancelled['Cancellation_By'].value_counts(normalize=True)
    f.write(counts.to_string())
    
    # Battery analysis for cancellations
    f.write("\n\nAvg Battery % by Cancellation Reason:\n")
    f.write(cancelled.groupby('Cancellation_By')['EV_Battery_%'].mean().to_string())
    
    # Check if 'Driver' cancellations align with low battery
    driver_cancels = cancelled[cancelled['Cancellation_By'] == 'Driver']
    if not driver_cancels.empty:
        f.write(f"\n\nDriver Cancellations - Avg Battery: {driver_cancels['EV_Battery_%'].mean():.2f}%\n")
    
def analyze_fleet_utilization(rides, f):
    f.write("\n\n--- Task 3: Fleet Utilization Efficiency Assessment ---\n")
    
    zone_stats = rides.groupby(['City', 'Pickup_Zone']).agg(
        Total_Rides=('Ride_ID', 'count'),
        Avg_Surge=('Surge_Multiplier', 'mean'),
        Completion_Rate=('Ride_Status', lambda x: (x == 'Completed').mean())
    ).reset_index()
    
    f.write("Zones with Lowest Surge (Potential Oversupply/Low Usage):\n")
    f.write(zone_stats.sort_values(by=['Avg_Surge', 'Total_Rides'], ascending=[True, True]).head(10).to_string())

def analyze_charging(charging, demand, f):
    f.write("\n\n--- Task 4: Charging Infrastructure Stress Analysis ---\n")
    # Focus on available stations
    # subset = charging[charging['Station_ID'].isin([f'CS{i}' for i in range(200, 240)])]
    # Actually just analyze all top wait times
    
    # Join with Zone Demand characteristics
    # Calculate 'Peak_Demand' for each Zone/City from Demand sheet
    zone_peak = demand.groupby(['City', 'Zone']).agg(
        Max_Requests=('Avg_Ride_Requests', 'max'),
        Mean_Requests=('Avg_Ride_Requests', 'mean')
    ).reset_index()
    
    merged = pd.merge(charging, zone_peak, how='left', on=['City', 'Zone'])
    
    # Metric for "Peaky" demand: Max / Mean ratio
    merged['Demand_Peakedness'] = merged['Max_Requests'] / merged['Mean_Requests']
    
    # Sort by Wait Time
    f.write("Top Charging Stations by Wait Time (with Demand Context):\n")
    f.write(merged.sort_values(by='Avg_Wait_Time_Min', ascending=False).head(15).to_string())

def main():
    try:
        rides, drivers, demand, charging = load_data()
        with open("analysis_results.txt", "w") as f:
            analyze_demand_supply(rides, f)
            analyze_cancellations(rides, f)
            analyze_fleet_utilization(rides, f)
            analyze_charging(charging, demand, f)
    except Exception as e:
        with open("analysis_results.txt", "a") as f:
            f.write(f"\nAn error occurred: {e}")

if __name__ == "__main__":
    main()

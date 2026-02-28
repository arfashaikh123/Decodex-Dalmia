import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# Set style for professional reports
sns.set_theme(style="whitegrid")
plt.rcParams['figure.dpi'] = 300
plt.rcParams['font.family'] = 'sans-serif'

FILE_PATH = "d:/ARFA PROJECTS/Decodex Dalmia/DecodeX_VoltRide_Dataset.xlsx"

def load_data():
    xls = pd.ExcelFile(FILE_PATH)
    rides = pd.read_excel(xls, 'Ride_Level_Data')
    drivers = pd.read_excel(xls, 'Driver_Data')
    demand = pd.read_excel(xls, 'Zone_Hour_Demand')
    charging = pd.read_excel(xls, 'Charging_Stations')
    return rides, drivers, demand, charging

def plot_demand_stress(rides):
    print("Generating Demand Stress Map...")
    rides['Is_Completed'] = rides['Ride_Status'] == 'Completed'
    
    summary = rides.groupby(['City', 'Pickup_Zone', 'Hour']).agg(
        Total_Requests=('Ride_ID', 'count'),
        Completed_Rides=('Is_Completed', 'sum'),
        Avg_Surge=('Surge_Multiplier', 'mean')
    ).reset_index()
    
    summary = summary[summary['Total_Requests'] >= 3] # Filter strictly logic
    summary['Completion_Rate'] = summary['Completed_Rides'] / summary['Total_Requests']
    
    plt.figure(figsize=(10, 6))
    scatter = sns.scatterplot(
        data=summary, 
        x='Avg_Surge', 
        y='Completion_Rate',
        hue='City',
        size='Total_Requests',
        sizes=(20, 200),
        alpha=0.7
    )
    
    plt.title('Demand-Supply Stress Map: Surge vs. Completion Rate', fontsize=14)
    plt.xlabel('Average Surge Multiplier', fontsize=12)
    plt.ylabel('Completion Rate (0-1)', fontsize=12)
    plt.axvline(x=1.5, color='red', linestyle='--', alpha=0.5, label='High Surge Threshold')
    plt.axhline(y=0.5, color='red', linestyle='--', alpha=0.5, label='Low Completion Threshold')
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    plt.savefig('demand_stress.png')
    plt.close()

def plot_cancellation_drivers(rides):
    print("Generating Cancellation Drivers Chart...")
    cancelled = rides[rides['Ride_Status'] == 'Cancelled'].copy()
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    # Pie Chart: Cancellation Reasons
    counts = cancelled['Cancellation_By'].value_counts()
    ax1.pie(counts, labels=counts.index, autopct='%1.1f%%', startangle=140, colors=sns.color_palette('pastel'))
    ax1.set_title('Distribution of Cancellation Reasons', fontsize=14)
    
    # Bar Chart: Avg Battery by Reason
    avg_battery = cancelled.groupby('Cancellation_By')['EV_Battery_%'].mean().reset_index()
    sns.barplot(data=avg_battery, x='Cancellation_By', y='EV_Battery_%', ax=ax2, palette='viridis')
    ax2.set_title('Average Battery % at Time of Cancellation', fontsize=14)
    ax2.set_ylabel('Battery %')
    ax2.set_ylim(0, 100)
    for i, v in enumerate(avg_battery['EV_Battery_%']):
        ax2.text(i, v + 2, f"{v:.1f}%", ha='center', fontsize=10)
        
    plt.tight_layout()
    plt.savefig('cancellation_drivers.png')
    plt.close()

def plot_fleet_utilization(rides):
    print("Generating Fleet Utilization Chart...")
    zone_stats = rides.groupby(['City', 'Pickup_Zone']).agg(
        Total_Rides=('Ride_ID', 'count'),
        Avg_Surge=('Surge_Multiplier', 'mean')
    ).reset_index()
    
    plt.figure(figsize=(10, 6))
    sns.scatterplot(
        data=zone_stats,
        x='Total_Rides',
        y='Avg_Surge',
        hue='City',
        s=100,
        palette='deep'
    )
    
    # Highlight potential oversupply (Low Surge, High Volume)
    plt.axhline(y=1.4, color='green', linestyle='--', alpha=0.5, label='Efficiency Threshold')
    plt.title('Fleet Utilization: Volume vs. Surge Multiplier', fontsize=14)
    plt.xlabel('Total Ride Volume (Demand)', fontsize=12)
    plt.ylabel('Average Surge Multiplier (Supply Strain)', fontsize=12)
    plt.legend()
    plt.tight_layout()
    plt.savefig('fleet_utilization.png')
    plt.close()

def plot_charging_stress(charging, demand):
    print("Generating Charging Stress Chart...")
    zone_peak = demand.groupby(['City', 'Zone']).agg(
        Max_Requests=('Avg_Ride_Requests', 'max'),
        Mean_Requests=('Avg_Ride_Requests', 'mean')
    ).reset_index()
    
    merged = pd.merge(charging, zone_peak, how='left', on=['City', 'Zone'])
    merged['Demand_Peakedness'] = merged['Max_Requests'] / merged['Mean_Requests']
    
    # Top 15 stations by Wait Time
    top_stations = merged.sort_values(by='Avg_Wait_Time_Min', ascending=False).head(15)
    
    plt.figure(figsize=(12, 6))
    norm = plt.Normalize(merged['Demand_Peakedness'].min(), merged['Demand_Peakedness'].max())
    sm = plt.cm.ScalarMappable(cmap="coolwarm", norm=norm)
    sm.set_array([])

    sns.barplot(
        data=top_stations,
        x='Station_ID',
        y='Avg_Wait_Time_Min',
        hue='Demand_Peakedness',
        palette='coolwarm',
        dodge=False 
    )
    
    plt.title('Top Charging Stations by Wait Time (Color = Demand Volatility)', fontsize=14)
    plt.xlabel('Charging Station ID', fontsize=12)
    plt.ylabel('Average Wait Time (Minutes)', fontsize=12)
    plt.xticks(rotation=45)
    
    # Add colorbar manually since hue is continuous mapped cleanly
    cbar = plt.colorbar(sm, ax=plt.gca())
    cbar.set_label('Demand Peakedness (Max/Mean Requests)')
    plt.legend([],[], frameon=False) # Hide default legend
    
    plt.tight_layout()
    plt.savefig('charging_stress.png')
    plt.close()

def main():
    try:
        rides, drivers, demand, charging = load_data()
        plot_demand_stress(rides)
        plot_cancellation_drivers(rides)
        plot_fleet_utilization(rides)
        plot_charging_stress(charging, demand)
        print("All visualizations generated successfully.")
    except Exception as e:
        print(f"Error generating visualizations: {e}")

if __name__ == "__main__":
    main()

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# Set style for professional reports
sns.set_theme(style="white")
plt.rcParams['figure.dpi'] = 300
plt.rcParams['font.family'] = 'sans-serif'

FILE_PATH = "d:/ARFA PROJECTS/Decodex Dalmia/DecodeX_VoltRide_Dataset.xlsx"

def load_data():
    xls = pd.ExcelFile(FILE_PATH)
    rides = pd.read_excel(xls, 'Ride_Level_Data')
    drivers = pd.read_excel(xls, 'Driver_Data')
    return rides, drivers

def analyze_revenue_loss(rides):
    print("Analyzing Lost Revenue...")
    # Filter for uncompleted rides (Cancelled, etc)
    # Be careful: 'Ride_Status' != 'Completed'
    uncompleted = rides[rides['Ride_Status'] != 'Completed'].copy()
    
    # Calculate potential revenue lost
    # If Estimated_Fare is NaN, fill with mean of that Zone-City pair? 
    # For now, drop NaNs or fill with global mean is risky. Let's assume Estimated_Fare is populated.
    
    loss_by_zone = uncompleted.groupby(['City', 'Pickup_Zone'])['Estimated_Fare'].sum().reset_index()
    loss_by_zone.columns = ['City', 'Zone', 'Lost_Revenue']
    
    # Top 10 Money Losing Zones
    top_loss = loss_by_zone.sort_values(by='Lost_Revenue', ascending=False).head(10)
    
    plt.figure(figsize=(12, 6))
    sns.barplot(
        data=top_loss,
        x='Lost_Revenue',
        y='Zone',
        hue='City',
        orient='h',
        palette='Reds_r'
    )
    plt.title('Top 10 Zones by "Lost Revenue" (Uncompleted Rides)', fontsize=14)
    plt.xlabel('Total Estimated Fare Lost (Currency)', fontsize=12)
    plt.ylabel('Pickup Zone', fontsize=12)
    plt.tight_layout()
    plt.savefig('revenue_loss_chart.png')
    plt.close()

def analyze_stress_heatmap(rides):
    print("Generating Stress Heatmap...")
    rides['Is_Completed'] = rides['Ride_Status'] == 'Completed'
    
    # Pivot table: Index=City, Columns=Hour, Values=Completion_Rate
    heatmap_data = rides.pivot_table(
        index='City', 
        columns='Hour', 
        values='Is_Completed', 
        aggfunc='mean'
    )
    
    plt.figure(figsize=(14, 5))
    sns.heatmap(
        heatmap_data, 
        cmap='RdYlGn', 
        annot=True, 
        fmt=".2f", 
        cbar_kws={'label': 'Completion Rate'},
        vmin=0, vmax=1
    )
    plt.title('Operational Reliability Heatmap: City vs. Hour of Day', fontsize=14)
    plt.xlabel('Hour of Day (0-23)', fontsize=12)
    plt.ylabel('City', fontsize=12)
    plt.tight_layout()
    plt.savefig('stress_heatmap.png')
    plt.close()

def analyze_driver_segmentation(drivers):
    print("Segmenting Driver Risk...")
    # Scatter: Experience (X) vs Cancellation Rate (Y)
    # Color regions?
    
    plt.figure(figsize=(10, 6))
    sns.scatterplot(
        data=drivers,
        x='Experience_Months',
        y='Cancellation_Rate_%',
        hue='City',
        alpha=0.6,
        s=60
    )
    
    # Add quadrants
    # Median Experience
    med_exp = drivers['Experience_Months'].median()
    # Median Cancel
    med_cancel = drivers['Cancellation_Rate_%'].median()
    
    plt.axvline(x=med_exp, color='grey', linestyle='--', alpha=0.5)
    plt.axhline(y=med_cancel, color='grey', linestyle='--', alpha=0.5)
    
    plt.text(med_exp + 5, med_cancel + 5, 'High Risk / Senior\n(Burnout?)', fontsize=10, color='red')
    plt.text(med_exp - 20, med_cancel + 5, 'High Risk / Junior\n(Training Need)', fontsize=10, color='orange')
    plt.text(med_exp + 5, med_cancel - 5, 'Star Performers\n(Reliable)', fontsize=10, color='green')
    
    plt.title('Driver Risk Segmentation: Experience vs. Reliability', fontsize=14)
    plt.xlabel('Experience (Months)', fontsize=12)
    plt.ylabel('Cancellation Rate (%)', fontsize=12)
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    plt.savefig('driver_risk_segmentation.png')
    plt.close()

def main():
    try:
        rides, drivers = load_data()
        analyze_revenue_loss(rides)
        analyze_stress_heatmap(rides)
        analyze_driver_segmentation(drivers)
        print("Advanced analysis visualizations generated.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()

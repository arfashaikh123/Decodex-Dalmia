import pandas as pd
import json
import os

# File paths
load_path = r'Train Set\Electric_Load_Data_Train.csv'
factor_path = r'Train Set\External_Factor_Data_Train.csv'
output_dir = 'OUTCOMES/public'
output_file = os.path.join(output_dir, 'data.json')

def prepare_data():
    print("Loading data...")
    load_df = pd.read_csv(load_path)
    factor_df = pd.read_csv(factor_path)
    events_df = pd.read_csv('Events_Data.csv')
    
    print("Merging load and weather data...")
    merged_df = pd.merge(load_df, factor_df, on='DATETIME')
    
    print("Processing timestamps...")
    merged_df['DATETIME'] = pd.to_datetime(merged_df['DATETIME'], format='%d%b%Y:%H:%M:%S')
    
    print("Aggregating to daily averages...")
    merged_df.set_index('DATETIME', inplace=True)
    daily_df = merged_df.resample('D').mean().reset_index()
    
    print("Processing events...")
    # Basic date parsing for events (handling DD-Mon-YY)
    def parse_event_date(date_str):
        try:
            # Try 01-Jan-11 format
            return pd.to_datetime(date_str, format='%d-%b-%y')
        except:
            return None

    events_df['parsed_date'] = events_df['Date'].apply(parse_event_date)
    # Filter out complex ranges for now to avoid errors, or handle simple ones if needed
    cleaned_events = events_df.dropna(subset=['parsed_date'])
    
    # Merge events with daily data
    # Note: Multiple events can happen on one day, we'll take the first for simplicity in the chart
    daily_df['date_key'] = daily_df['DATETIME'].dt.normalize()
    cleaned_events['date_key'] = cleaned_events['parsed_date'].dt.normalize()
    
    event_lookup = cleaned_events.groupby('date_key').agg({
        'Event_Name': lambda x: ', '.join(x.unique()),
        'Holiday_Ind': 'max'
    }).reset_index()
    
    final_df = pd.merge(daily_df, event_lookup, left_on='date_key', right_on='date_key', how='left')
    
    # Fill NaN for days without events
    final_df['Event_Name'] = final_df['Event_Name'].fillna('')
    final_df['Holiday_Ind'] = final_df['Holiday_Ind'].fillna(0)
    
    print("Calculating Data Science Metrics...")
    # Moving Averages
    final_df['LOAD_MA7'] = final_df['LOAD'].rolling(window=7, min_periods=1).mean()
    final_df['LOAD_MA30'] = final_df['LOAD'].rolling(window=30, min_periods=1).mean()
    
    # Lag Features (Predictive Patterns)
    final_df['LOAD_LAG1'] = final_df['LOAD'].shift(1)
    final_df['LOAD_LAG7'] = final_df['LOAD'].shift(7)
    
    # Rolling Correlations (Feature Relationship)
    final_df['CORR_TEMP'] = final_df['LOAD'].rolling(window=30, min_periods=1).corr(final_df['ACT_TEMP'])
    final_df['CORR_HUMIDITY'] = final_df['LOAD'].rolling(window=30, min_periods=1).corr(final_df['ACT_HUMIDITY'])
    
    # Anomaly Detection (2 Sigma)
    rolling_std = final_df['LOAD'].rolling(window=14, min_periods=1).std()
    final_df['is_anomaly'] = ((final_df['LOAD'] - final_df['LOAD_MA7']).abs() > (2 * rolling_std)).astype(int)
    
    # Time Intelligence
    final_df['month'] = daily_df['DATETIME'].dt.month
    final_df['weekday'] = daily_df['DATETIME'].dt.weekday # 0=Mon, 6=Sun
    
    def get_season(month):
        if month in [3, 4, 5]: return 'Spring'
        if month in [6, 7, 8]: return 'Summer'
        if month in [9, 10]: return 'Autumn/Monsoon'
        if month in [11, 12, 1, 2]: return 'Winter'
        return 'Unknown'
    
    final_df['season'] = final_df['month'].apply(get_season)
    
    # Format date for JSON
    final_df['date'] = daily_df['DATETIME'].dt.strftime('%Y-%m-%d')
    
    # Round numbers for smaller JSON
    final_df = final_df.round(3)
    
    # Fill NaN values for JSON safety (especially for rolling correlations)
    final_df = final_df.fillna(0)
    
    # Drop intermediate and non-serializable columns
    final_df = final_df.drop(columns=['date_key', 'DATETIME'])
    
    print(f"Creating output directory {output_dir}...")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    print(f"Saving to {output_file}...")
    data = final_df.to_dict(orient='records')
    with open(output_file, 'w') as f:
        json.dump(data, f)
        
    print(f"Done! Saved {len(data)} records.")

if __name__ == "__main__":
    prepare_data()

import pandas as pd

def robust_date_parser(series):
    """
    Attempts to parse dates using specific formats. 
    1. %d%b%Y:%H:%M:%S (e.g., 01APR2013:00:15:00)
    2. %d-%m-%Y %H:%M (e.g., 13-04-2013 00:00)
    """
    # Try the APR format first
    parsed = pd.to_datetime(series, format='%d%b%Y:%H:%M:%S', errors='coerce')
    
    # Fill in any failed rows using the DD-MM-YYYY format
    mask = parsed.isna()
    if mask.any():
        parsed[mask] = pd.to_datetime(series[mask], dayfirst=True, errors='coerce')
    
    return parsed

# 1. Load the primary datasets
print("Loading datasets...")
electric_load = pd.read_csv('Electric_Load_Data_Train.csv')
external_factors = pd.read_csv('External_Factor_Data_Train.csv')

# Use our robust parser
print("Parsing DATETIME columns...")
electric_load['DATETIME'] = robust_date_parser(electric_load['DATETIME'])
external_factors['DATETIME'] = robust_date_parser(external_factors['DATETIME'])

# Merge the dataframes on the DATETIME column
df = pd.merge(electric_load, external_factors, on='DATETIME', how='inner')
df['DATE_ONLY'] = df['DATETIME'].dt.date

# 2. Load and Clean Events Data
print("Processing Events data...")
events = pd.read_csv('Events_Data.csv')

def parse_event_dates(date_str):
    try:
        if ' to ' in str(date_str):
            start_str, end_str = date_str.split(' to ')
            start_date = pd.to_datetime(start_str, dayfirst=True).date()
            end_date = pd.to_datetime(end_str, dayfirst=True).date()
            return pd.date_range(start_date, end_date).date.tolist()
        else:
            return [pd.to_datetime(date_str, dayfirst=True, errors='coerce').date()]
    except:
        return []

expanded_events = []
for _, row in events.iterrows():
    dates = parse_event_dates(row['Date'])
    for d in dates:
        if pd.notnull(d):
            expanded_events.append({
                'DATE_ONLY': d,
                'Event_Name': row['Event_Name'],
                'Holiday_Ind': row['Holiday_Ind']
            })

events_cleaned = pd.DataFrame(expanded_events).drop_duplicates('DATE_ONLY')

# 3. Final Integration
print("Merging all data...")
final_df = pd.merge(df, events_cleaned, on='DATE_ONLY', how='left')

# Fill missing event data
final_df['Holiday_Ind'] = final_df['Holiday_Ind'].fillna(0).astype(int)
final_df['Event_Name'] = final_df['Event_Name'].fillna('Normal Day')

# 4. REORDER COLUMNS: Move LOAD to the absolute rightmost side
cols = [c for c in final_df.columns if c not in ['LOAD', 'DATE_ONLY']]
final_df = final_df[cols + ['LOAD']]

# Save to CSV
final_df.to_csv('Integrated_Load_Data_Final.csv', index=False)

print("\nSuccess! 'Integrated_Load_Data_Final.csv' created.")
print(f"Total Rows: {len(final_df)}")
print(f"Columns: {final_df.columns.tolist()}")

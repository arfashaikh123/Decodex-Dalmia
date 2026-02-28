import pandas as pd

# Load the datasets
electric_load = pd.read_csv('Electric_Load_Data_Train.csv')
external_factors = pd.read_csv('External_Factor_Data_Train.csv')

# Convert DATETIME to a consistent datetime object for precise merging
# The format is based on '01APR2013:00:15:00'
date_format = '%d%b%Y:%H:%M:%S'
electric_load['DATETIME'] = pd.to_datetime(electric_load['DATETIME'], format=date_format)
external_factors['DATETIME'] = pd.to_datetime(external_factors['DATETIME'], format=date_format)

# Merge the dataframes on the DATETIME column
# An 'inner' join ensures we only keep rows where both load and external factors exist
merged_df = pd.merge(electric_load, external_factors, on='DATETIME', how='inner')

# Reorder columns to make LOAD the last column (standard for dependent variables/labels)
# Also sorting by DATETIME to maintain chronological order
merged_df = merged_df.sort_values(by='DATETIME')

cols = [c for c in merged_df.columns if c not in ['LOAD', 'DATETIME']]
# Standard structure: [Timestamp, Features..., Target]
final_df = merged_df[['DATETIME'] + cols + ['LOAD']]

# Save to a new formatted CSV
final_df.to_csv('Formatted_Load_Data.csv', index=False)

print("Merged CSV created successfully: 'Formatted_Load_Data.csv'")
print("\nFirst 5 rows of the merged data:")
print(final_df.head())

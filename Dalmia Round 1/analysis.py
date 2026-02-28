import pandas as pd
import numpy as np

def analyze_csv(path, name):
    print(f"\n--- Analysis for {name} ---")
    try:
        df = pd.read_csv(path)
        print(f"Shape: {df.shape}")
        print("\nFirst 5 rows:")
        print(df.head())
        print("\nDescriptive Statistics:")
        print(df.describe(include='all'))
        print("\nNull Values:")
        print(df.isnull().sum())
        
        if 'DATETIME' in df.columns:
            print("\nDate Range:")
            print(f"Min: {df['DATETIME'].min()}")
            print(f"Max: {df['DATETIME'].max()}")
            
        return df
    except Exception as e:
        print(f"Error analyzing {name}: {e}")
        return None

# File paths
events_path = r'd:\ARFA PROJECTS\Decodex Dalmia\Dalmia Round 1\Events_Data.csv'
load_path = r'd:\ARFA PROJECTS\Decodex Dalmia\Dalmia Round 1\Train Set\Electric_Load_Data_Train.csv'
factor_path = r'd:\ARFA PROJECTS\Decodex Dalmia\Dalmia Round 1\Train Set\External_Factor_Data_Train.csv'

# Perform analysis
events_df = analyze_csv(events_path, "Events_Data.csv")
load_df = analyze_csv(load_path, "Electric_Load_Data_Train.csv")
factor_df = analyze_csv(factor_path, "External_Factor_Data_Train.csv")

# Correlation analysis if possible
if load_df is not None and factor_df is not None:
    print("\n--- Correlation Analysis ---")
    # Merge on DATETIME
    merged_df = pd.merge(load_df, factor_df, on='DATETIME')
    print(f"Merged Shape: {merged_df.shape}")
    
    # Calculate correlations (only numeric columns)
    numeric_merged = merged_df.select_dtypes(include=[np.number])
    correlations = numeric_merged.corr()['LOAD'].sort_values(ascending=False)
    print("\nCorrelation with LOAD:")
    print(correlations)

# Events summary
if events_df is not None:
    print("\n--- Events Summary ---")
    print(events_df['Holiday_Ind'].value_counts())
    print("\nSample Events:")
    print(events_df['Event_Name'].unique()[:10])

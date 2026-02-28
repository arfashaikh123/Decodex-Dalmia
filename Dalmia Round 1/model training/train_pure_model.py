import pandas as pd
import numpy as np
import lightgbm as lgb
import os
import pickle
from sklearn.model_selection import train_test_split

# 1. Load Data
data_path = 'Integrated_Load_Data_Final.csv'
if not os.path.exists(data_path):
    print(f"Data file {data_path} not found.")
    exit(1)

df = pd.read_csv(data_path)
df['DATETIME'] = pd.to_datetime(df['DATETIME'], format='mixed', dayfirst=True)

# 2. Re-calculate engineered features (copying from forecast_logic.py)
def engineer_features(df):
    df = df.copy()
    # Basic Time Features
    df['hour'] = df['DATETIME'].dt.hour
    df['minute'] = df['DATETIME'].dt.minute
    df['day_of_week'] = df['DATETIME'].dt.dayofweek
    df['day_of_month'] = df['DATETIME'].dt.day
    df['month'] = df['DATETIME'].dt.month
    df['year'] = df['DATETIME'].dt.year
    df['week_of_year'] = df['DATETIME'].dt.isocalendar().week.astype(int)
    df['quarter'] = df['DATETIME'].dt.quarter
    df['time_slot'] = df['hour'] * 4 + df['minute'] // 15
    df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
    
    # Cyclic Transformations
    df['hour_sin'] = np.sin(2 * np.pi * df['hour']/24)
    df['hour_cos'] = np.cos(2 * np.pi * df['hour']/24)
    df['month_sin'] = np.sin(2 * np.pi * (df['month']-1)/12)
    df['month_cos'] = np.cos(2 * np.pi * (df['month']-1)/12)
    df['dow_sin'] = np.sin(2 * np.pi * df['day_of_week']/7)
    df['dow_cos'] = np.cos(2 * np.pi * df['day_of_week']/7)
    
    # Interactions
    df['temp_humidity'] = df['ACT_TEMP'] * df['ACT_HUMIDITY']
    df['heat_index_sq'] = df['ACT_HEAT_INDEX']**2
    df['cool_factor_sq'] = df['COOL_FACTOR']**2
    
    # Label Encoding (assuming existing label_encoder_event.pkl is present)
    with open('label_encoder_event.pkl', 'rb') as f:
        le = pickle.load(f)
    
    # Ensure all event names are covered
    df['Event_Encoded'] = le.transform(df['Event_Name'])
    return df

df = engineer_features(df)

# 3. Define Pure Feature Columns (NO LAGS)
feature_cols = [
    'ACT_HEAT_INDEX', 'ACT_HUMIDITY', 'ACT_RAIN', 'ACT_TEMP', 'COOL_FACTOR', 
    'Holiday_Ind', 'hour', 'minute', 'day_of_week', 'day_of_month', 'month', 
    'year', 'week_of_year', 'quarter', 'time_slot', 'is_weekend', 
    'hour_sin', 'hour_cos', 'month_sin', 'month_cos', 'dow_sin', 'dow_cos', 
    'Event_Encoded', 'temp_humidity', 'heat_index_sq', 'cool_factor_sq'
]

# 4. Train Models
X = df[feature_cols]
y = df['LOAD']

params = {
    'objective': 'quantile',
    'metric': 'quantile',
    'boosting_type': 'gbdt',
    'num_leaves': 128,        # Doubled for maximum detail
    'learning_rate': 0.02,    # Slower learning for better plateauing
    'feature_fraction': 0.8,
    'bagging_fraction': 0.8,
    'bagging_freq': 5,
    'verbose': -1
}

print("Running Maximum Optimization (2000 rounds)...")
for quantile, label in zip([0.1, 0.5, 0.9], ['P10', 'P50', 'P90']):
    print(f"Deep Training {label} on 280k+ samples...")
    q_params = params.copy()
    q_params['alpha'] = quantile
    
    dtrain = lgb.Dataset(X, label=y)
    # Increased rounds to 2000 for maximum possible detail
    model = lgb.train(q_params, dtrain, num_boost_round=2000) 
    model.save_model(f'lgbm_quantile_{label}.txt')

# 5. Save new feature columns
with open('feature_columns.txt', 'w') as f:
    for col in feature_cols:
        f.write(f"{col}\n")

print("Successfully trained pure feature models and updated feature_columns.txt")

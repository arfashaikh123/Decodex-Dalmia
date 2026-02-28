"""
Quick retrain script - Generate models for Stage 2
"""
import pandas as pd
import numpy as np
import lightgbm as lgb
import os
from datetime import datetime

print("="*70)
print(" QUICK RETRAIN - STAGE 2 PREPARATION")
print("="*70)

# Load integrated data
print("\n[1/3] Loading training data...")
df = pd.read_csv('Integrated_Load_Events_Data.csv')
df['DATETIME'] = pd.to_datetime(df['DATETIME'])

# Filter training period (up to Jan 2021)
train_data = df[df['DATETIME'] < '2021-02-01']
val_data = df[(df['DATETIME'] >= '2021-02-01') & (df['DATETIME'] < '2021-05-01')]

print(f"  Training: {len(train_data):,} rows (2013-Jan 2021)")
print(f"  Validation: {len(val_data):,} rows (Feb-Apr 2021)")

# Features
FEATURES = [
    'year', 'month', 'day', 'hour', 'minute', 'dayofweek', 'dayofyear', 
    'weekofyear', 'quarter', 'is_weekend', 'time_of_day',
    'sin_hour', 'cos_hour', 'sin_month', 'cos_month', 'is_peak', 'is_holiday',
    'ACT_TEMP', 'ACT_HUMIDITY', 'ACT_RAIN', 'ACT_HEAT_INDEX', 'COOL_FACTOR',
    'temp_humidity', 'heat_rain',
    'load_lag_2d', 'load_lag_3d', 'load_lag_7d', 'load_lag_14d',
    'load_rolling_mean_7d', 'load_rolling_std_7d', 'load_rolling_max_7d', 'load_rolling_min_7d',
    'daily_mean', 'daily_max', 'daily_min', 'daily_std',
]

# Prepare data
train_clean = train_data.dropna(subset=FEATURES + ['LOAD'])
X_train = train_clean[FEATURES]
y_train = train_clean['LOAD']

print(f"\n[2/3] Training models (3-5 min)...")
print(f"  Features: {len(FEATURES)}")
print(f"  Training rows: {len(X_train):,}")

# Model 1: MSE
params_mse = {
    'objective': 'regression',
    'metric': 'rmse',
    'learning_rate': 0.05,
    'num_leaves': 31,
    'verbose': -1,
    'seed': 42,
}
train_mse = lgb.Dataset(X_train, y_train)
model_mse = lgb.train(params_mse, train_mse, num_boost_round=300)
model_mse.save_model('outputs/model_mse.txt')
print(f"  ✅ MSE model saved")

# Model 2: Quantile 0.67
params_q67 = {
    'objective': 'quantile',
    'alpha': 0.667,
    'metric': 'quantile',
    'learning_rate': 0.05,
    'num_leaves': 31,
    'verbose': -1,
    'seed': 42,
}
model_q67 = lgb.train(params_q67, train_mse, num_boost_round=300)
model_q67.save_model('outputs/model_quantile_67.txt')
print(f"  ✅ Q0.67 model saved")

# Model 3: Quantile 0.90
params_q90 = {
    'objective': 'quantile',
    'alpha': 0.90,
    'metric': 'quantile',
    'learning_rate': 0.05,
    'num_leaves': 31,
    'verbose': -1,
    'seed': 42,
}
model_q90 = lgb.train(params_q90, train_mse, num_boost_round=300)
model_q90.save_model('outputs/model_quantile_90.txt')
print(f"  ✅ Q0.90 model saved")

print(f"\n[3/3] Models ready for Stage 2 prediction!")
print(f"\n📌 Next: Run predict_test_set.py to generate Stage 2 results")
print("="*70)

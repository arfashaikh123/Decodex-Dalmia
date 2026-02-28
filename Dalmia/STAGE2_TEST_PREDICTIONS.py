"""
GRIDSHIELD Stage 2 - Complete Pipeline
Loads raw test data, trains models, generates predictions, calculates penalties
"""

import pandas as pd
import numpy as np
import lightgbm as lgb
import os
from datetime import datetime

print("="*70)
print(" GRIDSHIELD STAGE 2 - COMPLETE PREDICTION PIPELINE")
print("="*70)

# ===========================================================================
# 1. LOAD & ENGINEER TRAINING DATA
# ===========================================================================
print("\n[1/6] Loading and engineering training data...")
train_df = pd.read_csv('Integrated_Load_Events_Data.csv')
train_df['DATETIME'] = pd.to_datetime(train_df['DATETIME'])

print(f"  Loaded {len(train_df):,} training rows")

# Filter up to April 2021 (before test period)
train_df = train_df[train_df['DATETIME'] < '2021-05-01'].copy()

# Time features
train_df['year'] = train_df['DATETIME'].dt.year
train_df['month'] = train_df['DATETIME'].dt.month
train_df['day'] = train_df['DATETIME'].dt.day
train_df['hour'] = train_df['DATETIME'].dt.hour
train_df['minute'] = train_df['DATETIME'].dt.minute
train_df['dayofweek'] = train_df['DATETIME'].dt.dayofweek
train_df['dayofyear'] = train_df['DATETIME'].dt.dayofyear
train_df['weekofyear'] = train_df['DATETIME'].dt.isocalendar().week.astype(int)
train_df['quarter'] = train_df['DATETIME'].dt.quarter
train_df['is_weekend'] = (train_df['dayofweek'] >= 5).astype(int)
train_df['time_of_day'] = train_df['hour'] + train_df['minute']/60.0
train_df['sin_hour'] = np.sin(2 * np.pi * train_df['hour'] / 24)
train_df['cos_hour'] = np.cos(2 * np.pi * train_df['hour'] / 24)
train_df['sin_month'] = np.sin(2 * np.pi * train_df['month'] / 12)
train_df['cos_month'] = np.cos(2 * np.pi * train_df['month'] / 12)
train_df['is_peak'] = ((train_df['hour'] >= 18) & (train_df['hour'] < 22)).astype(int)
train_df['is_holiday'] = train_df['Event_Name'].str.contains('Holiday|Din|Festival', case=False, na=False).astype(int)

# Weather interactions
train_df['temp_humidity'] = train_df['ACT_TEMP'] * train_df['ACT_HUMIDITY']
train_df['heat_rain'] = train_df['ACT_HEAT_INDEX'] * train_df['ACT_RAIN']

# NO LAG FEATURES - Not relevant for test set without historical data
# Using only time and weather features for better generalization

FEATURES = [
    # Time features (cyclic patterns)
    'year', 'month', 'day', 'hour', 'minute', 'dayofweek', 'dayofyear',
    'weekofyear', 'quarter', 'is_weekend', 'time_of_day',
    'sin_hour', 'cos_hour', 'sin_month', 'cos_month', 'is_peak', 'is_holiday',
    # Weather features (actual drivers)
    'ACT_TEMP', 'ACT_HUMIDITY', 'ACT_RAIN', 'ACT_HEAT_INDEX', 'COOL_FACTOR',
    'temp_humidity', 'heat_rain',
]

train_clean = train_df[FEATURES + ['LOAD']].dropna()
print(f"  Engineered features, {len(train_clean):,} clean rows ready")

# ===========================================================================
# 2. TRAIN MODELS
# ===========================================================================
print("\n[2/6] Training models (1-2 min)...")

X_train = train_clean[FEATURES]
y_train = train_clean['LOAD']

train_data = lgb.Dataset(X_train, y_train)

# MSE model
params_mse = {'objective': 'regression', 'metric': 'rmse', 'learning_rate': 0.05, 'num_leaves': 255, 'verbose': -1, 'seed': 42}
model_mse = lgb.train(params_mse, train_data, num_boost_round=150)
print("  ✅ MSE model trained")

# Q0.67 model
params_q67 = {'objective': 'quantile', 'alpha': 0.667, 'metric': 'quantile', 'learning_rate': 0.05, 'num_leaves': 255, 'verbose': -1, 'seed': 42}
model_q67 = lgb.train(params_q67, train_data, num_boost_round=150)
print("  ✅ Q0.67 model trained")

# Q0.90 model
params_q90 = {'objective': 'quantile', 'alpha': 0.90, 'metric': 'quantile', 'learning_rate': 0.05, 'num_leaves': 255, 'verbose': -1, 'seed': 42}
model_q90 = lgb.train(params_q90, train_data, num_boost_round=150)
print("  ✅ Q0.90 model trained")

# ===========================================================================
# 3. LOAD & ENGINEER TEST DATA
# ===========================================================================
print("\n[3/6] Loading and engineering test data...")

test_load = pd.read_csv('Test Set/Electric_Load_Data_Test.csv')
test_ext = pd.read_csv('Test Set/External_Factor_Data_Test.csv')

test_load['DATETIME'] = pd.to_datetime(test_load['DATETIME'], format='%d%b%Y:%H:%M:%S')
test_ext['DATETIME'] = pd.to_datetime(test_ext['DATETIME'], format='%d%b%Y:%H:%M:%S')

test_df = test_load.merge(test_ext, on='DATETIME', how='inner')
print(f"  Loaded {len(test_df):,} test rows (May 2021)")

# Engineer same features as training
test_df['year'] = test_df['DATETIME'].dt.year
test_df['month'] = test_df['DATETIME'].dt.month
test_df['day'] = test_df['DATETIME'].dt.day
test_df['hour'] = test_df['DATETIME'].dt.hour
test_df['minute'] = test_df['DATETIME'].dt.minute
test_df['dayofweek'] = test_df['DATETIME'].dt.dayofweek
test_df['dayofyear'] = test_df['DATETIME'].dt.dayofyear
test_df['weekofyear'] = test_df['DATETIME'].dt.isocalendar().week.astype(int)
test_df['quarter'] = test_df['DATETIME'].dt.quarter
test_df['is_weekend'] = (test_df['dayofweek'] >= 5).astype(int)
test_df['time_of_day'] = test_df['hour'] + test_df['minute']/60.0
test_df['sin_hour'] = np.sin(2 * np.pi * test_df['hour'] / 24)
test_df['cos_hour'] = np.cos(2 * np.pi * test_df['hour'] / 24)
test_df['sin_month'] = np.sin(2 * np.pi * test_df['month'] / 12)
test_df['cos_month'] = np.cos(2 * np.pi * test_df['month'] / 12)
test_df['is_peak'] = ((test_df['hour'] >= 18) & (test_df['hour'] < 22)).astype(int)
test_df['is_holiday'] = (test_df['DATETIME'].dt.date == pd.Timestamp('2021-05-01').date()).astype(int)

test_df['temp_humidity'] = test_df['ACT_TEMP'] * test_df['ACT_HUMIDITY']
test_df['heat_rain'] = test_df['ACT_HEAT_INDEX'] * test_df['ACT_RAIN']

# NO LAG FEATURES - Using only weather and time patterns
# This improves generalization to unseen test period

print("  ✅ Features engineered (time + weather only, no lags)")

# ===========================================================================
# 4. GENERATE PREDICTIONS
# ===========================================================================
print("\n[4/6] Generating predictions...")

X_test = test_df[FEATURES]
y_actual = test_df['LOAD'].values

pred_mse = model_mse.predict(X_test)
pred_q67 = model_q67.predict(X_test)
pred_q90 = model_q90.predict(X_test)
pred_hybrid = np.where(test_df['is_peak'] == 1, pred_q90, pred_q67)

# Naive baseline: use training mean (no historical lags available for May)
pred_naive = np.full(len(test_df), train_clean['LOAD'].mean())

print(f"  ✅ Generated predictions for {len(pred_mse):,} timesteps")

# ===========================================================================
# 5. CALCULATE PENALTIES
# ===========================================================================
print("\n[5/6] Calculating Stage 2 penalties...")

PENALTY_UNDER = 4.0
PENALTY_OVER = 2.0

def calc_penalty(actual, forecast, is_peak):
    error = actual - forecast
    under = np.maximum(error, 0)
    over = np.maximum(-error, 0)
    
    total = (under * PENALTY_UNDER + over * PENALTY_OVER).sum()
    peak_pen = (under[is_peak==1] * PENALTY_UNDER + over[is_peak==1] * PENALTY_OVER).sum()
    offpeak_pen = (under[is_peak==0] * PENALTY_UNDER + over[is_peak==0] * PENALTY_OVER).sum()
    
    mae = np.mean(np.abs(error))
    rmse = np.sqrt(np.mean(error**2))
    mape = np.mean(np.abs(error/actual)) * 100
    bias = np.mean(error)
    
    return {
        'total': total,
        'peak': peak_pen,
        'offpeak': offpeak_pen,
        'mae': mae,
        'rmse': rmse,
        'mape': mape,
        'bias': bias,
    }

is_peak = test_df['is_peak'].values

results = {
    'Naive': calc_penalty(y_actual, pred_naive, is_peak),
    'MSE': calc_penalty(y_actual, pred_mse, is_peak),
    'Q0.67': calc_penalty(y_actual, pred_q67, is_peak),
    'Q0.90': calc_penalty(y_actual, pred_q90, is_peak),
    'HYBRID': calc_penalty(y_actual, pred_hybrid, is_peak),
}

print("\n" + "="*90)
print(" STAGE 2 TEST RESULTS - MAY 2021")
print("="*90)
print(f"{'Strategy':<15} {'Total INR':<15} {'Peak INR':<15} {'Off-Peak INR':<15} {'MAE':<8} {'MAPE':<8}")
print("-"*90)

for name, r in results.items():
    print(f"{name:<15} Rs{r['total']:>12,.0f}  Rs{r['peak']:>12,.0f}  Rs{r['offpeak']:>12,.0f}  {r['mae']:>6.1f}  {r['mape']:>5.2f}%")

print("="*90)

naive_pen = results['Naive']['total']
hybrid_pen = results['HYBRID']['total']
improvement = (naive_pen - hybrid_pen) / naive_pen * 100

print(f"\nGRIDSHIELD vs Naive: {improvement:.1f}% penalty reduction")
print(f"   Rs{naive_pen:,.0f} -> Rs{hybrid_pen:,.0f} (Rs{naive_pen - hybrid_pen:,.0f} savings)")

# ===========================================================================
# 6. SAVE OUTPUTS
# ===========================================================================
print("\n[6/6] Saving outputs...")

os.makedirs('outputs', exist_ok=True)

# Predictions CSV
out_df = test_df[['DATETIME', 'LOAD', 'is_peak']].copy()
out_df['Pred_MSE'] = pred_mse
out_df['Pred_Q67'] = pred_q67
out_df['Pred_Q90'] = pred_q90
out_df['Pred_HYBRID'] = pred_hybrid
out_df.to_csv('outputs/stage2_test_predictions.csv', index=False)
print("  Saved: outputs/stage2_test_predictions.csv")

# Results summary
results_df = pd.DataFrame([
    {'Strategy': name, 'Total_Penalty_INR': r['total'], 'Peak_Penalty_INR': r['peak'],
     'OffPeak_Penalty_INR': r['offpeak'], 'MAE_kW': r['mae'], 'RMSE_kW': r['rmse'],
     'MAPE_pct': r['mape'], 'Bias_kW': r['bias']}
    for name, r in results.items()
])
results_df.to_csv('outputs/stage2_results_summary.csv', index=False)
print("  Saved: outputs/stage2_results_summary.csv")

print("\n" + "="*70)
print(" STAGE 2 COMPLETE!")
print("="*70)
print(f"\nKEY FINDINGS:")
print(f"  Test period: May 2021 (31 days, 2,977 timesteps)")
print(f"  Best strategy: {min(results, key=lambda k: results[k]['total'])}")
print(f"  Penalty reduction: {improvement:.1f}% vs Naive baseline")
print(f"  Model generalization: {'GOOD' if improvement > 40 else 'NEEDS REVIEW'}")
print(f"\nNext Steps:")
print(f"  1. Review: outputs/stage2_results_summary.csv")
print(f"  2. Prepare: 5-slide Stage 2 interim brief (due 11 PM tonight)")
print(f"  3. Email: decodex.cases@nldalmia.edu.in")
print("")

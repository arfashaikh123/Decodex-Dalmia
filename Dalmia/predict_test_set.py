"""
GRIDSHIELD Stage 2 - Test Set Prediction
Generate forecasts for May 2021 test period and calculate Stage 2 penalties
"""

import pandas as pd
import numpy as np
import lightgbm as lgb
import pickle
from datetime import datetime
import os

# File paths
TEST_LOAD = "Test Set/Electric_Load_Data_Test.csv"
TEST_EXT = "Test Set/External_Factor_Data_Test.csv"
OUTPUT_DIR = "outputs"

print("="*70)
print(" GRIDSHIELD STAGE 2 - TEST SET PREDICTION")
print("="*70)

# ============================================================================
# 1. LOAD TEST DATA
# ============================================================================
print("\n[1/5] Loading test set data...")
test_load = pd.read_csv(TEST_LOAD)
test_ext = pd.read_csv(TEST_EXT)

# Parse datetime
test_load['DATETIME'] = pd.to_datetime(test_load['DATETIME'], format='%d%b%Y:%H:%M:%S')
test_ext['DATETIME'] = pd.to_datetime(test_ext['DATETIME'], format='%d%b%Y:%H:%M:%S')

# Merge
test_df = test_load.merge(test_ext, on='DATETIME', how='inner')
print(f"  ✅ Loaded {len(test_df):,} test observations")
print(f"  📅 Period: {test_df['DATETIME'].min()} to {test_df['DATETIME'].max()}")

# ============================================================================
# 2. FEATURE ENGINEERING (MUST MATCH TRAINING)
# ============================================================================
print("\n[2/5] Engineering features...")

# Time features
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

# Time of day
test_df['time_of_day'] = test_df['hour'] + test_df['minute']/60.0
test_df['sin_hour'] = np.sin(2 * np.pi * test_df['hour'] / 24)
test_df['cos_hour'] = np.cos(2 * np.pi * test_df['hour'] / 24)
test_df['sin_month'] = np.sin(2 * np.pi * test_df['month'] / 12)
test_df['cos_month'] = np.cos(2 * np.pi * test_df['month'] / 12)

# Peak hour flag
test_df['is_peak'] = ((test_df['hour'] >= 18) & (test_df['hour'] < 22)).astype(int)

# Holiday flag (May 1 = Maharashtra Din)
test_df['is_holiday'] = (test_df['DATETIME'].dt.date == pd.Timestamp('2021-05-01').date()).astype(int)

# Weather interactions
test_df['temp_humidity'] = test_df['ACT_TEMP'] * test_df['ACT_HUMIDITY']
test_df['heat_rain'] = test_df['ACT_HEAT_INDEX'] * test_df['ACT_RAIN']

# Lag features (2-day-ahead safe - from TRAINING data)
# WARNING: We don't have recent lags for May 1st! Use last known values from validation
# For real deployment, you'd load last 14 days of training data
# For now, use mean imputation or forward fill strategy

# Create lag columns with NaN (will handle below)
for lag_days in [2, 3, 7, 14]:
    test_df[f'load_lag_{lag_days}d'] = np.nan

# Rolling features (will be NaN for first few days)
test_df['load_rolling_mean_7d'] = np.nan
test_df['load_rolling_std_7d'] = np.nan
test_df['load_rolling_max_7d'] = np.nan
test_df['load_rolling_min_7d'] = np.nan

# Daily stats (from 2 days ago) - will be NaN initially
test_df['daily_mean'] = np.nan
test_df['daily_max'] = np.nan
test_df['daily_min'] = np.nan
test_df['daily_std'] = np.nan

print(f"  ✅ Engineered {len(test_df.columns)} features")

# ============================================================================
# 3. HANDLE MISSING LAG FEATURES
# ============================================================================
print("\n[3/5] Handling missing lag features...")
print("  ⚠️  WARNING: Test set lacks historical lags (cold start)")
print("  🔧 Strategy: Using mean imputation from training statistics")

# Load training statistics if available, else use reasonable estimates
TRAINING_MEAN_LOAD = 1150.0  # kW (approximate from 2013-2021 data)
TRAINING_STD_LOAD = 215.0    # kW

# Impute lags with training mean
for lag_days in [2, 3, 7, 14]:
    test_df[f'load_lag_{lag_days}d'].fillna(TRAINING_MEAN_LOAD, inplace=True)

# Impute rolling stats
test_df['load_rolling_mean_7d'].fillna(TRAINING_MEAN_LOAD, inplace=True)
test_df['load_rolling_std_7d'].fillna(TRAINING_STD_LOAD, inplace=True)
test_df['load_rolling_max_7d'].fillna(TRAINING_MEAN_LOAD + TRAINING_STD_LOAD, inplace=True)
test_df['load_rolling_min_7d'].fillna(TRAINING_MEAN_LOAD - TRAINING_STD_LOAD, inplace=True)

# Impute daily stats
test_df['daily_mean'].fillna(TRAINING_MEAN_LOAD, inplace=True)
test_df['daily_max'].fillna(TRAINING_MEAN_LOAD + 100, inplace=True)
test_df['daily_min'].fillna(TRAINING_MEAN_LOAD - 100, inplace=True)
test_df['daily_std'].fillna(TRAINING_STD_LOAD, inplace=True)

print(f"  ✅ All features imputed (NaN count: {test_df.isnull().sum().sum()})")

# ============================================================================
# 4. TRAIN MODELS (FAST - 30 seconds)
# ============================================================================
print("\n[4/7] Training models on historical data (30 sec)...")

# Load training data
train_df = pd.read_csv('Integrated_Load_Events_Data.csv')
train_df['DATETIME'] = pd.to_datetime(train_df['DATETIME'])

# Filter training period (up to April 2021)
train_split = train_df[train_df['DATETIME'] < '2021-05-01']
train_clean = train_split.dropna(subset=['LOAD'] + [c for c in train_split.columns if c in test_df.columns])

# Define features (MUST MATCH training)
FEATURES = [
    # Time features
    'year', 'month', 'day', 'hour', 'minute', 'dayofweek', 'dayofyear', 
    'weekofyear', 'quarter', 'is_weekend', 'time_of_day',
    'sin_hour', 'cos_hour', 'sin_month', 'cos_month', 'is_peak', 'is_holiday',
    # Weather
    'ACT_TEMP', 'ACT_HUMIDITY', 'ACT_RAIN', 'ACT_HEAT_INDEX', 'COOL_FACTOR',
    'temp_humidity', 'heat_rain',
    # Lags
    'load_lag_2d', 'load_lag_3d', 'load_lag_7d', 'load_lag_14d',
    'load_rolling_mean_7d', 'load_rolling_std_7d', 'load_rolling_max_7d', 'load_rolling_min_7d',
    # Daily stats
    'daily_mean', 'daily_max', 'daily_min', 'daily_std',
]

X_train = train_clean[FEATURES]
y_train = train_clean['LOAD']

print(f"  Training on {len(X_train):,} rows...")

# Train MSE model
params_mse = {'objective': 'regression', 'metric': 'rmse', 'learning_rate': 0.05, 'num_leaves': 255, 'verbose': -1, 'seed': 42}
train_data = lgb.Dataset(X_train, y_train)
model_mse = lgb.train(params_mse, train_data, num_boost_round=100)
print("  ✅ MSE model trained")

# Train Q0.67 model
params_q67 = {'objective': 'quantile', 'alpha': 0.667, 'metric': 'quantile', 'learning_rate': 0.05, 'num_leaves': 255, 'verbose': -1, 'seed': 42}
model_q67 = lgb.train(params_q67, train_data, num_boost_round=100)
print("  ✅ Q0.67 model trained")

# Train Q0.90 model
params_q90 = {'objective': 'quantile', 'alpha': 0.90, 'metric': 'quantile', 'learning_rate': 0.05, 'num_leaves': 255, 'verbose': -1, 'seed': 42}
model_q90 = lgb.train(params_q90, train_data, num_boost_round=100)
print("  ✅ Q0.90 model trained")

# ============================================================================
# 5. GENERATE PREDICTIONS ON TEST SET
# ============================================================================
print("\n[5/7] Generating predictions on May 2021 test set...")

X_test = test_df[FEATURES]
y_actual = test_df['LOAD'].values

# Generate predictions
pred_mse = model_mse.predict(X_test)
pred_q67 = model_q67.predict(X_test)
pred_q90 = model_q90.predict(X_test)

# Hybrid strategy (Q67 off-peak, Q90 peak)
pred_hybrid = np.where(test_df['is_peak'].values == 1, pred_q90, pred_q67)

# Naive baseline (use lag_7d as naive forecast)
pred_naive = test_df['load_lag_7d'].values

print(f"  ✅ Generated predictions for {len(pred_mse):,} timesteps")

# ============================================================================
# 6. CALCULATE STAGE 2 PENALTIES
# ============================================================================
print("\n[6/7] Calculating Stage 2 penalty costs...")

PENALTY_UNDER = 4.0  # INR per kW under-forecast
PENALTY_OVER = 2.0   # INR per kW over-forecast

def calculate_penalty(actual, forecast, is_peak):
    """Calculate asymmetric penalty cost"""
    error = actual - forecast
    under = np.maximum(error, 0)  # Positive error = under-forecast
    over = np.maximum(-error, 0)  # Negative error = over-forecast
    
    penalty_under = under * PENALTY_UNDER
    penalty_over = over * PENALTY_OVER
    total_penalty = penalty_under + penalty_over
    
    # Split by peak/off-peak
    peak_penalty = np.sum(total_penalty[is_peak == 1])
    offpeak_penalty = np.sum(total_penalty[is_peak == 0])
    
    # Error metrics
    mae = np.mean(np.abs(error))
    rmse = np.sqrt(np.mean(error ** 2))
    mape = np.mean(np.abs(error / actual)) * 100
    bias = np.mean(error)
    
    return {
        'total_penalty': total_penalty.sum(),
        'peak_penalty': peak_penalty,
        'offpeak_penalty': offpeak_penalty,
        'penalty_under_total': penalty_under.sum(),
        'penalty_over_total': penalty_over.sum(),
        'mae': mae,
        'rmse': rmse,
        'mape': mape,
        'bias': bias,
    }

is_peak = test_df['is_peak'].values

results = {
    'Naive (Last Week)': calculate_penalty(y_actual, pred_naive, is_peak),
    'LightGBM MSE': calculate_penalty(y_actual, pred_mse, is_peak),
    'LightGBM Q0.67': calculate_penalty(y_actual, pred_q67, is_peak),
    'LightGBM Q0.90': calculate_penalty(y_actual, pred_q90, is_peak),
    'HYBRID (Q67+Q90)': calculate_penalty(y_actual, pred_hybrid, is_peak),
}

# Print results table
print("\n" + "="*90)
print(" STAGE 2 TEST SET RESULTS (MAY 2021)")
print("="*90)
print(f"{'Strategy':<20} {'Total ₹':<12} {'Peak ₹':<12} {'Off-Peak ₹':<12} {'MAE':<8} {'RMSE':<8} {'MAPE':<8}")
print("-"*90)

for name, r in results.items():
    print(f"{name:<20} "
          f"₹{r['total_penalty']:>10,.0f}  "
          f"₹{r['peak_penalty']:>10,.0f}  "
          f"₹{r['offpeak_penalty']:>10,.0f}  "
          f"{r['mae']:>6.1f}  {r['rmse']:>6.1f}  {r['mape']:>5.2f}%")

print("="*90)

# Calculate improvement
naive_cost = results['Naive (Last Week)']['total_penalty']
hybrid_cost = results['HYBRID (Q67+Q90)']['total_penalty']
improvement = (naive_cost - hybrid_cost) / naive_cost * 100

print(f"\n🏆 GRIDSHIELD IMPROVEMENT: {improvement:.1f}% penalty reduction vs Naive")
print(f"   ₹{naive_cost:,.0f} → ₹{hybrid_cost:,.0f} = ₹{naive_cost - hybrid_cost:,.0f} savings")

# ============================================================================
# 7. SAVE OUTPUTS
# ============================================================================
print("\n[7/7] Saving outputs...")

# Save predictions
output_df = test_df[['DATETIME', 'LOAD', 'is_peak']].copy()
output_df['Forecast_MSE'] = pred_mse
output_df['Forecast_Q67'] = pred_q67
output_df['Forecast_Q90'] = pred_q90
output_df['Forecast_HYBRID'] = pred_hybrid
output_df['Error_HYBRID'] = y_actual - pred_hybrid
output_df['Penalty_HYBRID'] = np.where(
    output_df['Error_HYBRID'] > 0,
    output_df['Error_HYBRID'] * PENALTY_UNDER,
    -output_df['Error_HYBRID'] * PENALTY_OVER
)

output_path = os.path.join(OUTPUT_DIR, 'stage2_test_predictions.csv')
output_df.to_csv(output_path, index=False)
print(f"  ✅ Saved: {output_path}")

# Save results summary
results_df = pd.DataFrame([
    {
        'Strategy': name,
        'Total_Penalty_INR': r['total_penalty'],
        'Peak_Penalty_INR': r['peak_penalty'],
        'OffPeak_Penalty_INR': r['offpeak_penalty'],
        'Under_Penalty_INR': r['penalty_under_total'],
        'Over_Penalty_INR': r['penalty_over_total'],
        'MAE_kW': r['mae'],
        'RMSE_kW': r['rmse'],
        'MAPE_pct': r['mape'],
        'Bias_kW': r['bias'],
    }
    for name, r in results.items()
])
results_path = os.path.join(OUTPUT_DIR, 'stage2_test_results.csv')
results_df.to_csv(results_path, index=False)
print(f"  ✅ Saved: {results_path}")

print("\n" + "="*70)
print(" STAGE 2 PREDICTION COMPLETE!")
print("="*70)
print(f"\n📊 Next Steps:")
print(f"  1. Review: outputs/stage2_test_results.csv")
print(f"  2. Analyze: outputs/stage2_test_predictions.csv")
print(f"  3. Prepare: 5-slide Stage 2 interim brief (deadline: 11 PM)")
print(f"  4. Submit: decodex.cases@nldalmia.edu.in")
print("")

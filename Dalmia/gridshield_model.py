"""
GRIDSHIELD Case 2 - Stage 1: Cost-Aware Load Forecasting Model
===============================================================
Lumina Energy | Mumbai Suburban Distribution Zone
Objective: Minimize financial penalty under ABT regulations
    Under-forecast penalty: ₹4/kWh
    Over-forecast penalty:  ₹2/kWh
    Optimal quantile: 4/(4+2) = 0.667
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import mean_absolute_error, mean_squared_error
import lightgbm as lgb
import warnings
import os
import json

warnings.filterwarnings('ignore')
np.random.seed(42)

BASE_DIR = r'c:\Users\mansu\Downloads\02 – Case GRIDSHIELD'
OUTPUT_DIR = os.path.join(BASE_DIR, 'outputs')
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Penalty constants
PENALTY_UNDER = 4  # ₹/kWh when Actual > Forecast
PENALTY_OVER = 2   # ₹/kWh when Forecast > Actual
OPTIMAL_QUANTILE = PENALTY_UNDER / (PENALTY_UNDER + PENALTY_OVER)  # 0.667

print("="*70)
print("GRIDSHIELD - Stage 1: Cost-Aware Load Forecasting")
print("="*70)

# ======================================================================
# 1. DATA LOADING & PREPROCESSING
# ======================================================================
print("\n[1/6] Loading data...")

df = pd.read_csv(os.path.join(BASE_DIR, 'Integrated_Load_Events_Data.csv'))
df['DATETIME'] = pd.to_datetime(df['DATETIME'])
df = df.sort_values('DATETIME').reset_index(drop=True)

print(f"  Data shape: {df.shape}")
print(f"  Date range: {df['DATETIME'].min()} to {df['DATETIME'].max()}")
print(f"  Total days: {(df['DATETIME'].max() - df['DATETIME'].min()).days}")
print(f"  Missing LOAD: {df['LOAD'].isna().sum()}")
print(f"  Load range: {df['LOAD'].min():.0f} - {df['LOAD'].max():.0f} kW")

# ======================================================================
# 2. FEATURE ENGINEERING
# ======================================================================
print("\n[2/6] Engineering features...")

# -- Temporal features --
df['hour'] = df['DATETIME'].dt.hour
df['minute'] = df['DATETIME'].dt.minute
df['time_slot'] = df['hour'] * 4 + df['minute'] // 15  # 0-95 (96 slots/day)
df['day_of_week'] = df['DATETIME'].dt.dayofweek  # 0=Mon, 6=Sun
df['day_of_month'] = df['DATETIME'].dt.day
df['month'] = df['DATETIME'].dt.month
df['year'] = df['DATETIME'].dt.year
df['week_of_year'] = df['DATETIME'].dt.isocalendar().week.astype(int)
df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)
df['quarter'] = df['DATETIME'].dt.quarter

# Cyclical encoding
df['hour_sin'] = np.sin(2 * np.pi * df['time_slot'] / 96)
df['hour_cos'] = np.cos(2 * np.pi * df['time_slot'] / 96)
df['dow_sin'] = np.sin(2 * np.pi * df['day_of_week'] / 7)
df['dow_cos'] = np.cos(2 * np.pi * df['day_of_week'] / 7)
df['month_sin'] = np.sin(2 * np.pi * df['month'] / 12)
df['month_cos'] = np.cos(2 * np.pi * df['month'] / 12)

# -- Peak hour flag (6 PM - 10 PM) --
df['is_peak'] = ((df['hour'] >= 18) & (df['hour'] < 22)).astype(int)

# -- COVID / Regime indicator --
covid_start = pd.Timestamp('2020-03-24')
df['is_post_covid'] = (df['DATETIME'] >= covid_start).astype(int)

# Lockdown phases (more granular)
df['lockdown_phase'] = 0
df.loc[(df['DATETIME'] >= '2020-03-24') & (df['DATETIME'] < '2020-06-01'), 'lockdown_phase'] = 1  # Strict lockdown
df.loc[(df['DATETIME'] >= '2020-06-01') & (df['DATETIME'] < '2020-11-01'), 'lockdown_phase'] = 2  # Unlock phases
df.loc[(df['DATETIME'] >= '2020-11-01') & (df['DATETIME'] < '2021-02-01'), 'lockdown_phase'] = 3  # Night curfew era
df.loc[(df['DATETIME'] >= '2021-02-01'), 'lockdown_phase'] = 4  # Recovery/new normal

# -- Holiday feature (already in data) --
df['Holiday_Ind'] = df['Holiday_Ind'].fillna(0).astype(int)

# -- Event type encoding --
df['is_normal_day'] = (df['Event_Name'] == 'Normal Day').astype(int)
df['is_festival'] = df['Event_Name'].str.contains(
    'Ganesh|Navratri|Diwali|Laxmi|Dussera|Holi|Dhulivandan', 
    case=False, na=False
).astype(int)
df['is_lockdown_event'] = df['Event_Name'].str.contains(
    'Lockdown|Curfew|Unlock|WFH', 
    case=False, na=False
).astype(int)
df['is_rain_event'] = df['Event_Name'].str.contains(
    'Rain', case=False, na=False
).astype(int)

# -- Weather-derived features --
df['temp_humidity_interaction'] = df['ACT_TEMP'] * df['ACT_HUMIDITY'] / 100
df['cool_factor_sq'] = df['COOL_FACTOR'] ** 2  # Non-linear cooling effect
df['is_hot'] = (df['ACT_TEMP'] > 30).astype(int)
df['is_rainy'] = (df['ACT_RAIN'] > 0).astype(int)
df['heat_stress'] = np.maximum(df['ACT_HEAT_INDEX'] - 30, 0)  # Heat above comfort

# -- LAG FEATURES (must be >=48h old for 2-day-ahead forecast!) --
# 48h = 192 slots, 7 days = 672 slots
print("  Creating lag features (2-day-ahead safe)...")
for lag_days in [2, 3, 7, 14]:
    lag_slots = lag_days * 96
    df[f'load_lag_{lag_days}d'] = df['LOAD'].shift(lag_slots)

# Same time last week
df['load_lag_7d'] = df['LOAD'].shift(7 * 96)

# Rolling stats (using 48h-old data minimum)
df['load_rolling_mean_7d'] = df['LOAD'].shift(192).rolling(window=7*96, min_periods=96).mean()
df['load_rolling_std_7d'] = df['LOAD'].shift(192).rolling(window=7*96, min_periods=96).std()
df['load_rolling_max_7d'] = df['LOAD'].shift(192).rolling(window=7*96, min_periods=96).max()
df['load_rolling_min_7d'] = df['LOAD'].shift(192).rolling(window=7*96, min_periods=96).min()

# Weather rolling (current is OK since weather forecast is available ahead)
df['temp_rolling_6h'] = df['ACT_TEMP'].rolling(window=24, min_periods=1).mean()
df['humidity_rolling_6h'] = df['ACT_HUMIDITY'].rolling(window=24, min_periods=1).mean()

# -- Daily load profile stats from 2 days ago --
df['date'] = df['DATETIME'].dt.date
daily_stats = df.groupby('date')['LOAD'].agg(['mean', 'max', 'min', 'std']).reset_index()
daily_stats.columns = ['date', 'daily_mean', 'daily_max', 'daily_min', 'daily_std']
df['date_for_merge'] = (df['DATETIME'] - pd.Timedelta(days=2)).dt.date
df = df.merge(daily_stats, left_on='date_for_merge', right_on='date', how='left', suffixes=('', '_lag2d'))
df.drop(columns=['date_lag2d', 'date_for_merge'], inplace=True, errors='ignore')

print(f"  Total features created: {len(df.columns)}")

# ======================================================================
# 3. EDA PLOTS
# ======================================================================
print("\n[3/6] Generating EDA plots...")

fig, axes = plt.subplots(2, 3, figsize=(20, 10))

# Plot 1: Load over time (monthly avg)
monthly = df.groupby(df['DATETIME'].dt.to_period('M'))['LOAD'].mean()
axes[0,0].plot(monthly.index.astype(str), monthly.values, linewidth=0.7)
axes[0,0].set_title('Monthly Avg Load Over Time')
axes[0,0].tick_params(axis='x', rotation=90)
axes[0,0].axvline(x='2020-03', color='red', linestyle='--', label='COVID')
axes[0,0].set_ylabel('Load (kW)')
axes[0,0].legend()
# Reduce x ticks
ticks = list(range(0, len(monthly), 6))
axes[0,0].set_xticks(ticks)
axes[0,0].set_xticklabels([monthly.index.astype(str)[i] for i in ticks], rotation=45)

# Plot 2: Average daily load curve (weekday vs weekend)
weekday_profile = df[df['is_weekend']==0].groupby('time_slot')['LOAD'].mean()
weekend_profile = df[df['is_weekend']==1].groupby('time_slot')['LOAD'].mean()
axes[0,1].plot(weekday_profile.index, weekday_profile.values, label='Weekday')
axes[0,1].plot(weekend_profile.index, weekend_profile.values, label='Weekend')
axes[0,1].set_title('Avg Daily Load Profile')
axes[0,1].set_xlabel('Time Slot (15-min)')
axes[0,1].set_ylabel('Load (kW)')
axes[0,1].axvspan(72, 88, alpha=0.2, color='red', label='Peak 6-10 PM')
axes[0,1].legend()

# Plot 3: Temperature vs Load
sample = df.sample(n=5000, random_state=42)
axes[0,2].scatter(sample['ACT_TEMP'], sample['LOAD'], alpha=0.2, s=5)
axes[0,2].set_title('Temperature vs Load')
axes[0,2].set_xlabel('Temperature (°C)')
axes[0,2].set_ylabel('Load (kW)')

# Plot 4: COOL_FACTOR vs Load
axes[1,0].scatter(sample['COOL_FACTOR'], sample['LOAD'], alpha=0.2, s=5, c='orange')
axes[1,0].set_title('COOL_FACTOR vs Load')
axes[1,0].set_xlabel('COOL_FACTOR')
axes[1,0].set_ylabel('Load (kW)')

# Plot 5: Pre-COVID vs Post-COVID daily curves
pre = df[df['DATETIME'] < '2020-01-01'].groupby('time_slot')['LOAD'].mean()
post = df[df['DATETIME'] >= '2020-06-01'].groupby('time_slot')['LOAD'].mean()
axes[1,1].plot(pre.index, pre.values, label='Pre-COVID (2013-2019)')
axes[1,1].plot(post.index, post.values, label='Post-COVID (Jun 2020+)')
axes[1,1].set_title('COVID Impact on Load Curve')
axes[1,1].set_xlabel('Time Slot')
axes[1,1].set_ylabel('Load (kW)')
axes[1,1].legend()

# Plot 6: Monthly seasonal pattern
monthly_pattern = df.groupby('month')['LOAD'].mean()
axes[1,2].bar(monthly_pattern.index, monthly_pattern.values, color='teal')
axes[1,2].set_title('Avg Load by Month (Seasonal)')
axes[1,2].set_xlabel('Month')
axes[1,2].set_ylabel('Load (kW)')

plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, 'eda_plots.png'), dpi=150)
plt.close()
print("  Saved: outputs/eda_plots.png")

# ======================================================================
# 4. MODEL TRAINING
# ======================================================================
print("\n[4/6] Training cost-aware forecasting model...")

# Define features
FEATURES = [
    # Temporal
    'time_slot', 'day_of_week', 'month', 'year', 'is_weekend', 'quarter',
    'hour_sin', 'hour_cos', 'dow_sin', 'dow_cos', 'month_sin', 'month_cos',
    'is_peak', 'day_of_month',
    # Weather
    'ACT_TEMP', 'ACT_HUMIDITY', 'ACT_RAIN', 'ACT_HEAT_INDEX', 'COOL_FACTOR',
    'temp_humidity_interaction', 'cool_factor_sq', 'is_hot', 'is_rainy', 'heat_stress',
    'temp_rolling_6h', 'humidity_rolling_6h',
    # Events
    'Holiday_Ind', 'is_normal_day', 'is_festival', 'is_lockdown_event', 'is_rain_event',
    # Regime
    'is_post_covid', 'lockdown_phase',
    # Lags (2-day-ahead safe)
    'load_lag_2d', 'load_lag_3d', 'load_lag_7d', 'load_lag_14d',
    'load_rolling_mean_7d', 'load_rolling_std_7d', 'load_rolling_max_7d', 'load_rolling_min_7d',
    # Daily stats from 2 days ago
    'daily_mean', 'daily_max', 'daily_min', 'daily_std',
]

TARGET = 'LOAD'

# Drop NaN rows (from lags)
df_model = df.dropna(subset=FEATURES + [TARGET]).copy()
print(f"  Rows after dropping NaN lags: {len(df_model):,} (dropped {len(df) - len(df_model):,})")

# Train/test split: use last 3 months as validation (like out-of-time)
split_date = pd.Timestamp('2021-02-01')
train = df_model[df_model['DATETIME'] < split_date]
test = df_model[df_model['DATETIME'] >= split_date]

print(f"  Train: {len(train):,} rows ({train['DATETIME'].min().date()} to {train['DATETIME'].max().date()})")
print(f"  Test:  {len(test):,} rows ({test['DATETIME'].min().date()} to {test['DATETIME'].max().date()})")

X_train, y_train = train[FEATURES], train[TARGET]
X_test, y_test = test[FEATURES], test[TARGET]

# --- Model A: LightGBM with ASYMMETRIC (Quantile) Loss ---
# Quantile = 0.667 biases forecast upward to minimize cost
print("\n  Training Model A: LightGBM Quantile Regression (q=0.667)...")

params_quantile = {
    'objective': 'quantile',
    'alpha': OPTIMAL_QUANTILE,  # 0.667 → biased toward over-forecasting
    'metric': 'quantile',
    'boosting_type': 'gbdt',
    'num_leaves': 255,
    'learning_rate': 0.05,
    'feature_fraction': 0.8,
    'bagging_fraction': 0.8,
    'bagging_freq': 5,
    'min_child_samples': 50,
    'n_jobs': -1,
    'verbose': -1,
    'seed': 42,
}

train_data = lgb.Dataset(X_train, label=y_train)
val_data = lgb.Dataset(X_test, label=y_test, reference=train_data)

model_quantile = lgb.train(
    params_quantile,
    train_data,
    num_boost_round=2000,
    valid_sets=[val_data],
    callbacks=[lgb.early_stopping(50), lgb.log_evaluation(200)]
)

# --- Model B: LightGBM with standard L2 (for comparison) ---
print("\n  Training Model B: LightGBM MSE (baseline)...")

params_mse = {
    'objective': 'regression',
    'metric': 'rmse',
    'boosting_type': 'gbdt',
    'num_leaves': 255,
    'learning_rate': 0.05,
    'feature_fraction': 0.8,
    'bagging_fraction': 0.8,
    'bagging_freq': 5,
    'min_child_samples': 50,
    'n_jobs': -1,
    'verbose': -1,
    'seed': 42,
}

model_mse = lgb.train(
    params_mse,
    train_data,
    num_boost_round=2000,
    valid_sets=[val_data],
    callbacks=[lgb.early_stopping(50), lgb.log_evaluation(200)]
)

# --- Model C: LightGBM Quantile 0.90 for peak hours (conservative) ---
print("\n  Training Model C: LightGBM Quantile 0.90 (peak-hour conservative)...")

params_q90 = params_quantile.copy()
params_q90['alpha'] = 0.90  

model_q90 = lgb.train(
    params_q90,
    train_data,
    num_boost_round=2000,
    valid_sets=[val_data],
    callbacks=[lgb.early_stopping(50), lgb.log_evaluation(200)]
)

# ======================================================================
# 5. BACKTESTING & PENALTY CALCULATION
# ======================================================================
print("\n[5/6] Backtesting on validation set...")

def calculate_penalties(actual, forecast, is_peak, label=""):
    """Calculate ABT deviation penalties."""
    deviation = actual - forecast  # positive = under-forecast
    
    under_mask = deviation > 0
    over_mask = deviation < 0
    
    # Convert kW per 15-min to kWh: multiply by 0.25
    penalty_under = (deviation[under_mask] * 0.25 * PENALTY_UNDER).sum()
    penalty_over = (-deviation[over_mask] * 0.25 * PENALTY_OVER).sum()
    total_penalty = penalty_under + penalty_over
    
    # Peak vs off-peak
    peak_mask = is_peak == 1
    peak_dev = deviation[peak_mask]
    peak_penalty_under = (peak_dev[peak_dev > 0] * 0.25 * PENALTY_UNDER).sum()
    peak_penalty_over = (-peak_dev[peak_dev < 0] * 0.25 * PENALTY_OVER).sum()
    peak_total = peak_penalty_under + peak_penalty_over
    
    offpeak_total = total_penalty - peak_total
    
    # Bias
    bias = deviation.mean()
    bias_pct = (bias / actual.mean()) * 100
    
    # 95th percentile absolute deviation
    p95_dev = np.percentile(np.abs(deviation), 95)
    
    mae = mean_absolute_error(actual, forecast)
    rmse = np.sqrt(mean_squared_error(actual, forecast))
    mape = (np.abs(deviation) / actual).mean() * 100
    
    results = {
        'label': label,
        'total_penalty_INR': total_penalty,
        'peak_penalty_INR': peak_total,
        'offpeak_penalty_INR': offpeak_total,
        'under_forecast_penalty': penalty_under,
        'over_forecast_penalty': penalty_over,
        'bias_kW': bias,
        'bias_pct': bias_pct,
        'p95_abs_dev_kW': p95_dev,
        'MAE': mae,
        'RMSE': rmse,
        'MAPE': mape,
    }
    return results

# Predictions
pred_quantile = model_quantile.predict(X_test)
pred_mse = model_mse.predict(X_test)
pred_q90 = model_q90.predict(X_test)

# Hybrid strategy: use q90 for peak hours, q67 for off-peak
pred_hybrid = pred_quantile.copy()
peak_idx = test['is_peak'] == 1
pred_hybrid[peak_idx] = pred_q90[peak_idx]

# Naive baseline: same time last week
pred_naive = test['load_lag_7d'].values

is_peak_test = test['is_peak'].values

# Calculate penalties for all strategies
strategies = [
    ('Naive (Same Week Ago)', pred_naive),
    ('LightGBM MSE (Baseline)', pred_mse),
    ('LightGBM Quantile 0.667', pred_quantile),
    ('LightGBM Quantile 0.90', pred_q90),
    ('HYBRID (q67 off-peak + q90 peak)', pred_hybrid),
]

print("\n" + "="*70)
print("BACKTEST RESULTS ON VALIDATION SET (Feb-Apr 2021)")
print("="*70)

all_results = []
for name, preds in strategies:
    r = calculate_penalties(y_test.values, preds, is_peak_test, name)
    all_results.append(r)
    print(f"\n--- {name} ---")
    print(f"  Total Penalty:     ₹{r['total_penalty_INR']:,.0f}")
    print(f"    Peak Penalty:    ₹{r['peak_penalty_INR']:,.0f}")
    print(f"    Off-Peak Penalty:₹{r['offpeak_penalty_INR']:,.0f}")
    print(f"    Under-forecast:  ₹{r['under_forecast_penalty']:,.0f}")
    print(f"    Over-forecast:   ₹{r['over_forecast_penalty']:,.0f}")
    print(f"  Bias:              {r['bias_pct']:+.2f}%")
    print(f"  95th %ile |dev|:   {r['p95_abs_dev_kW']:.1f} kW")
    print(f"  MAE: {r['MAE']:.2f} | RMSE: {r['RMSE']:.2f} | MAPE: {r['MAPE']:.2f}%")

# Best strategy
best = min(all_results, key=lambda x: x['total_penalty_INR'])
naive_penalty = all_results[0]['total_penalty_INR']
print(f"\n{'='*70}")
print(f"BEST STRATEGY: {best['label']}")
print(f"  Total Penalty: ₹{best['total_penalty_INR']:,.0f}")
print(f"  vs Naive: {((best['total_penalty_INR'] - naive_penalty) / naive_penalty * 100):+.1f}% penalty reduction")
print(f"{'='*70}")

# Save results to JSON
results_df = pd.DataFrame(all_results)
results_df.to_csv(os.path.join(OUTPUT_DIR, 'backtest_results.csv'), index=False)

# ======================================================================
# 5b. FEATURE IMPORTANCE
# ======================================================================
importance = pd.DataFrame({
    'feature': FEATURES,
    'importance': model_quantile.feature_importance(importance_type='gain')
}).sort_values('importance', ascending=False)

fig, ax = plt.subplots(figsize=(10, 10))
top20 = importance.head(20)
ax.barh(range(len(top20)), top20['importance'].values)
ax.set_yticks(range(len(top20)))
ax.set_yticklabels(top20['feature'].values)
ax.invert_yaxis()
ax.set_title('Top 20 Feature Importance (Gain)')
ax.set_xlabel('Importance')
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, 'feature_importance.png'), dpi=150)
plt.close()
print("\n  Saved: outputs/feature_importance.png")

# ======================================================================
# 5c. BACKTEST VISUALIZATIONS
# ======================================================================
# Plot actual vs predicted for last 2 weeks of test data
fig, axes = plt.subplots(2, 1, figsize=(18, 10))

last_2w = test.tail(96*14).copy()
last_2w_actual = last_2w[TARGET].values
last_2w_quantile = model_quantile.predict(last_2w[FEATURES])
last_2w_mse = model_mse.predict(last_2w[FEATURES])
last_2w_hybrid = last_2w_quantile.copy()
last_2w_hybrid[last_2w['is_peak'].values == 1] = model_q90.predict(last_2w[FEATURES])[last_2w['is_peak'].values == 1]

axes[0].plot(last_2w['DATETIME'].values, last_2w_actual, label='Actual', linewidth=1, alpha=0.8)
axes[0].plot(last_2w['DATETIME'].values, last_2w_hybrid, label='Hybrid Forecast', linewidth=1, alpha=0.8)
axes[0].set_title('Actual vs Forecast (Last 2 Weeks of Validation)')
axes[0].legend()
axes[0].set_ylabel('Load (kW)')

# Deviation plot
deviation = last_2w_actual - last_2w_hybrid
colors = ['red' if d > 0 else 'green' for d in deviation]
axes[1].bar(range(len(deviation)), deviation, color=colors, alpha=0.6, width=1)
axes[1].set_title('Forecast Deviation (Red=Under-forecast ₹4, Green=Over-forecast ₹2)')
axes[1].set_ylabel('Deviation (kW)')
axes[1].axhline(y=0, color='black', linewidth=0.5)

plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, 'backtest_forecast_vs_actual.png'), dpi=150)
plt.close()
print("  Saved: outputs/backtest_forecast_vs_actual.png")

# Penalty comparison bar chart
fig, ax = plt.subplots(figsize=(12, 6))
names = [r['label'] for r in all_results]
penalties = [r['total_penalty_INR'] for r in all_results]
colors = ['gray', 'steelblue', 'coral', 'orange', 'green']
bars = ax.bar(range(len(names)), penalties, color=colors)
ax.set_xticks(range(len(names)))
ax.set_xticklabels(names, rotation=15, ha='right')
ax.set_ylabel('Total Deviation Penalty (₹)')
ax.set_title('Penalty Comparison Across Strategies')
for bar, val in zip(bars, penalties):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1000, 
            f'₹{val:,.0f}', ha='center', va='bottom', fontsize=9)
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, 'penalty_comparison.png'), dpi=150)
plt.close()
print("  Saved: outputs/penalty_comparison.png")

# ======================================================================
# 6. GENERATE 2-DAY AHEAD FORECAST
# ======================================================================
print("\n[6/6] Generating 2-day ahead forecast...")

# The last date in training data is April 30, 2021
# So we forecast May 1-2, 2021 (192 time slots)
last_datetime = df['DATETIME'].max()
print(f"  Last data point: {last_datetime}")

# Create future datetime index
future_dates = pd.date_range(
    start=last_datetime + pd.Timedelta(minutes=15),
    periods=192,  # 2 days * 96 slots
    freq='15min'
)

future_df = pd.DataFrame({'DATETIME': future_dates})

# Temporal features
future_df['hour'] = future_df['DATETIME'].dt.hour
future_df['minute'] = future_df['DATETIME'].dt.minute
future_df['time_slot'] = future_df['hour'] * 4 + future_df['minute'] // 15
future_df['day_of_week'] = future_df['DATETIME'].dt.dayofweek
future_df['day_of_month'] = future_df['DATETIME'].dt.day
future_df['month'] = future_df['DATETIME'].dt.month
future_df['year'] = future_df['DATETIME'].dt.year
future_df['week_of_year'] = future_df['DATETIME'].dt.isocalendar().week.astype(int)
future_df['is_weekend'] = (future_df['day_of_week'] >= 5).astype(int)
future_df['quarter'] = future_df['DATETIME'].dt.quarter

future_df['hour_sin'] = np.sin(2 * np.pi * future_df['time_slot'] / 96)
future_df['hour_cos'] = np.cos(2 * np.pi * future_df['time_slot'] / 96)
future_df['dow_sin'] = np.sin(2 * np.pi * future_df['day_of_week'] / 7)
future_df['dow_cos'] = np.cos(2 * np.pi * future_df['day_of_week'] / 7)
future_df['month_sin'] = np.sin(2 * np.pi * future_df['month'] / 12)
future_df['month_cos'] = np.cos(2 * np.pi * future_df['month'] / 12)

future_df['is_peak'] = ((future_df['hour'] >= 18) & (future_df['hour'] < 22)).astype(int)
future_df['is_post_covid'] = 1
future_df['lockdown_phase'] = 4  # Recovery/new normal

# May 1 = Maharashtra Din (holiday), May 2 = Normal
future_df['Holiday_Ind'] = 0
future_df.loc[future_df['DATETIME'].dt.day == 1, 'Holiday_Ind'] = 1
future_df['is_normal_day'] = (future_df['Holiday_Ind'] == 0).astype(int)
future_df['is_festival'] = 0
future_df['is_lockdown_event'] = 0
future_df['is_rain_event'] = 0

# Weather: use the average weather from the last week of April as proxy
last_week = df[df['DATETIME'] >= (last_datetime - pd.Timedelta(days=7))]

# For each time_slot, get avg weather from last week
weather_by_slot = last_week.groupby('time_slot').agg({
    'ACT_TEMP': 'mean', 
    'ACT_HUMIDITY': 'mean', 
    'ACT_RAIN': 'mean',
    'ACT_HEAT_INDEX': 'mean',
    'COOL_FACTOR': 'mean',
}).reset_index()

future_df = future_df.merge(weather_by_slot, on='time_slot', how='left')

# Derived weather features
future_df['temp_humidity_interaction'] = future_df['ACT_TEMP'] * future_df['ACT_HUMIDITY'] / 100
future_df['cool_factor_sq'] = future_df['COOL_FACTOR'] ** 2
future_df['is_hot'] = (future_df['ACT_TEMP'] > 30).astype(int)
future_df['is_rainy'] = (future_df['ACT_RAIN'] > 0).astype(int)
future_df['heat_stress'] = np.maximum(future_df['ACT_HEAT_INDEX'] - 30, 0)
future_df['temp_rolling_6h'] = future_df['ACT_TEMP'].rolling(window=24, min_periods=1).mean()
future_df['humidity_rolling_6h'] = future_df['ACT_HUMIDITY'].rolling(window=24, min_periods=1).mean()

# Lag features from historical data
# 2 days ago = April 29-30
for lag_days in [2, 3, 7, 14]:
    lag_start = last_datetime - pd.Timedelta(days=lag_days) + pd.Timedelta(minutes=15)
    lag_data = df[df['DATETIME'] >= lag_start].head(192)
    if len(lag_data) >= 192:
        future_df[f'load_lag_{lag_days}d'] = lag_data['LOAD'].values[:192]
    else:
        # Pad with last available
        vals = lag_data['LOAD'].values
        future_df[f'load_lag_{lag_days}d'] = np.pad(vals, (0, 192 - len(vals)), mode='edge')

# Rolling stats from historical
recent_data = df[df['DATETIME'] <= last_datetime].tail(7 * 96)
future_df['load_rolling_mean_7d'] = recent_data['LOAD'].mean()
future_df['load_rolling_std_7d'] = recent_data['LOAD'].std()
future_df['load_rolling_max_7d'] = recent_data['LOAD'].max()
future_df['load_rolling_min_7d'] = recent_data['LOAD'].min()

# Daily stats from 2 days ago (April 29)
apr29_data = df[df['DATETIME'].dt.date == (last_datetime - pd.Timedelta(days=1)).date()]
if len(apr29_data) > 0:
    future_df['daily_mean'] = apr29_data['LOAD'].mean()
    future_df['daily_max'] = apr29_data['LOAD'].max()
    future_df['daily_min'] = apr29_data['LOAD'].min()
    future_df['daily_std'] = apr29_data['LOAD'].std()
else:
    future_df['daily_mean'] = recent_data['LOAD'].mean()
    future_df['daily_max'] = recent_data['LOAD'].max()
    future_df['daily_min'] = recent_data['LOAD'].min()
    future_df['daily_std'] = recent_data['LOAD'].std()

# Make predictions using all three models
future_df['forecast_quantile_67'] = model_quantile.predict(future_df[FEATURES])
future_df['forecast_mse'] = model_mse.predict(future_df[FEATURES])
future_df['forecast_quantile_90'] = model_q90.predict(future_df[FEATURES])

# Hybrid: q67 for off-peak, q90 for peak
future_df['forecast_hybrid'] = future_df['forecast_quantile_67']
future_df.loc[future_df['is_peak'] == 1, 'forecast_hybrid'] = future_df.loc[future_df['is_peak'] == 1, 'forecast_quantile_90']

# Save forecast
forecast_output = future_df[['DATETIME', 'time_slot', 'is_peak', 
                              'forecast_mse', 'forecast_quantile_67', 
                              'forecast_quantile_90', 'forecast_hybrid']].copy()
forecast_output.columns = ['DATETIME', 'TimeSlot', 'IsPeakHour',
                           'Forecast_MSE', 'Forecast_Q67', 'Forecast_Q90', 'Forecast_HYBRID']
forecast_output = forecast_output.round(2)
forecast_output.to_csv(os.path.join(OUTPUT_DIR, '2day_ahead_forecast.csv'), index=False)
print(f"  Saved: outputs/2day_ahead_forecast.csv")

# Forecast visualization
fig, axes = plt.subplots(2, 1, figsize=(18, 10))

# Day 1
day1 = future_df[future_df['DATETIME'].dt.day == future_dates[0].day]
day2 = future_df[future_df['DATETIME'].dt.day == future_dates[-1].day]

for day_data, ax, day_label in [(day1, axes[0], 'Day 1 (May 1 - Maharashtra Din - Holiday)'), 
                                  (day2, axes[1], 'Day 2 (May 2 - Normal Weekday)')]:
    hours = day_data['DATETIME'].dt.strftime('%H:%M')
    ax.plot(range(len(day_data)), day_data['forecast_mse'], label='MSE Forecast', alpha=0.7)
    ax.plot(range(len(day_data)), day_data['forecast_quantile_67'], label='Quantile 0.67', alpha=0.7)
    ax.plot(range(len(day_data)), day_data['forecast_hybrid'], label='HYBRID (Recommended)', 
            linewidth=2.5, color='green')
    
    # Mark peak hours
    peak_mask = day_data['is_peak'] == 1
    if peak_mask.any():
        peak_start = peak_mask.values.argmax()
        peak_end = len(peak_mask) - peak_mask.values[::-1].argmax()
        ax.axvspan(peak_start, peak_end, alpha=0.15, color='red', label='Peak Hours (6-10 PM)')
    
    ax.set_title(f'2-Day Ahead Forecast: {day_label}')
    ax.set_ylabel('Load (kW)')
    ax.set_xlabel('Time Slot (15-min)')
    ticks_pos = list(range(0, len(day_data), 8))
    ax.set_xticks(ticks_pos)
    ax.set_xticklabels([hours.iloc[i] if i < len(hours) else '' for i in ticks_pos])
    ax.legend()
    ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, '2day_forecast_plot.png'), dpi=150)
plt.close()
print("  Saved: outputs/2day_forecast_plot.png")

# ======================================================================
# FINAL SUMMARY
# ======================================================================
print("\n" + "="*70)
print("STAGE 1 COMPLETE - SUMMARY")
print("="*70)
print(f"""
DATA: Mumbai suburban load, 15-min intervals, Apr 2013 - Apr 2021
      283,392 data points | Weather + Events integrated

MODEL: LightGBM with Asymmetric Cost-Aware Loss
  - Quantile 0.667 (off-peak): Biased upward to minimize ₹4 under-forecast penalty
  - Quantile 0.90 (peak hours): Extra conservative during 6-10 PM
  - Hybrid strategy combines both

KEY FEATURES:
{importance.head(10).to_string(index=False)}

FORECAST: May 1-2, 2021 (2-day ahead, 192 slots)
  - May 1 = Maharashtra Din (Holiday) → Lower commercial load
  - May 2 = Normal Day (Saturday) → Weekend pattern

RISK STRATEGY:
  - Under-forecast penalty (₹4/kWh) is 2x over-forecast (₹2/kWh)
  - Optimal bias: Slightly over-forecast (quantile 0.667)
  - Peak hours: Extra buffer using 90th percentile forecast
  - Expected penalty reduction vs naive: See backtest results above

OUTPUT FILES:
  - outputs/2day_ahead_forecast.csv       → The actual forecast
  - outputs/backtest_results.csv          → Penalty metrics for all strategies
  - outputs/eda_plots.png                 → Exploratory analysis
  - outputs/feature_importance.png        → Top feature drivers
  - outputs/backtest_forecast_vs_actual.png → Actual vs Predicted
  - outputs/penalty_comparison.png        → Strategy penalty comparison
  - outputs/2day_forecast_plot.png        → 2-day forecast visualization
""")

# Save models
model_quantile.save_model(os.path.join(OUTPUT_DIR, 'model_quantile_67.txt'))
model_mse.save_model(os.path.join(OUTPUT_DIR, 'model_mse.txt'))
model_q90.save_model(os.path.join(OUTPUT_DIR, 'model_q90.txt'))
print("  Models saved to outputs/")
print("\nDone! Ready for Stage 2 regime shift at 7:00 PM.")

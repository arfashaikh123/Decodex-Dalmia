"""
GRIDSHIELD Stage 2 - Interactive Date-Based Prediction
Usage: python STAGE2_PREDICT.py
       Prompts for start/end date, predicts, calculates actual penalties
"""

import pandas as pd
import numpy as np
import lightgbm as lgb
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

print("="*70)
print(" GRIDSHIELD - STAGE 2 INTERACTIVE PREDICTOR")
print("="*70)

# ===========================================================================
# 1. LOAD ALL DATA (Training + Test combined for proper lag computation)
# ===========================================================================
print("\n[1/5] Loading all available data...")

# Training data
train_df = pd.read_csv('Integrated_Load_Events_Data.csv')
train_df['DATETIME'] = pd.to_datetime(train_df['DATETIME'])
train_df = train_df[['DATETIME', 'LOAD', 'ACT_TEMP', 'ACT_HUMIDITY', 'ACT_RAIN', 'ACT_HEAT_INDEX', 'COOL_FACTOR', 'Event_Name']].copy()

# Test data (has actual load!)
test_load = pd.read_csv('Test Set/Electric_Load_Data_Test.csv')
test_ext  = pd.read_csv('Test Set/External_Factor_Data_Test.csv')
test_load['DATETIME'] = pd.to_datetime(test_load['DATETIME'], format='%d%b%Y:%H:%M:%S')
test_ext['DATETIME']  = pd.to_datetime(test_ext['DATETIME'],  format='%d%b%Y:%H:%M:%S')
test_df = test_load.merge(test_ext, on='DATETIME', how='inner')
test_df['Event_Name'] = 'Normal Day'

# Stack them all together so lags compute correctly across boundary
full_df = pd.concat([train_df, test_df], ignore_index=True).sort_values('DATETIME').reset_index(drop=True)
print(f"  Combined data: {full_df['DATETIME'].min().date()} → {full_df['DATETIME'].max().date()} ({len(full_df):,} rows)")

# ===========================================================================
# 2. FEATURE ENGINEERING (on full combined dataset)
# ===========================================================================
print("\n[2/5] Engineering features...")

# Time features
full_df['year']       = full_df['DATETIME'].dt.year
full_df['month']      = full_df['DATETIME'].dt.month
full_df['day']        = full_df['DATETIME'].dt.day
full_df['hour']       = full_df['DATETIME'].dt.hour
full_df['minute']     = full_df['DATETIME'].dt.minute
full_df['dayofweek']  = full_df['DATETIME'].dt.dayofweek
full_df['dayofyear']  = full_df['DATETIME'].dt.dayofyear
full_df['weekofyear'] = full_df['DATETIME'].dt.isocalendar().week.astype(int)
full_df['quarter']    = full_df['DATETIME'].dt.quarter
full_df['is_weekend'] = (full_df['dayofweek'] >= 5).astype(int)
full_df['time_of_day']= full_df['hour'] + full_df['minute']/60.0
full_df['sin_hour']   = np.sin(2 * np.pi * full_df['hour'] / 24)
full_df['cos_hour']   = np.cos(2 * np.pi * full_df['hour'] / 24)
full_df['sin_dow']    = np.sin(2 * np.pi * full_df['dayofweek'] / 7)
full_df['cos_dow']    = np.cos(2 * np.pi * full_df['dayofweek'] / 7)
full_df['sin_month']  = np.sin(2 * np.pi * full_df['month'] / 12)
full_df['cos_month']  = np.cos(2 * np.pi * full_df['month'] / 12)
full_df['is_peak']    = ((full_df['hour'] >= 18) & (full_df['hour'] < 22)).astype(int)
full_df['is_holiday'] = full_df['Event_Name'].str.contains('Holiday|Din|Festival|Ganesh|Diwali', case=False, na=False).astype(int)

# Weather interactions
full_df['temp_humidity'] = full_df['ACT_TEMP'] * full_df['ACT_HUMIDITY']
full_df['heat_rain']     = full_df['ACT_HEAT_INDEX'] * full_df['ACT_RAIN']
full_df['temp_sq']       = full_df['ACT_TEMP'] ** 2
full_df['cool_sq']       = full_df['COOL_FACTOR'] ** 2
full_df['is_hot']        = (full_df['ACT_TEMP'] > 30).astype(int)

# Lag features (computed correctly on full combined dataset)
for lag_days in [1, 2, 3, 7, 14]:
    full_df[f'load_lag_{lag_days}d'] = full_df['LOAD'].shift(lag_days * 96)

# Rolling stats  
full_df['load_rolling_mean_7d'] = full_df['LOAD'].shift(2*96).rolling(7*96, min_periods=96).mean()
full_df['load_rolling_std_7d']  = full_df['LOAD'].shift(2*96).rolling(7*96, min_periods=96).std()
full_df['load_rolling_max_7d']  = full_df['LOAD'].shift(2*96).rolling(7*96, min_periods=96).max()

# Daily stats from 2 days ago
full_df['date'] = full_df['DATETIME'].dt.date
daily_stats = full_df.groupby('date')['LOAD'].agg(['mean','max','min','std']).reset_index()
daily_stats.columns = ['date','daily_mean','daily_max','daily_min','daily_std']
full_df['date_lag2'] = (full_df['DATETIME'] - pd.Timedelta(days=2)).dt.date
full_df = full_df.merge(daily_stats, left_on='date_lag2', right_on='date', how='left', suffixes=('','_l'))
full_df.drop(columns=['date','date_lag2','date_l'], inplace=True, errors='ignore')

FEATURES = [
    'year','month','day','hour','minute','dayofweek','dayofyear',
    'weekofyear','quarter','is_weekend','time_of_day',
    'sin_hour','cos_hour','sin_dow','cos_dow','sin_month','cos_month',
    'is_peak','is_holiday',
    'ACT_TEMP','ACT_HUMIDITY','ACT_RAIN','ACT_HEAT_INDEX','COOL_FACTOR',
    'temp_humidity','heat_rain','temp_sq','cool_sq','is_hot',
    'load_lag_1d','load_lag_2d','load_lag_3d','load_lag_7d','load_lag_14d',
    'load_rolling_mean_7d','load_rolling_std_7d','load_rolling_max_7d',
    'daily_mean','daily_max','daily_min','daily_std',
]

print(f"  {len(FEATURES)} features ready")

# ===========================================================================
# 3. TRAIN MODELS (on data before 2021-05-01 only)
# ===========================================================================
print("\n[3/5] Training models on 2013-Apr 2021 data...")

train_mask = full_df['DATETIME'] < '2021-05-01'
train_clean = full_df[train_mask].dropna(subset=FEATURES + ['LOAD'])

X_tr = train_clean[FEATURES]
y_tr = train_clean['LOAD']
lgb_data = lgb.Dataset(X_tr, y_tr)

base_params = {
    'learning_rate': 0.05, 'num_leaves': 255,
    'feature_fraction': 0.8, 'bagging_fraction': 0.8,
    'bagging_freq': 5, 'min_child_samples': 50,
    'verbose': -1, 'seed': 42,
}

model_mse = lgb.train({**base_params,'objective':'regression','metric':'rmse'}, lgb_data, num_boost_round=300)
model_q67 = lgb.train({**base_params,'objective':'quantile','alpha':0.667,'metric':'quantile'}, lgb_data, num_boost_round=300)
model_q90 = lgb.train({**base_params,'objective':'quantile','alpha':0.90,'metric':'quantile'}, lgb_data, num_boost_round=300)
print(f"  ✅ 3 models trained on {len(train_clean):,} rows")

# ===========================================================================
# 4. DATE SELECTION
# ===========================================================================
print("\n" + "="*70)
print(" DATE SELECTION")
print("="*70)
print(f"  Available range: 2013-04-15 to 2021-06-01")
print(f"  Test set available: 2021-05-01 to 2021-06-01 (has actual load)")
print(f"  Training period:    2013-04-15 to 2021-04-30 (has actual load)")
print("")

def get_date(prompt, default):
    val = input(f"  {prompt} [{default}]: ").strip()
    if val == '':
        return pd.Timestamp(default)
    try:
        return pd.Timestamp(val)
    except:
        print(f"  Invalid date, using default: {default}")
        return pd.Timestamp(default)

start_dt = get_date("Start date (YYYY-MM-DD)", "2021-05-01")
end_dt   = get_date("End date   (YYYY-MM-DD)", "2021-05-31")

# Ensure end includes full day
end_dt = end_dt + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)

print(f"\n  Predicting: {start_dt.date()} to {end_dt.date()}")

# ===========================================================================
# 5. PREDICT ON SELECTED PERIOD
# ===========================================================================
print("\n[4/5] Running predictions...")

mask = (full_df['DATETIME'] >= start_dt) & (full_df['DATETIME'] <= end_dt)
pred_df = full_df[mask].copy()

if len(pred_df) == 0:
    print("  ❌ No data found for selected date range!")
    exit(1)

has_actuals = pred_df['LOAD'].notna().all()
print(f"  Rows in range: {len(pred_df):,}")
print(f"  Has actual LOAD: {'Yes - can compute real penalties' if has_actuals else 'No - forecast only mode'}")

# Fill any missing features for prediction
X_pred = pred_df[FEATURES].fillna(full_df[FEATURES].mean())

pred_df = pred_df.copy()
pred_df['Pred_MSE']    = model_mse.predict(X_pred)
pred_df['Pred_Q67']    = model_q67.predict(X_pred)
pred_df['Pred_Q90']    = model_q90.predict(X_pred)
pred_df['Pred_HYBRID'] = np.where(pred_df['is_peak'] == 1, pred_df['Pred_Q90'], pred_df['Pred_Q67'])

# ===========================================================================
# 6. PENALTY CALCULATION (only if actuals available)
# ===========================================================================
PENALTY_UNDER = 4.0
PENALTY_OVER  = 2.0

if has_actuals:
    print("\n[5/5] Calculating penalties...")
    y_actual = pred_df['LOAD'].values
    is_peak  = pred_df['is_peak'].values

    def calc(actual, forecast, is_peak):
        err   = actual - forecast
        under = np.maximum(err, 0)
        over  = np.maximum(-err, 0)
        total = (under*PENALTY_UNDER + over*PENALTY_OVER).sum()
        p_pen = (under[is_peak==1]*PENALTY_UNDER + over[is_peak==1]*PENALTY_OVER).sum()
        o_pen = (under[is_peak==0]*PENALTY_UNDER + over[is_peak==0]*PENALTY_OVER).sum()
        mae   = np.mean(np.abs(err))
        rmse  = np.sqrt(np.mean(err**2))
        mape  = np.mean(np.abs(err/actual))*100
        bias  = np.mean(err)
        p95   = np.percentile(np.abs(err), 95)
        return dict(total=total, peak=p_pen, offpeak=o_pen, mae=mae, rmse=rmse, mape=mape, bias=bias, p95=p95)

    naive_mean = train_clean['LOAD'].mean()
    results = {
        'Naive (mean)': calc(y_actual, np.full(len(y_actual), naive_mean), is_peak),
        'MSE':          calc(y_actual, pred_df['Pred_MSE'].values, is_peak),
        'Q0.67':        calc(y_actual, pred_df['Pred_Q67'].values, is_peak),
        'Q0.90':        calc(y_actual, pred_df['Pred_Q90'].values, is_peak),
        'HYBRID':       calc(y_actual, pred_df['Pred_HYBRID'].values, is_peak),
    }

    print("\n" + "="*95)
    print(f" RESULTS: {start_dt.date()} to {end_dt.date()} ({len(pred_df):,} timesteps)")
    print("="*95)
    print(f"{'Strategy':<18} {'Total INR':>12} {'Peak INR':>12} {'Off-Peak':>12} {'MAE':>7} {'MAPE':>7} {'Bias':>7} {'P95':>7}")
    print("-"*95)
    for name, r in results.items():
        star = " <-- BEST" if r['total'] == min(v['total'] for v in results.values()) else ""
        print(f"{name:<18} Rs{r['total']:>10,.0f} Rs{r['peak']:>10,.0f} Rs{r['offpeak']:>10,.0f} "
              f"{r['mae']:>6.1f}  {r['mape']:>5.2f}%  {r['bias']:>+6.1f}  {r['p95']:>6.1f}{star}")
    print("="*95)

    best = min(results, key=lambda k: results[k]['total'])
    naive_tot = results['Naive (mean)']['total']
    best_tot  = results[best]['total']
    reduction = (naive_tot - best_tot) / naive_tot * 100
    print(f"\n  Best: {best} - {reduction:.1f}% penalty reduction vs Naive")
    print(f"  Accuracy: {100 - results['Q0.67']['mape']:.2f}% (MAPE-based)")

else:
    print("\n  Forecast only mode (no actual load to compare).")

# ===========================================================================
# 7. SAVE OUTPUTS
# ===========================================================================
os.makedirs('outputs', exist_ok=True)

date_tag = f"{start_dt.strftime('%Y%m%d')}_{end_dt.strftime('%Y%m%d')}"

# Save predictions CSV
out_cols = ['DATETIME','LOAD','is_peak','Pred_MSE','Pred_Q67','Pred_Q90','Pred_HYBRID']
pred_df[out_cols].to_csv(f'outputs/predictions_{date_tag}.csv', index=False)
print(f"\n  Saved: outputs/predictions_{date_tag}.csv")

# Plot
fig, axes = plt.subplots(2, 1, figsize=(18, 10))
fig.suptitle(f'GRIDSHIELD Forecast: {start_dt.date()} to {end_dt.date()}', fontsize=14, fontweight='bold')

# First 4 days (or whole range if shorter)
for i, ax in enumerate(axes):
    day_start = start_dt + pd.Timedelta(days=i*7)
    day_end   = day_start + pd.Timedelta(days=7)
    mask_plot = (pred_df['DATETIME'] >= day_start) & (pred_df['DATETIME'] < day_end)
    d = pred_df[mask_plot]
    if len(d) == 0:
        ax.set_visible(False)
        continue
    x = range(len(d))
    if has_actuals:
        ax.plot(x, d['LOAD'],         label='Actual',    color='#89b4fa', linewidth=1.5, alpha=0.9)
    ax.plot(x, d['Pred_HYBRID'], label='HYBRID Q67+Q90', color='#a6e3a1', linewidth=1.5)
    ax.plot(x, d['Pred_Q67'],   label='Q0.67',          color='#f9e2af', linewidth=1,   linestyle='--', alpha=0.7)
    ax.plot(x, d['Pred_Q90'],   label='Q0.90',          color='#fab387', linewidth=1,   linestyle='--', alpha=0.7)
    # Mark peak hours
    peak_mask = d['is_peak'].values == 1
    ax.fill_between(x, ax.get_ylim()[0] if ax.get_ylim()[0] > 0 else 0,
                    d['Pred_HYBRID'].max()*1.05,
                    where=peak_mask, alpha=0.08, color='red', label='Peak hours')
    ax.set_title(f'Week {i+1}: {day_start.date()} - {(day_end - pd.Timedelta(days=1)).date()}')
    ax.set_ylabel('Load (kW)')
    ax.legend(loc='upper right', fontsize=8)
    ax.grid(True, alpha=0.3)

plt.tight_layout()
plot_path = f'outputs/forecast_plot_{date_tag}.png'
plt.savefig(plot_path, dpi=150, bbox_inches='tight')
plt.close()
print(f"  Saved: {plot_path}")

print("\n" + "="*70)
print(" PREDICTION COMPLETE!")
print("="*70)

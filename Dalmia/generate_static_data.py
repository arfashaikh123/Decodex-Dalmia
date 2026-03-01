"""
Generate static JSON data for the GRIDSHIELD Dashboard.
This eliminates the need for the Flask backend — all predictions
are pre-computed and served as static files from the frontend.

Run: python generate_static_data.py
Output: Dashboard/public/data/predictions.json, explain.json, metadata.json
"""

import pandas as pd
import numpy as np
import lightgbm as lgb
import os, json, sys

BASE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(BASE, 'Dashboard', 'public', 'data')
os.makedirs(OUT_DIR, exist_ok=True)

# ─── Feature engineering (same as app.py) ───────────────────────────────────
def engineer_features(df):
    df = df.copy()
    df['year']       = df['DATETIME'].dt.year
    df['month']      = df['DATETIME'].dt.month
    df['day']        = df['DATETIME'].dt.day
    df['hour']       = df['DATETIME'].dt.hour
    df['minute']     = df['DATETIME'].dt.minute
    df['dayofweek']  = df['DATETIME'].dt.dayofweek
    df['dayofyear']  = df['DATETIME'].dt.dayofyear
    df['weekofyear'] = df['DATETIME'].dt.isocalendar().week.astype(int)
    df['quarter']    = df['DATETIME'].dt.quarter
    df['is_weekend'] = (df['dayofweek'] >= 5).astype(int)
    df['time_of_day']= df['hour'] + df['minute'] / 60.0
    df['sin_hour']   = np.sin(2 * np.pi * df['hour'] / 24)
    df['cos_hour']   = np.cos(2 * np.pi * df['hour'] / 24)
    df['sin_dow']    = np.sin(2 * np.pi * df['dayofweek'] / 7)
    df['cos_dow']    = np.cos(2 * np.pi * df['dayofweek'] / 7)
    df['sin_month']  = np.sin(2 * np.pi * df['month'] / 12)
    df['cos_month']  = np.cos(2 * np.pi * df['month'] / 12)
    df['is_peak']    = ((df['hour'] >= 18) & (df['hour'] < 22)).astype(int)
    df['is_holiday'] = df.get('Event_Name', pd.Series('Normal Day', index=df.index)) \
                         .str.contains('Holiday|Din|Festival|Ganesh|Diwali', case=False, na=False).astype(int)
    df['temp_humidity'] = df['ACT_TEMP'] * df['ACT_HUMIDITY']
    df['heat_rain']     = df['ACT_HEAT_INDEX'] * df['ACT_RAIN']
    df['temp_sq']       = df['ACT_TEMP'] ** 2
    df['cool_sq']       = df['COOL_FACTOR'] ** 2
    df['is_hot']        = (df['ACT_TEMP'] > 30).astype(int)
    for lag in [1, 2, 3, 7, 14]:
        if f'load_lag_{lag}d' not in df.columns:
            df[f'load_lag_{lag}d'] = df['LOAD'].shift(lag * 96)
    if 'load_rolling_mean_7d' not in df.columns:
        df['load_rolling_mean_7d'] = df['LOAD'].shift(2*96).rolling(7*96, min_periods=96).mean()
        df['load_rolling_std_7d']  = df['LOAD'].shift(2*96).rolling(7*96, min_periods=96).std()
        df['load_rolling_max_7d']  = df['LOAD'].shift(2*96).rolling(7*96, min_periods=96).max()
    if 'daily_mean' not in df.columns:
        df['date'] = df['DATETIME'].dt.date
        daily = df.groupby('date')['LOAD'].agg(['mean','max','min','std']).reset_index()
        daily.columns = ['date','daily_mean','daily_max','daily_min','daily_std']
        df['date_lag2'] = (df['DATETIME'] - pd.Timedelta(days=2)).dt.date
        df = df.merge(daily, left_on='date_lag2', right_on='date', how='left', suffixes=('','_l'))
        df.drop(columns=['date','date_lag2','date_l'], inplace=True, errors='ignore')
    return df

FEATURE_COLS = [
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

# ─── Load data ──────────────────────────────────────────────────────────────
print("[1/6] Loading data...")
train_df = pd.read_csv(os.path.join(BASE, 'Integrated_Load_Events_Data.csv'))
train_df['DATETIME'] = pd.to_datetime(train_df['DATETIME'])

test_load = pd.read_csv(os.path.join(BASE, 'Test Set', 'Electric_Load_Data_Test.csv'))
test_ext  = pd.read_csv(os.path.join(BASE, 'Test Set', 'External_Factor_Data_Test.csv'))
test_load['DATETIME'] = pd.to_datetime(test_load['DATETIME'], format='%d%b%Y:%H:%M:%S')
test_ext['DATETIME']  = pd.to_datetime(test_ext['DATETIME'],  format='%d%b%Y:%H:%M:%S')
test_df = test_load.merge(test_ext, on='DATETIME', how='inner')
test_df['Event_Name'] = 'Normal Day'

combined = pd.concat([train_df, test_df], ignore_index=True).sort_values('DATETIME').reset_index(drop=True)

print("[2/6] Engineering features...")
combined = engineer_features(combined)

# ─── Train models ───────────────────────────────────────────────────────────
print("[3/6] Training 5 LightGBM models...")
train_mask = combined['DATETIME'] < '2021-05-01'
train_clean = combined[train_mask].dropna(subset=FEATURE_COLS + ['LOAD'])
TRAIN_MEAN = float(train_clean['LOAD'].mean())

X_tr = train_clean[FEATURE_COLS]
y_tr = train_clean['LOAD']
lgb_data = lgb.Dataset(X_tr, y_tr)

base_p = {
    'learning_rate': 0.05, 'num_leaves': 255,
    'feature_fraction': 0.8, 'bagging_fraction': 0.8,
    'bagging_freq': 5, 'min_child_samples': 50,
    'verbose': -1, 'seed': 42,
}

MODELS = {}
for name, params in [
    ('mse', {'objective': 'regression', 'metric': 'rmse'}),
    ('q67', {'objective': 'quantile', 'alpha': 0.667, 'metric': 'quantile'}),
    ('q75', {'objective': 'quantile', 'alpha': 0.75,  'metric': 'quantile'}),
    ('q90', {'objective': 'quantile', 'alpha': 0.90,  'metric': 'quantile'}),
    ('q95', {'objective': 'quantile', 'alpha': 0.95,  'metric': 'quantile'}),
]:
    print(f"  Training {name}...")
    MODELS[name] = lgb.train({**base_p, **params}, lgb_data, num_boost_round=300)

print("  All models trained!")

# ─── Generate predictions for test period ───────────────────────────────────
print("[4/6] Generating predictions for entire test set...")
test_mask = combined['DATETIME'] >= '2021-05-01'
pred_df = combined[test_mask].copy()

X_test = pred_df[FEATURE_COLS].fillna(TRAIN_MEAN)
pred_df['pred_mse'] = MODELS['mse'].predict(X_test)
pred_df['pred_q67'] = MODELS['q67'].predict(X_test)
pred_df['pred_q75'] = MODELS['q75'].predict(X_test)
pred_df['pred_q90'] = MODELS['q90'].predict(X_test)
pred_df['pred_q95'] = MODELS['q95'].predict(X_test)

# Build per-interval prediction records
predictions = []
for _, row in pred_df.iterrows():
    rec = {
        'datetime':    row['DATETIME'].strftime('%Y-%m-%dT%H:%M'),
        'actual':      round(float(row['LOAD']), 1) if pd.notna(row['LOAD']) else None,
        'isPeak':      bool(row['is_peak']),
        'isHoliday':   bool(row['is_holiday']) if pd.notna(row.get('is_holiday', 0)) else False,
        'isWeekend':   bool(row['is_weekend']) if pd.notna(row.get('is_weekend', 0)) else False,
        'predMSE':     round(float(row['pred_mse']), 1),
        'predQ67':     round(float(row['pred_q67']), 1),
        'predQ75':     round(float(row['pred_q75']), 1),
        'predQ90':     round(float(row['pred_q90']), 1),
        'predQ95':     round(float(row['pred_q95']), 1),
        'temperature': round(float(row['ACT_TEMP']), 1) if pd.notna(row.get('ACT_TEMP')) else None,
        'humidity':    round(float(row['ACT_HUMIDITY']), 1) if pd.notna(row.get('ACT_HUMIDITY')) else None,
        'heatIndex':   round(float(row['ACT_HEAT_INDEX']), 1) if pd.notna(row.get('ACT_HEAT_INDEX')) else None,
        'coolFactor':  round(float(row['COOL_FACTOR']), 2) if pd.notna(row.get('COOL_FACTOR')) else None,
        'rain':        round(float(row['ACT_RAIN']), 2) if pd.notna(row.get('ACT_RAIN')) else None,
        'lag7d':       round(float(row['load_lag_7d']), 1) if pd.notna(row.get('load_lag_7d')) else None,
        'rollingMean7d': round(float(row['load_rolling_mean_7d']), 1) if pd.notna(row.get('load_rolling_mean_7d')) else None,
        'rollingStd7d':  round(float(row['load_rolling_std_7d']), 1) if pd.notna(row.get('load_rolling_std_7d')) else None,
    }
    predictions.append(rec)

print(f"  {len(predictions)} intervals generated")

# ─── Compute lookback bias data (day before test set) ───────────────────────
# Pre-compute regime calibration bias for each day in the test period
lookback_biases = {}
for day_offset in range(32):  # May 1-31
    day = pd.Timestamp('2021-05-01') + pd.Timedelta(days=day_offset)
    day_str = day.strftime('%Y-%m-%d')
    lb_start = day - pd.Timedelta(days=1)
    lb_mask = (combined['DATETIME'] >= lb_start) & (combined['DATETIME'] < day)
    lb_df = combined[lb_mask].copy()
    
    if len(lb_df) >= 10 and lb_df['LOAD'].notna().sum() >= 10:
        X_lb = lb_df[FEATURE_COLS].fillna(TRAIN_MEAN)
        # Stage 1 bias
        lb_s1_offpeak = MODELS['q67'].predict(X_lb)
        lb_s1_peak = MODELS['q90'].predict(X_lb)
        is_pk_lb = lb_df['is_peak'].values if 'is_peak' in lb_df.columns else np.zeros(len(lb_df))
        lb_s1_hybrid = np.where(is_pk_lb == 1, lb_s1_peak, lb_s1_offpeak)
        bias_s1 = float(np.nanmean(lb_df['LOAD'].values - lb_s1_hybrid))
        mae_s1 = float(np.nanmean(np.abs(lb_df['LOAD'].values - lb_s1_hybrid)))
        # Stage 2/3 bias
        lb_s2_offpeak = MODELS['q75'].predict(X_lb)
        lb_s2_peak = MODELS['q95'].predict(X_lb)
        lb_s2_hybrid = np.where(is_pk_lb == 1, lb_s2_peak, lb_s2_offpeak)
        bias_s2 = float(np.nanmean(lb_df['LOAD'].values - lb_s2_hybrid))
        mae_s2 = float(np.nanmean(np.abs(lb_df['LOAD'].values - lb_s2_hybrid)))
        
        lookback_biases[day_str] = {
            'stage1': {'bias': round(bias_s1, 2), 'mae': round(mae_s1, 2)},
            'stage2': {'bias': round(bias_s2, 2), 'mae': round(mae_s2, 2)},
        }
    else:
        lookback_biases[day_str] = None

# ─── Compute feature importances & data statistics ──────────────────────────
print("[5/6] Computing feature importances & statistics...")

feature_importances = {}
for name, model in MODELS.items():
    imp = model.feature_importance(importance_type='gain')
    fi = sorted(
        [{'feature': f, 'importance': round(float(v), 2)}
         for f, v in zip(FEATURE_COLS, imp)],
        key=lambda x: -x['importance'],
    )
    feature_importances[name] = fi

# Category map
category_map = {}
for f in FEATURE_COLS:
    if 'lag' in f or 'rolling' in f or 'daily' in f:
        category_map[f] = 'Lag / Rolling'
    elif f in ('ACT_TEMP','ACT_HUMIDITY','ACT_RAIN','ACT_HEAT_INDEX','COOL_FACTOR',
               'temp_humidity','heat_rain','temp_sq','cool_sq','is_hot'):
        category_map[f] = 'Weather'
    elif f in ('year','month','day','hour','minute','dayofweek','dayofyear',
               'weekofyear','quarter','is_weekend','time_of_day',
               'sin_hour','cos_hour','sin_dow','cos_dow','sin_month','cos_month'):
        category_map[f] = 'Temporal'
    elif f in ('is_peak',):
        category_map[f] = 'Engineered'
    elif f in ('is_holiday',):
        category_map[f] = 'Event'
    else:
        category_map[f] = 'Other'

for model_name in feature_importances:
    for fi in feature_importances[model_name]:
        fi['category'] = category_map.get(fi['feature'], 'Other')

cat_totals = {}
for fi in feature_importances.get('q67', []):
    cat = fi['category']
    cat_totals[cat] = cat_totals.get(cat, 0) + fi['importance']
total_imp = sum(cat_totals.values()) or 1
category_pct = {k: round(v / total_imp * 100, 1) for k, v in cat_totals.items()}

# Data statistics
df_all = combined.dropna(subset=['LOAD'])
peak_all = df_all[df_all['is_peak'] == 1]
offpeak_all = df_all[df_all['is_peak'] == 0]
pk_avg = float(peak_all['LOAD'].mean()) if len(peak_all) else 0
op_avg = float(offpeak_all['LOAD'].mean()) if len(offpeak_all) else 0

def temp_sens(sub):
    if len(sub) < 100:
        return 0.0
    x, y = sub['ACT_TEMP'].values, sub['LOAD'].values
    mask = np.isfinite(x) & np.isfinite(y)
    if mask.sum() < 100:
        return 0.0
    c = np.polyfit(x[mask], y[mask], 1)
    return round(float(c[0]), 3)

hol = df_all[df_all['is_holiday'] == 1]['LOAD'].mean()
non = df_all[df_all['is_holiday'] == 0]['LOAD'].mean()
holiday_pct = round(float((hol - non) / non * 100), 2) if non else 0.0

we = df_all[df_all['is_weekend'] == 1]['LOAD'].mean()
wd = df_all[df_all['is_weekend'] == 0]['LOAD'].mean()
weekend_pct = round(float((we - wd) / wd * 100), 2) if wd else 0.0

peak_uplift = round(float((pk_avg - op_avg) / op_avg * 100), 2) if op_avg else 0

data_statistics = {
    'temp_sensitivity_peak_kW_per_C': temp_sens(peak_all),
    'temp_sensitivity_offpeak_kW_per_C': temp_sens(offpeak_all),
    'holiday_impact_pct': holiday_pct,
    'weekend_impact_pct': weekend_pct,
    'peak_uplift_pct': peak_uplift,
    'correlation_temp': round(float(df_all[['LOAD','ACT_TEMP']].corr().iloc[0,1]), 4),
    'correlation_humidity': round(float(df_all[['LOAD','ACT_HUMIDITY']].corr().iloc[0,1]), 4),
    'correlation_heat_index': round(float(df_all[['LOAD','ACT_HEAT_INDEX']].corr().iloc[0,1]), 4),
    'avg_load': round(float(df_all['LOAD'].mean()), 1),
    'std_load': round(float(df_all['LOAD'].std()), 1),
    'avg_peak_load': round(pk_avg, 1),
    'avg_offpeak_load': round(op_avg, 1),
    'training_rows': int(df_all[df_all['DATETIME'] < '2021-05-01'].shape[0]),
    'training_period': f"{df_all['DATETIME'].min().strftime('%Y-%m-%d')} to {df_all[df_all['DATETIME'] < '2021-05-01']['DATETIME'].max().strftime('%Y-%m-%d')}",
}

# ─── Write output files ─────────────────────────────────────────────────────
print("[6/6] Writing JSON files...")

# 1. predictions.json — all interval-level data
with open(os.path.join(OUT_DIR, 'predictions.json'), 'w') as f:
    json.dump(predictions, f)
print(f"  predictions.json: {len(predictions)} intervals ({os.path.getsize(os.path.join(OUT_DIR, 'predictions.json')) / 1024:.0f} KB)")

# 2. explain.json — feature importances + data statistics
explain_data = {
    'feature_importances': feature_importances,
    'category_importance_pct': category_pct,
    'data_statistics': data_statistics,
    'feature_categories': category_map,
    'penalty_formula': {
        'description': 'ABT Deviation Penalty: For each 15-min interval, penalty = max(actual-forecast, 0) × ₹under + max(forecast-actual, 0) × ₹over',
        'optimal_quantile': 'α* = penalty_under / (penalty_under + penalty_over)',
        'hybrid_strategy': 'Uses Q(α*) during off-peak hours and Q0.90 during peak hours (18:00-22:00) for extra safety margin',
    },
    'model_info': {
        'algorithm': 'LightGBM (Gradient Boosted Decision Trees)',
        'num_features': len(FEATURE_COLS),
        'feature_list': FEATURE_COLS,
        'models_trained': list(MODELS.keys()),
        'training_rows': data_statistics['training_rows'],
        'training_period': data_statistics['training_period'],
    },
}
with open(os.path.join(OUT_DIR, 'explain.json'), 'w') as f:
    json.dump(explain_data, f)
print(f"  explain.json written")

# 3. metadata.json — date ranges, training info, lookback biases
metadata = {
    'testStart': '2021-05-01',
    'testEnd': pred_df['DATETIME'].max().strftime('%Y-%m-%d'),
    'trainMean': round(TRAIN_MEAN, 1),
    'trainingRows': data_statistics['training_rows'],
    'trainingPeriod': data_statistics['training_period'],
    'totalTestIntervals': len(predictions),
    'trainTempMean': round(float(train_clean['ACT_TEMP'].mean()), 1),
    'trainHumMean': round(float(train_clean['ACT_HUMIDITY'].mean()), 1),
    'lookbackBiases': lookback_biases,
}
with open(os.path.join(OUT_DIR, 'metadata.json'), 'w') as f:
    json.dump(metadata, f)
print(f"  metadata.json written")

print(f"\n✅ All static data generated in: {OUT_DIR}")
print(f"   Now the frontend can run WITHOUT the Python backend!")

"""
Retrain Original Full Model (with Lag Features)
Restores the high-accuracy lag-based LightGBM model that was overwritten.
"""
import pandas as pd
import numpy as np
import lightgbm as lgb
import pickle, os

MODEL_DIR = r"d:\ARFA PROJECTS\Decodex Dalmia\Dalmia Round 1\model training"
DATA_CSV  = os.path.join(MODEL_DIR, "Integrated_Load_Data_Final.csv")

# ── 1. Load Data ───────────────────────────────────────────────────────────────
print("Loading training data...")
df = pd.read_csv(DATA_CSV)
df['DATETIME'] = pd.to_datetime(df['DATETIME'], format='mixed', dayfirst=True)
df = df.sort_values('DATETIME').reset_index(drop=True)

# ── 2. Time Features ──────────────────────────────────────────────────────────
df['hour']         = df['DATETIME'].dt.hour
df['minute']       = df['DATETIME'].dt.minute
df['day_of_week']  = df['DATETIME'].dt.dayofweek
df['day_of_month'] = df['DATETIME'].dt.day
df['month']        = df['DATETIME'].dt.month
df['year']         = df['DATETIME'].dt.year
df['week_of_year'] = df['DATETIME'].dt.isocalendar().week.astype(int)
df['quarter']      = df['DATETIME'].dt.quarter
df['time_slot']    = df['hour'] * 4 + df['minute'] // 15
df['is_weekend']   = df['day_of_week'].isin([5, 6]).astype(int)

df['hour_sin']  = np.sin(2 * np.pi * df['hour'] / 24)
df['hour_cos']  = np.cos(2 * np.pi * df['hour'] / 24)
df['month_sin'] = np.sin(2 * np.pi * (df['month'] - 1) / 12)
df['month_cos'] = np.cos(2 * np.pi * (df['month'] - 1) / 12)
df['dow_sin']   = np.sin(2 * np.pi * df['day_of_week'] / 7)
df['dow_cos']   = np.cos(2 * np.pi * df['day_of_week'] / 7)

# ── 3. Lag & Rolling Features ─────────────────────────────────────────────────
load = df['LOAD']
df['lag_15min']         = load.shift(1)
df['lag_1hr']           = load.shift(4)
df['lag_1day']          = load.shift(96)
df['lag_1week']         = load.shift(672)
df['rolling_mean_1hr']  = load.shift(1).rolling(4).mean()
df['rolling_std_1hr']   = load.shift(1).rolling(4).std()
df['rolling_mean_1day'] = load.shift(1).rolling(96).mean()
df['rolling_std_1day']  = load.shift(1).rolling(96).std()
df['rolling_mean_1week']= load.shift(1).rolling(672).mean()
df['load_diff_15min']   = load.diff(1)
df['load_diff_1hr']     = load.diff(4)
df['load_diff_1day']    = load.diff(96)

# ── 4. Interactions ───────────────────────────────────────────────────────────
df['temp_humidity']  = df['ACT_TEMP'] * df['ACT_HUMIDITY']
df['heat_index_sq']  = df['ACT_HEAT_INDEX'] ** 2
df['cool_factor_sq'] = df['COOL_FACTOR'] ** 2

# ── 5. Event Encoding ─────────────────────────────────────────────────────────
with open(os.path.join(MODEL_DIR, 'label_encoder_event.pkl'), 'rb') as f:
    le = pickle.load(f)
df['Event_Encoded'] = le.transform(df['Event_Name'])

# ── 6. Drop NAs from lags ─────────────────────────────────────────────────────
df = df.dropna().reset_index(drop=True)
print(f"Training set: {len(df)} rows after dropping NaN from lags")

# ── 7. Feature Columns ────────────────────────────────────────────────────────
feature_cols = [
    'ACT_HEAT_INDEX', 'ACT_HUMIDITY', 'ACT_RAIN', 'ACT_TEMP', 'COOL_FACTOR',
    'Holiday_Ind', 'hour', 'minute', 'day_of_week', 'day_of_month', 'month',
    'year', 'week_of_year', 'quarter', 'time_slot', 'is_weekend',
    'hour_sin', 'hour_cos', 'month_sin', 'month_cos', 'dow_sin', 'dow_cos',
    'Event_Encoded', 'lag_15min', 'lag_1hr', 'lag_1day', 'lag_1week',
    'rolling_mean_1hr', 'rolling_std_1hr', 'rolling_mean_1day', 'rolling_std_1day',
    'rolling_mean_1week', 'load_diff_15min', 'load_diff_1hr', 'load_diff_1day',
    'temp_humidity', 'heat_index_sq', 'cool_factor_sq'
]

X = df[feature_cols]
y = df['LOAD']

# ── 8. Train Models ───────────────────────────────────────────────────────────
params = {
    'objective': 'quantile',
    'metric': 'quantile',
    'boosting_type': 'gbdt',
    'num_leaves': 64,
    'learning_rate': 0.03,
    'feature_fraction': 0.8,
    'bagging_fraction': 0.8,
    'bagging_freq': 5,
    'verbose': -1
}

print("Training Full Lag-Based Models (1000 rounds)...")
for quantile, label in zip([0.1, 0.5, 0.9], ['P10', 'P50', 'P90']):
    print(f"  Training {label}...")
    q_params = {**params, 'alpha': quantile}
    dtrain = lgb.Dataset(X, label=y)
    model = lgb.train(q_params, dtrain, num_boost_round=1000)
    model.save_model(os.path.join(MODEL_DIR, f'lgbm_quantile_{label}.txt'))

# ── 9. Save Feature Columns ───────────────────────────────────────────────────
with open(os.path.join(MODEL_DIR, 'feature_columns.txt'), 'w') as f:
    for col in feature_cols:
        f.write(f"{col}\n")

print("Original Lag-Based Model Restored Successfully!")

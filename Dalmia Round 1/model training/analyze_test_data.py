"""
Full Test Data Analysis Script
Merges Electric Load Test + External Factor Test CSVs,
runs them through the trained model, and computes performance metrics.
"""

import pandas as pd
import numpy as np
import pickle
import lightgbm as lgb
import os
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for saving

# ── 0. Config ──────────────────────────────────────────────────────────────────
MODEL_DIR = r"d:\ARFA PROJECTS\Decodex Dalmia\Dalmia Round 1\model training"
LOAD_CSV  = os.path.join(MODEL_DIR, "Electric_Load_Data_Test.csv")
EXT_CSV   = os.path.join(MODEL_DIR, "External_Factor_Data_Test.csv")
OUTPUT_CSV = os.path.join(MODEL_DIR, "test_predictions_analysis.csv")
CHART_PATH = os.path.join(MODEL_DIR, "test_analysis_chart.png")

# ── 1. Load CSVs ───────────────────────────────────────────────────────────────
print("Loading test data...")
load_df = pd.read_csv(LOAD_CSV)
ext_df  = pd.read_csv(EXT_CSV)

# ── 2. Parse & Merge ───────────────────────────────────────────────────────────
def parse_datetime(df):
    df['DATETIME'] = pd.to_datetime(df['DATETIME'], format='%d%b%Y:%H:%M:%S', dayfirst=True)
    return df

load_df = parse_datetime(load_df)
ext_df  = parse_datetime(ext_df)

df = pd.merge(load_df, ext_df, on='DATETIME', how='inner')
print(f"Merged dataset: {len(df)} rows from {df['DATETIME'].min()} to {df['DATETIME'].max()}")

# ── 3. Feature Engineering ─────────────────────────────────────────────────────
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

# Cyclic
df['hour_sin']  = np.sin(2 * np.pi * df['hour'] / 24)
df['hour_cos']  = np.cos(2 * np.pi * df['hour'] / 24)
df['month_sin'] = np.sin(2 * np.pi * (df['month'] - 1) / 12)
df['month_cos'] = np.cos(2 * np.pi * (df['month'] - 1) / 12)
df['dow_sin']   = np.sin(2 * np.pi * df['day_of_week'] / 7)
df['dow_cos']   = np.cos(2 * np.pi * df['day_of_week'] / 7)

# Interactions
df['temp_humidity']  = df['ACT_TEMP'] * df['ACT_HUMIDITY']
df['heat_index_sq']  = df['ACT_HEAT_INDEX'] ** 2
df['cool_factor_sq'] = df['COOL_FACTOR'] ** 2

# ── 4. Lag & Rolling Features ──────────────────────────────────────────────────
# We have actual load data in the test CSV, so we can compute proper lags
load = df['LOAD']
df['lag_15min']          = load.shift(1)
df['lag_1hr']            = load.shift(4)
df['lag_1day']           = load.shift(96)
df['lag_1week']          = load.shift(672)
df['rolling_mean_1hr']   = load.shift(1).rolling(4).mean()
df['rolling_std_1hr']    = load.shift(1).rolling(4).std()
df['rolling_mean_1day']  = load.shift(1).rolling(96).mean()
df['rolling_std_1day']   = load.shift(1).rolling(96).std()
df['rolling_mean_1week'] = load.shift(1).rolling(672).mean()
df['load_diff_15min']    = load.diff(1)
df['load_diff_1hr']      = load.diff(4)
df['load_diff_1day']     = load.diff(96)

# Drop rows where lags couldn't be computed (start of series)
df = df.dropna(subset=['lag_1week', 'rolling_mean_1week']).reset_index(drop=True)
print(f"Rows after lag computation: {len(df)}")

df['Holiday_Ind']    = 0
with open(os.path.join(MODEL_DIR, 'label_encoder_event.pkl'), 'rb') as f:
    le = pickle.load(f)
default_event = 'Normal Day' if 'Normal Day' in le.classes_ else le.classes_[0]
df['Event_Encoded'] = le.transform([default_event] * len(df))

# ── 4. Load feature list & Models ─────────────────────────────────────────────
with open(os.path.join(MODEL_DIR, 'feature_columns.txt')) as f:
    feature_cols = [l.strip() for l in f.readlines()]

models = {}
for q in ['P10', 'P50', 'P90']:
    models[q] = lgb.Booster(model_file=os.path.join(MODEL_DIR, f'lgbm_quantile_{q}.txt'))

print(f"Loaded models with {len(feature_cols)} features: {feature_cols[:5]}...")

# ── 5. Predict ─────────────────────────────────────────────────────────────────
X = df[feature_cols]
df['P10'] = models['P10'].predict(X)
df['P50'] = models['P50'].predict(X)
df['P90'] = models['P90'].predict(X)

# ── 6. Metrics ─────────────────────────────────────────────────────────────────
actual = df['LOAD']
p50    = df['P50']

mae  = np.mean(np.abs(actual - p50))
rmse = np.sqrt(np.mean((actual - p50) ** 2))
mape = np.mean(np.abs((actual - p50) / actual)) * 100
r2   = 1 - (np.sum((actual - p50)**2) / np.sum((actual - actual.mean())**2))

# Capture Rate: what % of actuals fall within P10-P90
in_range = ((actual >= df['P10']) & (actual <= df['P90'])).mean() * 100

print("\n" + "="*55)
print("       FULL TEST SET MODEL PERFORMANCE REPORT")
print("="*55)
print(f"  Total Rows Evaluated : {len(df):,}")
print(f"  Date Range           : {df['DATETIME'].min().date()} → {df['DATETIME'].max().date()}")
print("-"*55)
print(f"  MAE  (P50 vs Actual) : {mae:.2f} MW")
print(f"  RMSE (P50 vs Actual) : {rmse:.2f} MW")
print(f"  MAPE (P50 vs Actual) : {mape:.2f} %")
print(f"  R²   (P50 vs Actual) : {r2:.4f}")
print(f"  P10-P90 Capture Rate : {in_range:.1f} %")
print("="*55)

# ── 7. Per-Hour Analysis ───────────────────────────────────────────────────────
df['abs_error'] = np.abs(actual - p50)
hourly = df.groupby('hour')['abs_error'].mean().reset_index()
hourly.columns = ['Hour', 'MAE_MW']

print("\n  Hourly MAE Summary:")
print(hourly.to_string(index=False))

# ── 8. Save Results ───────────────────────────────────────────────────────────
out = df[['DATETIME', 'LOAD', 'P10', 'P50', 'P90', 'abs_error']].copy()
out.columns = ['DATETIME', 'Actual_MW', 'P10_MW', 'P50_MW', 'P90_MW', 'Error_MW']
out.to_csv(OUTPUT_CSV, index=False)
print(f"\n  Results saved → {OUTPUT_CSV}")

# ── 9. Chart ──────────────────────────────────────────────────────────────────
fig, axes = plt.subplots(3, 1, figsize=(16, 14))
fig.suptitle("Full Test Set Analysis — Load Forecast Model", fontsize=16, fontweight='bold')

# 9a. Actual vs P50 (sample first 7 days)
sample = df.head(7 * 96)
axes[0].plot(sample['DATETIME'], sample['LOAD'], label='Actual',  color='white',    linewidth=1.5, alpha=0.9)
axes[0].plot(sample['DATETIME'], sample['P50'],  label='P50',     color='#2fa572',  linewidth=1.2)
axes[0].fill_between(sample['DATETIME'], sample['P10'], sample['P90'],
                     alpha=0.25, color='#3a7ebf', label='P10–P90 Range')
axes[0].set_facecolor('#1a1a2e')
axes[0].set_title("Actual vs Predicted (First 7 Days)", color='white')
axes[0].tick_params(colors='white')
axes[0].legend(facecolor='#16213e', labelcolor='white')
axes[0].spines['bottom'].set_color('#444')
axes[0].spines['left'].set_color('#444')

# 9b. Error Distribution
axes[1].hist(df['abs_error'], bins=80, color='#ffb300', edgecolor='none', alpha=0.9)
axes[1].axvline(mae, color='#df5234', linestyle='--', label=f'Mean Error = {mae:.1f} MW')
axes[1].set_facecolor('#1a1a2e')
axes[1].set_title("Absolute Error Distribution (P50)", color='white')
axes[1].tick_params(colors='white')
axes[1].legend(facecolor='#16213e', labelcolor='white')
axes[1].spines['bottom'].set_color('#444')
axes[1].spines['left'].set_color('#444')

# 9c. Hourly MAE
axes[2].bar(hourly['Hour'], hourly['MAE_MW'], color='#3a7ebf', alpha=0.9)
axes[2].set_facecolor('#1a1a2e')
axes[2].set_title("Mean Absolute Error by Hour of Day", color='white')
axes[2].set_xlabel("Hour", color='white')
axes[2].set_ylabel("MAE (MW)", color='white')
axes[2].tick_params(colors='white')
axes[2].spines['bottom'].set_color('#444')
axes[2].spines['left'].set_color('#444')

fig.patch.set_facecolor('#16213e')
plt.tight_layout()
plt.savefig(CHART_PATH, dpi=120, bbox_inches='tight')
print(f"  Chart saved → {CHART_PATH}")
print("\nAnalysis Complete!")

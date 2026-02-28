"""
GRIDSHIELD Case 2 - Interactive GUI Application
================================================
Tkinter-based dashboard for the cost-aware load forecasting model.
Run this after gridshield_model.py has generated the outputs.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import lightgbm as lgb
from sklearn.metrics import mean_absolute_error, mean_squared_error
import os
import threading
import warnings
warnings.filterwarnings('ignore')

BASE_DIR = r'c:\Users\mansu\Downloads\02 – Case GRIDSHIELD'
OUTPUT_DIR = os.path.join(BASE_DIR, 'outputs')
DATA_FILE = os.path.join(BASE_DIR, 'Integrated_Load_Events_Data.csv')

# ======================================================================
# CORE ENGINE (Data + Model Logic)
# ======================================================================

class GridShieldEngine:
    """Handles all data processing, model training, and forecasting."""

    def __init__(self):
        self.df = None
        self.df_model = None
        self.train = None
        self.test = None
        self.models = {}
        self.features = [
            'time_slot', 'day_of_week', 'month', 'year', 'is_weekend', 'quarter',
            'hour_sin', 'hour_cos', 'dow_sin', 'dow_cos', 'month_sin', 'month_cos',
            'is_peak', 'day_of_month',
            'ACT_TEMP', 'ACT_HUMIDITY', 'ACT_RAIN', 'ACT_HEAT_INDEX', 'COOL_FACTOR',
            'temp_humidity_interaction', 'cool_factor_sq', 'is_hot', 'is_rainy', 'heat_stress',
            'temp_rolling_6h', 'humidity_rolling_6h',
            'Holiday_Ind', 'is_normal_day', 'is_festival', 'is_lockdown_event', 'is_rain_event',
            'is_post_covid', 'lockdown_phase',
            'load_lag_2d', 'load_lag_3d', 'load_lag_7d', 'load_lag_14d',
            'load_rolling_mean_7d', 'load_rolling_std_7d', 'load_rolling_max_7d', 'load_rolling_min_7d',
            'daily_mean', 'daily_max', 'daily_min', 'daily_std',
        ]
        self.backtest_results = []
        self.forecast_df = None
        self.is_loaded = False
        self.is_trained = False

    def load_and_engineer(self, filepath, log_cb=None):
        """Load CSV and engineer all features."""
        def log(msg):
            if log_cb:
                log_cb(msg)

        log("Loading data...")
        self.df = pd.read_csv(filepath)
        self.df['DATETIME'] = pd.to_datetime(self.df['DATETIME'])
        self.df = self.df.sort_values('DATETIME').reset_index(drop=True)
        log(f"  Loaded {len(self.df):,} rows  |  {self.df['DATETIME'].min().date()} to {self.df['DATETIME'].max().date()}")

        df = self.df
        log("Engineering features...")

        # Temporal
        df['hour'] = df['DATETIME'].dt.hour
        df['minute'] = df['DATETIME'].dt.minute
        df['time_slot'] = df['hour'] * 4 + df['minute'] // 15
        df['day_of_week'] = df['DATETIME'].dt.dayofweek
        df['day_of_month'] = df['DATETIME'].dt.day
        df['month'] = df['DATETIME'].dt.month
        df['year'] = df['DATETIME'].dt.year
        df['week_of_year'] = df['DATETIME'].dt.isocalendar().week.astype(int)
        df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)
        df['quarter'] = df['DATETIME'].dt.quarter
        df['hour_sin'] = np.sin(2 * np.pi * df['time_slot'] / 96)
        df['hour_cos'] = np.cos(2 * np.pi * df['time_slot'] / 96)
        df['dow_sin'] = np.sin(2 * np.pi * df['day_of_week'] / 7)
        df['dow_cos'] = np.cos(2 * np.pi * df['day_of_week'] / 7)
        df['month_sin'] = np.sin(2 * np.pi * df['month'] / 12)
        df['month_cos'] = np.cos(2 * np.pi * df['month'] / 12)
        df['is_peak'] = ((df['hour'] >= 18) & (df['hour'] < 22)).astype(int)

        # COVID / Regime
        df['is_post_covid'] = (df['DATETIME'] >= '2020-03-24').astype(int)
        df['lockdown_phase'] = 0
        df.loc[(df['DATETIME'] >= '2020-03-24') & (df['DATETIME'] < '2020-06-01'), 'lockdown_phase'] = 1
        df.loc[(df['DATETIME'] >= '2020-06-01') & (df['DATETIME'] < '2020-11-01'), 'lockdown_phase'] = 2
        df.loc[(df['DATETIME'] >= '2020-11-01') & (df['DATETIME'] < '2021-02-01'), 'lockdown_phase'] = 3
        df.loc[(df['DATETIME'] >= '2021-02-01'), 'lockdown_phase'] = 4

        # Events
        df['Holiday_Ind'] = df['Holiday_Ind'].fillna(0).astype(int)
        df['is_normal_day'] = (df['Event_Name'] == 'Normal Day').astype(int)
        df['is_festival'] = df['Event_Name'].str.contains('Ganesh|Navratri|Diwali|Laxmi|Dussera|Holi|Dhulivandan', case=False, na=False).astype(int)
        df['is_lockdown_event'] = df['Event_Name'].str.contains('Lockdown|Curfew|Unlock|WFH', case=False, na=False).astype(int)
        df['is_rain_event'] = df['Event_Name'].str.contains('Rain', case=False, na=False).astype(int)

        # Weather derived
        df['temp_humidity_interaction'] = df['ACT_TEMP'] * df['ACT_HUMIDITY'] / 100
        df['cool_factor_sq'] = df['COOL_FACTOR'] ** 2
        df['is_hot'] = (df['ACT_TEMP'] > 30).astype(int)
        df['is_rainy'] = (df['ACT_RAIN'] > 0).astype(int)
        df['heat_stress'] = np.maximum(df['ACT_HEAT_INDEX'] - 30, 0)

        # Lags (2-day-ahead safe)
        log("  Creating lag features...")
        for lag_days in [2, 3, 7, 14]:
            df[f'load_lag_{lag_days}d'] = df['LOAD'].shift(lag_days * 96)
        df['load_lag_7d'] = df['LOAD'].shift(7 * 96)

        df['load_rolling_mean_7d'] = df['LOAD'].shift(192).rolling(window=7*96, min_periods=96).mean()
        df['load_rolling_std_7d'] = df['LOAD'].shift(192).rolling(window=7*96, min_periods=96).std()
        df['load_rolling_max_7d'] = df['LOAD'].shift(192).rolling(window=7*96, min_periods=96).max()
        df['load_rolling_min_7d'] = df['LOAD'].shift(192).rolling(window=7*96, min_periods=96).min()
        df['temp_rolling_6h'] = df['ACT_TEMP'].rolling(window=24, min_periods=1).mean()
        df['humidity_rolling_6h'] = df['ACT_HUMIDITY'].rolling(window=24, min_periods=1).mean()

        # Daily stats from 2 days ago
        df['date'] = df['DATETIME'].dt.date
        daily_stats = df.groupby('date')['LOAD'].agg(['mean', 'max', 'min', 'std']).reset_index()
        daily_stats.columns = ['date', 'daily_mean', 'daily_max', 'daily_min', 'daily_std']
        df['date_for_merge'] = (df['DATETIME'] - pd.Timedelta(days=2)).dt.date
        df = df.merge(daily_stats, left_on='date_for_merge', right_on='date', how='left', suffixes=('', '_lag2d'))
        df.drop(columns=['date_lag2d', 'date_for_merge'], inplace=True, errors='ignore')

        self.df = df
        self.df_model = df.dropna(subset=self.features + ['LOAD']).copy()
        self.is_loaded = True
        log(f"  Done! {len(self.df_model):,} usable rows with {len(self.features)} features.")

    def train_models(self, penalty_under, penalty_over, peak_start, peak_end,
                     val_months, n_rounds, log_cb=None):
        """Train all three LightGBM models."""
        def log(msg):
            if log_cb:
                log_cb(msg)

        optimal_q = penalty_under / (penalty_under + penalty_over)
        log(f"Optimal quantile: {optimal_q:.3f}  (Under=₹{penalty_under}, Over=₹{penalty_over})")

        # Update peak definition
        self.df_model['is_peak'] = ((self.df_model['hour'] >= peak_start) & (self.df_model['hour'] < peak_end)).astype(int)

        # Split
        max_date = self.df_model['DATETIME'].max()
        split_date = max_date - pd.DateOffset(months=val_months)
        self.train = self.df_model[self.df_model['DATETIME'] < split_date]
        self.test = self.df_model[self.df_model['DATETIME'] >= split_date]
        log(f"Train: {len(self.train):,} rows  |  Test: {len(self.test):,} rows")

        X_tr, y_tr = self.train[self.features], self.train['LOAD']
        X_te, y_te = self.test[self.features], self.test['LOAD']
        train_ds = lgb.Dataset(X_tr, label=y_tr)
        val_ds = lgb.Dataset(X_te, label=y_te, reference=train_ds)

        base_params = {
            'boosting_type': 'gbdt', 'num_leaves': 255, 'learning_rate': 0.05,
            'feature_fraction': 0.8, 'bagging_fraction': 0.8, 'bagging_freq': 5,
            'min_child_samples': 50, 'n_jobs': -1, 'verbose': -1, 'seed': 42,
        }

        # Model A: Quantile (optimal)
        log(f"\nTraining Model A: Quantile {optimal_q:.3f} ...")
        pa = {**base_params, 'objective': 'quantile', 'alpha': optimal_q, 'metric': 'quantile'}
        self.models['quantile'] = lgb.train(pa, train_ds, num_boost_round=n_rounds,
            valid_sets=[val_ds], callbacks=[lgb.early_stopping(50), lgb.log_evaluation(0)])
        log(f"  Best iteration: {self.models['quantile'].best_iteration}")

        # Model B: MSE baseline
        log("Training Model B: MSE Baseline ...")
        pb = {**base_params, 'objective': 'regression', 'metric': 'rmse'}
        self.models['mse'] = lgb.train(pb, train_ds, num_boost_round=n_rounds,
            valid_sets=[val_ds], callbacks=[lgb.early_stopping(50), lgb.log_evaluation(0)])
        log(f"  Best iteration: {self.models['mse'].best_iteration}")

        # Model C: Conservative Q90
        log("Training Model C: Quantile 0.90 (peak conservative) ...")
        pc = {**base_params, 'objective': 'quantile', 'alpha': 0.90, 'metric': 'quantile'}
        self.models['q90'] = lgb.train(pc, train_ds, num_boost_round=n_rounds,
            valid_sets=[val_ds], callbacks=[lgb.early_stopping(50), lgb.log_evaluation(0)])
        log(f"  Best iteration: {self.models['q90'].best_iteration}")

        self.is_trained = True
        self._penalty_under = penalty_under
        self._penalty_over = penalty_over
        log("\nAll models trained successfully!")

    def backtest(self, log_cb=None):
        """Run backtest on validation set."""
        def log(msg):
            if log_cb:
                log_cb(msg)

        X_te = self.test[self.features]
        y_te = self.test['LOAD'].values
        is_peak = self.test['is_peak'].values
        pu, po = self._penalty_under, self._penalty_over

        preds = {
            'Naive (Last Week)': self.test['load_lag_7d'].values,
            'LightGBM MSE': self.models['mse'].predict(X_te),
            f'LightGBM Q{pu/(pu+po):.2f}': self.models['quantile'].predict(X_te),
            'LightGBM Q0.90': self.models['q90'].predict(X_te),
        }
        # Hybrid
        hybrid = preds[f'LightGBM Q{pu/(pu+po):.2f}'].copy()
        hybrid[is_peak == 1] = preds['LightGBM Q0.90'][is_peak == 1]
        preds['HYBRID (Recommended)'] = hybrid

        self.backtest_results = []
        for name, pred in preds.items():
            dev = y_te - pred
            pen_u = (dev[dev > 0] * 0.25 * pu).sum()
            pen_o = (-dev[dev < 0] * 0.25 * po).sum()
            peak_dev = dev[is_peak == 1]
            peak_p = (peak_dev[peak_dev > 0] * 0.25 * pu).sum() + (-peak_dev[peak_dev < 0] * 0.25 * po).sum()

            self.backtest_results.append({
                'Strategy': name,
                'Total Penalty (₹)': pen_u + pen_o,
                'Peak Penalty (₹)': peak_p,
                'Under-fcst (₹)': pen_u,
                'Over-fcst (₹)': pen_o,
                'Bias (%)': f"{(dev.mean() / y_te.mean()) * 100:+.2f}",
                'MAE': round(mean_absolute_error(y_te, pred), 2),
                'RMSE': round(np.sqrt(mean_squared_error(y_te, pred)), 2),
                'MAPE (%)': round((np.abs(dev) / y_te).mean() * 100, 2),
            })

        best = min(self.backtest_results, key=lambda x: x['Total Penalty (₹)'])
        naive_p = self.backtest_results[0]['Total Penalty (₹)']
        reduction = (best['Total Penalty (₹)'] - naive_p) / naive_p * 100
        log(f"Best: {best['Strategy']}  |  ₹{best['Total Penalty (₹)']:,.0f}  |  {reduction:+.1f}% vs Naive")
        return self.backtest_results

    def forecast_2day(self, holiday_day1, holiday_day2, log_cb=None):
        """Generate 2-day ahead forecast from end of data."""
        def log(msg):
            if log_cb:
                log_cb(msg)

        last_dt = self.df['DATETIME'].max()
        future_dates = pd.date_range(start=last_dt + pd.Timedelta(minutes=15), periods=192, freq='15min')
        fdf = pd.DataFrame({'DATETIME': future_dates})

        # Temporal
        fdf['hour'] = fdf['DATETIME'].dt.hour
        fdf['minute'] = fdf['DATETIME'].dt.minute
        fdf['time_slot'] = fdf['hour'] * 4 + fdf['minute'] // 15
        fdf['day_of_week'] = fdf['DATETIME'].dt.dayofweek
        fdf['day_of_month'] = fdf['DATETIME'].dt.day
        fdf['month'] = fdf['DATETIME'].dt.month
        fdf['year'] = fdf['DATETIME'].dt.year
        fdf['week_of_year'] = fdf['DATETIME'].dt.isocalendar().week.astype(int)
        fdf['is_weekend'] = (fdf['day_of_week'] >= 5).astype(int)
        fdf['quarter'] = fdf['DATETIME'].dt.quarter
        fdf['hour_sin'] = np.sin(2 * np.pi * fdf['time_slot'] / 96)
        fdf['hour_cos'] = np.cos(2 * np.pi * fdf['time_slot'] / 96)
        fdf['dow_sin'] = np.sin(2 * np.pi * fdf['day_of_week'] / 7)
        fdf['dow_cos'] = np.cos(2 * np.pi * fdf['day_of_week'] / 7)
        fdf['month_sin'] = np.sin(2 * np.pi * fdf['month'] / 12)
        fdf['month_cos'] = np.cos(2 * np.pi * fdf['month'] / 12)
        fdf['is_peak'] = ((fdf['hour'] >= 18) & (fdf['hour'] < 22)).astype(int)
        fdf['is_post_covid'] = 1
        fdf['lockdown_phase'] = 4

        # Holidays
        fdf['Holiday_Ind'] = 0
        if holiday_day1:
            fdf.loc[fdf['DATETIME'].dt.day == future_dates[0].day, 'Holiday_Ind'] = 1
        if holiday_day2:
            fdf.loc[fdf['DATETIME'].dt.day == future_dates[-1].day, 'Holiday_Ind'] = 1
        fdf['is_normal_day'] = (fdf['Holiday_Ind'] == 0).astype(int)
        fdf['is_festival'] = 0
        fdf['is_lockdown_event'] = 0
        fdf['is_rain_event'] = 0

        # Weather proxy (last week avg by slot)
        last_week = self.df[self.df['DATETIME'] >= (last_dt - pd.Timedelta(days=7))]
        weather_slot = last_week.groupby('time_slot').agg({
            'ACT_TEMP': 'mean', 'ACT_HUMIDITY': 'mean', 'ACT_RAIN': 'mean',
            'ACT_HEAT_INDEX': 'mean', 'COOL_FACTOR': 'mean'
        }).reset_index()
        fdf = fdf.merge(weather_slot, on='time_slot', how='left')

        fdf['temp_humidity_interaction'] = fdf['ACT_TEMP'] * fdf['ACT_HUMIDITY'] / 100
        fdf['cool_factor_sq'] = fdf['COOL_FACTOR'] ** 2
        fdf['is_hot'] = (fdf['ACT_TEMP'] > 30).astype(int)
        fdf['is_rainy'] = (fdf['ACT_RAIN'] > 0).astype(int)
        fdf['heat_stress'] = np.maximum(fdf['ACT_HEAT_INDEX'] - 30, 0)
        fdf['temp_rolling_6h'] = fdf['ACT_TEMP'].rolling(window=24, min_periods=1).mean()
        fdf['humidity_rolling_6h'] = fdf['ACT_HUMIDITY'].rolling(window=24, min_periods=1).mean()

        # Lags
        for lag_days in [2, 3, 7, 14]:
            lag_start = last_dt - pd.Timedelta(days=lag_days) + pd.Timedelta(minutes=15)
            lag_data = self.df[self.df['DATETIME'] >= lag_start].head(192)
            vals = lag_data['LOAD'].values
            if len(vals) >= 192:
                fdf[f'load_lag_{lag_days}d'] = vals[:192]
            else:
                fdf[f'load_lag_{lag_days}d'] = np.pad(vals, (0, 192 - len(vals)), mode='edge')

        recent = self.df.tail(7 * 96)
        fdf['load_rolling_mean_7d'] = recent['LOAD'].mean()
        fdf['load_rolling_std_7d'] = recent['LOAD'].std()
        fdf['load_rolling_max_7d'] = recent['LOAD'].max()
        fdf['load_rolling_min_7d'] = recent['LOAD'].min()

        d2ago = self.df[self.df['DATETIME'].dt.date == (last_dt - pd.Timedelta(days=1)).date()]
        src = d2ago if len(d2ago) > 0 else recent
        fdf['daily_mean'] = src['LOAD'].mean()
        fdf['daily_max'] = src['LOAD'].max()
        fdf['daily_min'] = src['LOAD'].min()
        fdf['daily_std'] = src['LOAD'].std()

        # Predict
        fdf['Forecast_MSE'] = self.models['mse'].predict(fdf[self.features])
        fdf['Forecast_Q67'] = self.models['quantile'].predict(fdf[self.features])
        fdf['Forecast_Q90'] = self.models['q90'].predict(fdf[self.features])
        fdf['Forecast_HYBRID'] = fdf['Forecast_Q67'].copy()
        fdf.loc[fdf['is_peak'] == 1, 'Forecast_HYBRID'] = fdf.loc[fdf['is_peak'] == 1, 'Forecast_Q90']

        self.forecast_df = fdf
        d1 = future_dates[0].strftime('%Y-%m-%d')
        d2 = future_dates[-1].strftime('%Y-%m-%d')
        log(f"Forecast generated: {d1} to {d2}  (192 slots)")
        return fdf


# ======================================================================
# TKINTER GUI
# ======================================================================

class GridShieldApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("GRIDSHIELD  |  Cost-Aware Load Forecasting Dashboard")
        self.geometry("1280x820")
        self.configure(bg="#1e1e2e")
        self.resizable(True, True)

        self.engine = GridShieldEngine()
        self._build_ui()

    # ---- UI CONSTRUCTION ----

    def _build_ui(self):
        style = ttk.Style(self)
        style.theme_use('clam')

        # Colors
        BG = "#1e1e2e"
        FG = "#cdd6f4"
        ACCENT = "#89b4fa"
        CARD = "#313244"
        BTN_BG = "#45475a"
        BTN_FG = "#cdd6f4"
        ENTRY_BG = "#45475a"

        style.configure("TFrame", background=BG)
        style.configure("Card.TFrame", background=CARD)
        style.configure("TLabel", background=BG, foreground=FG, font=("Segoe UI", 10))
        style.configure("Card.TLabel", background=CARD, foreground=FG, font=("Segoe UI", 10))
        style.configure("Header.TLabel", background=BG, foreground=ACCENT, font=("Segoe UI", 14, "bold"))
        style.configure("SubHeader.TLabel", background=CARD, foreground=ACCENT, font=("Segoe UI", 11, "bold"))
        style.configure("Accent.TButton", background=ACCENT, foreground="#1e1e2e", font=("Segoe UI", 10, "bold"))
        style.map("Accent.TButton", background=[("active", "#74c7ec")])
        style.configure("TNotebook", background=BG)
        style.configure("TNotebook.Tab", background=BTN_BG, foreground=FG, font=("Segoe UI", 10, "bold"), padding=[12, 4])
        style.map("TNotebook.Tab", background=[("selected", ACCENT)], foreground=[("selected", "#1e1e2e")])

        # ---- HEADER ----
        header = ttk.Frame(self)
        header.pack(fill="x", padx=10, pady=(10, 5))
        ttk.Label(header, text="⚡ GRIDSHIELD", style="Header.TLabel",
                  font=("Segoe UI", 18, "bold")).pack(side="left")
        ttk.Label(header, text="Cost-Aware Load Forecasting  |  Lumina Energy  |  Mumbai",
                  style="TLabel").pack(side="left", padx=20)

        # ---- MAIN CONTAINER ----
        main = ttk.PanedWindow(self, orient="horizontal")
        main.pack(fill="both", expand=True, padx=10, pady=5)

        # LEFT PANEL — Controls
        left = ttk.Frame(main, width=340)
        main.add(left, weight=0)
        self._build_left_panel(left, CARD, ENTRY_BG, FG, ACCENT)

        # RIGHT PANEL — Notebook with tabs
        right = ttk.Frame(main)
        main.add(right, weight=1)
        self.notebook = ttk.Notebook(right)
        self.notebook.pack(fill="both", expand=True)

        # Tab: Log
        log_frame = ttk.Frame(self.notebook)
        self.notebook.add(log_frame, text="  Log  ")
        self.log_text = tk.Text(log_frame, bg="#181825", fg="#a6adc8", font=("Consolas", 10),
                                insertbackground="#cdd6f4", wrap="word", bd=0, padx=8, pady=8)
        self.log_text.pack(fill="both", expand=True)
        self._log("GRIDSHIELD Dashboard ready. Load data to begin.")

        # Tab: Backtest Results
        bt_frame = ttk.Frame(self.notebook)
        self.notebook.add(bt_frame, text="  Backtest  ")
        self.bt_tree = self._make_treeview(bt_frame,
            columns=["Strategy", "Total Penalty (₹)", "Peak Penalty (₹)", "Under-fcst (₹)",
                      "Over-fcst (₹)", "Bias (%)", "MAE", "RMSE", "MAPE (%)"])

        # Tab: Forecast Table
        fc_frame = ttk.Frame(self.notebook)
        self.notebook.add(fc_frame, text="  Forecast  ")
        self.fc_tree = self._make_treeview(fc_frame,
            columns=["DateTime", "Slot", "Peak", "MSE", "Q67", "Q90", "HYBRID"])

        # Tab: Charts
        chart_frame = ttk.Frame(self.notebook)
        self.notebook.add(chart_frame, text="  Charts  ")
        self.chart_frame = chart_frame
        self.fig = Figure(figsize=(10, 6), dpi=100, facecolor="#1e1e2e")
        self.canvas = FigureCanvasTkAgg(self.fig, master=chart_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
        toolbar = NavigationToolbar2Tk(self.canvas, chart_frame)
        toolbar.update()

    def _build_left_panel(self, parent, CARD, ENTRY_BG, FG, ACCENT):
        canvas = tk.Canvas(parent, bg="#1e1e2e", highlightthickness=0, width=320)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scroll_frame = ttk.Frame(canvas)
        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Helper to make cards
        def card(parent_frame, title):
            c = ttk.Frame(parent_frame, style="Card.TFrame", padding=10)
            c.pack(fill="x", padx=5, pady=5)
            ttk.Label(c, text=title, style="SubHeader.TLabel").pack(anchor="w")
            ttk.Separator(c).pack(fill="x", pady=(4, 8))
            return c

        def labeled_entry(parent_frame, label_text, default, width=12):
            row = ttk.Frame(parent_frame, style="Card.TFrame")
            row.pack(fill="x", pady=2)
            ttk.Label(row, text=label_text, style="Card.TLabel", width=22, anchor="w").pack(side="left")
            var = tk.StringVar(value=str(default))
            e = tk.Entry(row, textvariable=var, width=width, bg=ENTRY_BG, fg=FG,
                         insertbackground=FG, font=("Segoe UI", 10), bd=0, relief="flat")
            e.pack(side="right", padx=(0, 5))
            return var

        def labeled_check(parent_frame, label_text, default=False):
            var = tk.BooleanVar(value=default)
            cb = tk.Checkbutton(parent_frame, text=label_text, variable=var,
                                bg="#313244", fg=FG, selectcolor=ENTRY_BG,
                                activebackground="#313244", activeforeground=FG,
                                font=("Segoe UI", 10))
            cb.pack(anchor="w", pady=1)
            return var

        # ---- Data Card ----
        c1 = card(scroll_frame, "📂 Data")
        self.data_path_var = tk.StringVar(value=DATA_FILE)
        path_row = ttk.Frame(c1, style="Card.TFrame")
        path_row.pack(fill="x", pady=2)
        tk.Entry(path_row, textvariable=self.data_path_var, bg=ENTRY_BG, fg=FG,
                 insertbackground=FG, font=("Segoe UI", 9), bd=0, width=28).pack(side="left", fill="x", expand=True)
        tk.Button(path_row, text="...", command=self._browse_file, bg=ACCENT, fg="#1e1e2e",
                  font=("Segoe UI", 9, "bold"), bd=0, width=3).pack(side="right", padx=(4, 0))

        tk.Button(c1, text="▶  Load & Engineer Features", command=self._on_load,
                  bg=ACCENT, fg="#1e1e2e", font=("Segoe UI", 10, "bold"), bd=0,
                  activebackground="#74c7ec", cursor="hand2", pady=6).pack(fill="x", pady=(8, 0))

        # ---- Penalty Card ----
        c2 = card(scroll_frame, "💰 Penalty Parameters")
        self.pen_under = labeled_entry(c2, "Under-forecast (₹/kWh):", 4)
        self.pen_over = labeled_entry(c2, "Over-forecast (₹/kWh):", 2)
        self.peak_start = labeled_entry(c2, "Peak start hour:", 18)
        self.peak_end = labeled_entry(c2, "Peak end hour:", 22)

        # ---- Model Card ----
        c3 = card(scroll_frame, "🧠 Model Settings")
        self.val_months = labeled_entry(c3, "Validation months:", 3)
        self.n_rounds = labeled_entry(c3, "Max boosting rounds:", 2000)

        tk.Button(c3, text="▶  Train Models", command=self._on_train,
                  bg="#a6e3a1", fg="#1e1e2e", font=("Segoe UI", 10, "bold"), bd=0,
                  activebackground="#94e2d5", cursor="hand2", pady=6).pack(fill="x", pady=(8, 0))

        # ---- Backtest Card ----
        c4 = card(scroll_frame, "📊 Backtest")
        tk.Button(c4, text="▶  Run Backtest", command=self._on_backtest,
                  bg="#fab387", fg="#1e1e2e", font=("Segoe UI", 10, "bold"), bd=0,
                  activebackground="#f9e2af", cursor="hand2", pady=6).pack(fill="x")

        # ---- Forecast Card ----
        c5 = card(scroll_frame, "🔮 2-Day Forecast")
        self.hol_day1 = labeled_check(c5, "Day 1 is Holiday", default=True)
        self.hol_day2 = labeled_check(c5, "Day 2 is Holiday", default=False)

        tk.Button(c5, text="▶  Generate Forecast", command=self._on_forecast,
                  bg="#cba6f7", fg="#1e1e2e", font=("Segoe UI", 10, "bold"), bd=0,
                  activebackground="#b4befe", cursor="hand2", pady=6).pack(fill="x", pady=(8, 0))

        tk.Button(c5, text="💾  Export Forecast CSV", command=self._on_export,
                  bg=ENTRY_BG, fg=FG, font=("Segoe UI", 9), bd=0,
                  cursor="hand2", pady=4).pack(fill="x", pady=(6, 0))

        # ---- Chart Card ----
        c6 = card(scroll_frame, "📈 Visualize")
        chart_btns = [
            ("Forecast Plot", self._chart_forecast),
            ("Penalty Comparison", self._chart_penalty),
            ("Feature Importance", self._chart_importance),
            ("Actual vs Predicted", self._chart_actual_vs_pred),
        ]
        for label, cmd in chart_btns:
            tk.Button(c6, text=label, command=cmd, bg=ENTRY_BG, fg=FG,
                      font=("Segoe UI", 9), bd=0, cursor="hand2", pady=3,
                      activebackground="#585b70").pack(fill="x", pady=1)

    # ---- HELPERS ----

    def _make_treeview(self, parent, columns):
        container = ttk.Frame(parent)
        container.pack(fill="both", expand=True)
        tree = ttk.Treeview(container, columns=columns, show="headings", height=12)
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=110 if "₹" in col else 90, anchor="center")
        vsb = ttk.Scrollbar(container, orient="vertical", command=tree.yview)
        hsb = ttk.Scrollbar(container, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        hsb.pack(side="bottom", fill="x")
        return tree

    def _log(self, msg):
        self.log_text.insert("end", msg + "\n")
        self.log_text.see("end")
        self.update_idletasks()

    def _browse_file(self):
        f = filedialog.askopenfilename(filetypes=[("CSV", "*.csv")])
        if f:
            self.data_path_var.set(f)

    def _run_threaded(self, target, *args):
        """Run a function in a background thread to keep GUI responsive."""
        def wrapper():
            try:
                target(*args)
            except Exception as e:
                self._log(f"\n❌ ERROR: {e}")
        t = threading.Thread(target=wrapper, daemon=True)
        t.start()

    # ---- ACTIONS ----

    def _on_load(self):
        path = self.data_path_var.get().strip()
        if not os.path.exists(path):
            messagebox.showerror("Error", f"File not found:\n{path}")
            return
        self._log("\n" + "="*50)
        self.notebook.select(0)  # Switch to Log tab
        self._run_threaded(self.engine.load_and_engineer, path, self._log)

    def _on_train(self):
        if not self.engine.is_loaded:
            messagebox.showwarning("Warning", "Load data first!")
            return
        try:
            pu = float(self.pen_under.get())
            po = float(self.pen_over.get())
            ps = int(self.peak_start.get())
            pe = int(self.peak_end.get())
            vm = int(self.val_months.get())
            nr = int(self.n_rounds.get())
        except ValueError:
            messagebox.showerror("Error", "Invalid parameter values. Please enter numbers.")
            return
        self._log("\n" + "="*50)
        self.notebook.select(0)
        self._run_threaded(self.engine.train_models, pu, po, ps, pe, vm, nr, self._log)

    def _on_backtest(self):
        if not self.engine.is_trained:
            messagebox.showwarning("Warning", "Train models first!")
            return
        self._log("\n" + "="*50)
        results = self.engine.backtest(self._log)

        # Populate treeview
        for row in self.bt_tree.get_children():
            self.bt_tree.delete(row)
        for r in results:
            vals = [
                r['Strategy'],
                f"₹{r['Total Penalty (₹)']:,.0f}",
                f"₹{r['Peak Penalty (₹)']:,.0f}",
                f"₹{r['Under-fcst (₹)']:,.0f}",
                f"₹{r['Over-fcst (₹)']:,.0f}",
                r['Bias (%)'],
                r['MAE'],
                r['RMSE'],
                r['MAPE (%)'],
            ]
            self.bt_tree.insert("", "end", values=vals)
        self.notebook.select(1)  # Switch to Backtest tab

    def _on_forecast(self):
        if not self.engine.is_trained:
            messagebox.showwarning("Warning", "Train models first!")
            return
        self._log("\n" + "="*50)
        fdf = self.engine.forecast_2day(self.hol_day1.get(), self.hol_day2.get(), self._log)

        # Populate treeview
        for row in self.fc_tree.get_children():
            self.fc_tree.delete(row)
        for _, r in fdf.iterrows():
            self.fc_tree.insert("", "end", values=[
                r['DATETIME'].strftime('%Y-%m-%d %H:%M'),
                int(r['time_slot']),
                "PEAK" if r['is_peak'] else "",
                f"{r['Forecast_MSE']:.1f}",
                f"{r['Forecast_Q67']:.1f}",
                f"{r['Forecast_Q90']:.1f}",
                f"{r['Forecast_HYBRID']:.1f}",
            ])
        self.notebook.select(2)  # Switch to Forecast tab
        self._chart_forecast()

    def _on_export(self):
        if self.engine.forecast_df is None:
            messagebox.showwarning("Warning", "Generate forecast first!")
            return
        path = filedialog.asksaveasfilename(defaultextension=".csv",
                filetypes=[("CSV", "*.csv")],
                initialfile="2day_ahead_forecast.csv")
        if path:
            out = self.engine.forecast_df[['DATETIME', 'time_slot', 'is_peak',
                'Forecast_MSE', 'Forecast_Q67', 'Forecast_Q90', 'Forecast_HYBRID']].round(2)
            out.to_csv(path, index=False)
            self._log(f"Exported to: {path}")
            messagebox.showinfo("Exported", f"Forecast saved to:\n{path}")

    # ---- CHARTS ----

    def _chart_forecast(self):
        fdf = self.engine.forecast_df
        if fdf is None:
            messagebox.showwarning("Warning", "Generate forecast first!")
            return
        self.fig.clear()
        dates = fdf['DATETIME']
        day1_end = dates.iloc[0].normalize() + pd.Timedelta(days=1)

        ax1 = self.fig.add_subplot(211)
        ax2 = self.fig.add_subplot(212)

        for ax, mask, title in [
            (ax1, dates < day1_end, f"Day 1: {dates.iloc[0].strftime('%b %d, %Y')}"),
            (ax2, dates >= day1_end, f"Day 2: {dates.iloc[-1].strftime('%b %d, %Y')}")
        ]:
            d = fdf[mask]
            x = range(len(d))
            ax.plot(x, d['Forecast_MSE'], label='MSE', alpha=0.6, linewidth=1)
            ax.plot(x, d['Forecast_Q67'], label='Quantile 0.67', alpha=0.6, linewidth=1)
            ax.plot(x, d['Forecast_HYBRID'], label='HYBRID', linewidth=2.2, color='#a6e3a1')
            # Peak shading
            pk = d['is_peak'] == 1
            if pk.any():
                first = pk.values.argmax()
                last = len(pk) - pk.values[::-1].argmax()
                ax.axvspan(first, last, alpha=0.12, color='red', label='Peak')
            ax.set_title(title, color='#cdd6f4', fontsize=11)
            ax.set_ylabel('Load (kW)', color='#cdd6f4')
            ax.set_facecolor('#181825')
            ax.tick_params(colors='#a6adc8')
            ax.legend(fontsize=8, loc='upper left')
            ax.grid(True, alpha=0.15)

            ticks = list(range(0, len(d), 8))
            ax.set_xticks(ticks)
            ax.set_xticklabels([d['DATETIME'].iloc[i].strftime('%H:%M') if i < len(d) else '' for i in ticks], fontsize=8)

        self.fig.tight_layout()
        self.canvas.draw()
        self.notebook.select(3)

    def _chart_penalty(self):
        if not self.engine.backtest_results:
            messagebox.showwarning("Warning", "Run backtest first!")
            return
        self.fig.clear()
        ax = self.fig.add_subplot(111)
        names = [r['Strategy'] for r in self.engine.backtest_results]
        vals = [r['Total Penalty (₹)'] for r in self.engine.backtest_results]
        colors = ['#6c7086', '#89b4fa', '#f38ba8', '#fab387', '#a6e3a1']
        bars = ax.bar(range(len(names)), vals, color=colors[:len(names)])
        ax.set_xticks(range(len(names)))
        ax.set_xticklabels(names, rotation=20, ha='right', fontsize=8, color='#a6adc8')
        ax.set_ylabel('Total Penalty (₹)', color='#cdd6f4')
        ax.set_title('Penalty Comparison', color='#cdd6f4', fontsize=13)
        ax.set_facecolor('#181825')
        ax.tick_params(colors='#a6adc8')
        for bar, v in zip(bars, vals):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height(),
                    f'₹{v:,.0f}', ha='center', va='bottom', fontsize=8, color='#cdd6f4')
        self.fig.tight_layout()
        self.canvas.draw()
        self.notebook.select(3)

    def _chart_importance(self):
        if not self.engine.is_trained:
            messagebox.showwarning("Warning", "Train models first!")
            return
        self.fig.clear()
        ax = self.fig.add_subplot(111)
        imp = pd.DataFrame({
            'feature': self.engine.features,
            'importance': self.engine.models['quantile'].feature_importance(importance_type='gain')
        }).sort_values('importance', ascending=True).tail(15)
        ax.barh(range(len(imp)), imp['importance'], color='#89b4fa')
        ax.set_yticks(range(len(imp)))
        ax.set_yticklabels(imp['feature'], fontsize=9, color='#cdd6f4')
        ax.set_xlabel('Importance (Gain)', color='#cdd6f4')
        ax.set_title('Top 15 Feature Importance', color='#cdd6f4', fontsize=13)
        ax.set_facecolor('#181825')
        ax.tick_params(colors='#a6adc8')
        self.fig.tight_layout()
        self.canvas.draw()
        self.notebook.select(3)

    def _chart_actual_vs_pred(self):
        if not self.engine.is_trained:
            messagebox.showwarning("Warning", "Train models first!")
            return
        self.fig.clear()
        test = self.engine.test.tail(96 * 7)  # Last 7 days
        X = test[self.engine.features]
        actual = test['LOAD'].values
        pred = self.engine.models['quantile'].predict(X)

        ax1 = self.fig.add_subplot(211)
        ax1.plot(range(len(actual)), actual, label='Actual', linewidth=1, alpha=0.8, color='#89b4fa')
        ax1.plot(range(len(pred)), pred, label='Forecast', linewidth=1, alpha=0.8, color='#a6e3a1')
        ax1.set_title('Actual vs Forecast (Last 7 Days of Validation)', color='#cdd6f4')
        ax1.set_ylabel('Load (kW)', color='#cdd6f4')
        ax1.legend(fontsize=9)
        ax1.set_facecolor('#181825')
        ax1.tick_params(colors='#a6adc8')
        ax1.grid(True, alpha=0.15)

        ax2 = self.fig.add_subplot(212)
        dev = actual - pred
        colors_dev = ['#f38ba8' if d > 0 else '#a6e3a1' for d in dev]
        ax2.bar(range(len(dev)), dev, color=colors_dev, width=1, alpha=0.7)
        ax2.axhline(y=0, color='#585b70', linewidth=0.5)
        ax2.set_title('Deviation (Red=Under-fcst ₹4  |  Green=Over-fcst ₹2)', color='#cdd6f4')
        ax2.set_ylabel('Deviation (kW)', color='#cdd6f4')
        ax2.set_facecolor('#181825')
        ax2.tick_params(colors='#a6adc8')

        self.fig.tight_layout()
        self.canvas.draw()
        self.notebook.select(3)


# ======================================================================
# MAIN
# ======================================================================
if __name__ == "__main__":
    app = GridShieldApp()
    app.mainloop()

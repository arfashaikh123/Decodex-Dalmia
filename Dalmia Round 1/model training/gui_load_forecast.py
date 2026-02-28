import customtkinter as ctk
import pandas as pd
import numpy as np
import lightgbm as lgb
import shap
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pickle
import os
import warnings
from datetime import datetime

warnings.filterwarnings('ignore')

# Set appearance and theme
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class LoadForecasterGUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("⚡ Dalmia Load Forecasting - Quantile Regression & Explainability")
        self.geometry("1100x850")

        # --- Data & Model Storage ---
        self.models = {}
        self.le_event = None
        self.feature_cols = []
        self.dataset = None
        self.explainer = None
        
        # --- UI Setup ---
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.setup_sidebar()
        self.setup_main_frame()
        
        # Load resources
        self.load_models_and_data()

    def setup_sidebar(self):
        self.sidebar_frame = ctk.CTkFrame(self, width=250, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="Forecast Controls", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        # Date/Time selector
        self.date_label = ctk.CTkLabel(self.sidebar_frame, text="Select Timestamp from Data:")
        self.date_label.grid(row=1, column=0, padx=20, pady=(10, 0))
        
        self.timestamp_option = ctk.CTkOptionMenu(self.sidebar_frame, values=["Loading..."], command=self.on_timestamp_change)
        self.timestamp_option.grid(row=2, column=0, padx=20, pady=10)

        # Manual Overrides Label
        self.override_label = ctk.CTkLabel(self.sidebar_frame, text="Manual Overrides", font=ctk.CTkFont(size=16, weight="bold"))
        self.override_label.grid(row=3, column=0, padx=20, pady=(20, 10))

        # Temperature
        self.temp_label = ctk.CTkLabel(self.sidebar_frame, text="Temp (°C):")
        self.temp_label.grid(row=4, column=0, padx=20, pady=(5, 0))
        self.temp_slider = ctk.CTkSlider(self.sidebar_frame, from_=15, to=45, number_of_steps=60)
        self.temp_slider.grid(row=5, column=0, padx=20, pady=5)
        self.temp_val_label = ctk.CTkLabel(self.sidebar_frame, text="28.0")
        self.temp_val_label.grid(row=6, column=0, padx=20, pady=0)
        self.temp_slider.configure(command=lambda v: self.temp_val_label.configure(text=f"{v:.1f}"))

        # Humidity
        self.hum_label = ctk.CTkLabel(self.sidebar_frame, text="Humidity (%):")
        self.hum_label.grid(row=7, column=0, padx=20, pady=(10, 0))
        self.hum_slider = ctk.CTkSlider(self.sidebar_frame, from_=10, to=100, number_of_steps=90)
        self.hum_slider.grid(row=8, column=0, padx=20, pady=5)
        self.hum_val_label = ctk.CTkLabel(self.sidebar_frame, text="70")
        self.hum_val_label.grid(row=9, column=0, padx=20, pady=0)
        self.hum_slider.configure(command=lambda v: self.hum_val_label.configure(text=f"{int(v)}"))

        # Buttons
        self.predict_btn = ctk.CTkButton(self.sidebar_frame, text="Predict Load", command=self.make_prediction, fg_color="#2196F3", hover_color="#1976D2")
        self.predict_btn.grid(row=10, column=0, padx=20, pady=(30, 10))

        self.explain_btn = ctk.CTkButton(self.sidebar_frame, text="Explain (SHAP)", command=self.show_explanation, fg_color="#FF9800", hover_color="#F57C00")
        self.explain_btn.grid(row=11, column=0, padx=20, pady=10)

        self.appearance_mode_label = ctk.CTkLabel(self.sidebar_frame, text="Appearance Mode:", anchor="w")
        self.appearance_mode_label.grid(row=12, column=0, padx=20, pady=(20, 0))
        self.appearance_mode_optionemenu = ctk.CTkOptionMenu(self.sidebar_frame, values=["Light", "Dark", "System"], command=self.change_appearance_mode_event)
        self.appearance_mode_optionemenu.grid(row=13, column=0, padx=20, pady=(10, 20))
        self.appearance_mode_optionemenu.set("Dark")

    def setup_main_frame(self):
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(2, weight=1)

        # Header
        self.header_label = ctk.CTkLabel(self.main_frame, text="Load Forecast Results", font=ctk.CTkFont(size=24, weight="bold"))
        self.header_label.grid(row=0, column=0, padx=20, pady=20)

        # Prediction Cards Frame
        self.cards_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.cards_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        self.cards_frame.grid_columnconfigure((0, 1, 2), weight=1)

        # P10 Card
        self.p10_card = self.create_card(self.cards_frame, "P10 (Lower)", "0.0", "#4FC3F7", 0)
        # P50 Card
        self.p50_card = self.create_card(self.cards_frame, "P50 (Median)", "0.0", "#4CAF50", 1)
        # P90 Card
        self.p90_card = self.create_card(self.cards_frame, "P90 (Upper)", "0.0", "#F44336", 2)

        # Plot Frame
        self.plot_frame = ctk.CTkFrame(self.main_frame)
        self.plot_frame.grid(row=2, column=0, padx=20, pady=20, sticky="nsew")
        self.plot_label = ctk.CTkLabel(self.plot_frame, text="SHAP Feature Importance will appear here after clicking 'Explain'")
        self.plot_label.pack(expand=True)

        self.status_bar = ctk.CTkLabel(self.main_frame, text="Status: Ready", anchor="w")
        self.status_bar.grid(row=3, column=0, padx=20, pady=5, sticky="ew")

    def create_card(self, parent, title, value, color, column):
        card = ctk.CTkFrame(parent, border_width=2, border_color=color)
        card.grid(row=0, column=column, padx=10, pady=10, sticky="nsew")
        
        lbl_title = ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=14))
        lbl_title.pack(pady=(10, 0))
        
        lbl_val = ctk.CTkLabel(card, text=value, font=ctk.CTkFont(size=28, weight="bold"), text_color=color)
        lbl_val.pack(pady=(5, 10))
        
        unit_lbl = ctk.CTkLabel(card, text="MW", font=ctk.CTkFont(size=12))
        unit_lbl.pack(pady=(0, 10))
        
        return lbl_val

    def load_models_and_data(self):
        try:
            self.update_status("Loading models and data... please wait.")
            
            # Load Models
            for q in ['P10', 'P50', 'P90']:
                path = f'lgbm_quantile_{q}.txt'
                if os.path.exists(path):
                    self.models[q] = lgb.Booster(model_file=path)
                else:
                    raise FileNotFoundError(f"Model file {path} not found.")

            # Load Feature List
            if os.path.exists('feature_columns.txt'):
                with open('feature_columns.txt', 'r') as f:
                    self.feature_cols = [line.strip() for line in f.readlines()]
            else:
                raise FileNotFoundError("feature_columns.txt not found.")

            # Load Label Encoder
            if os.path.exists('label_encoder_event.pkl'):
                with open('label_encoder_event.pkl', 'rb') as f:
                    self.le_event = pickle.load(f)
            else:
                raise FileNotFoundError("label_encoder_event.pkl not found.")

            # Load Dataset for lookup (first 500 rows for speed in GUI dropdown)
            if os.path.exists('Integrated_Load_Data_Final.csv'):
                self.dataset = pd.read_csv('Integrated_Load_Data_Final.csv', nrows=2000)
                self.dataset['DATETIME'] = pd.to_datetime(self.dataset['DATETIME'], dayfirst=True)
                ts_list = self.dataset['DATETIME'].dt.strftime('%Y-%m-%d %H:%M').tolist()
                self.timestamp_option.configure(values=ts_list)
                self.timestamp_option.set(ts_list[0])
                self.on_timestamp_change(ts_list[0])
            else:
                self.update_status("Error: CSV not found. Manual input only.")

            # Initialize SHAP explainer for P50
            self.explainer = shap.TreeExplainer(self.models['P50'])
            
            self.update_status("Status: Models and Data loaded successfully.")
            
        except Exception as e:
            self.update_status(f"Error during initialization: {str(e)}")
            print(f"Init Error: {e}")

    def on_timestamp_change(self, ts_str):
        if self.dataset is not None:
            row = self.dataset[self.dataset['DATETIME'].dt.strftime('%Y-%m-%d %H:%M') == ts_str].iloc[0]
            self.temp_slider.set(row['ACT_TEMP'])
            self.temp_val_label.configure(text=f"{row['ACT_TEMP']:.1f}")
            self.hum_slider.set(row['ACT_HUMIDITY'])
            self.hum_val_label.configure(text=f"{int(row['ACT_HUMIDITY'])}")

    def feature_engineering(self, base_row, temp, humidity):
        """Replicates notebook feature engineering on a single row."""
        row = base_row.copy()
        
        # Update with manual overrides
        row['ACT_TEMP'] = temp
        row['ACT_HUMIDITY'] = humidity
        
        # Parse datetime
        dt = pd.to_datetime(row['DATETIME'])
        
        # Time features
        row['hour'] = dt.hour
        row['minute'] = dt.minute
        row['day_of_week'] = dt.dayofweek
        row['day_of_month'] = dt.day
        row['month'] = dt.month
        row['year'] = dt.year
        row['week_of_year'] = dt.isocalendar().week
        row['quarter'] = dt.quarter
        row['time_slot'] = dt.hour * 4 + dt.minute // 15
        row['is_weekend'] = 1 if dt.dayofweek >= 5 else 0
        
        # Cyclical
        row['hour_sin'] = np.sin(2 * np.pi * dt.hour / 24)
        row['hour_cos'] = np.cos(2 * np.pi * dt.hour / 24)
        row['month_sin'] = np.sin(2 * np.pi * dt.month / 12)
        row['month_cos'] = np.cos(2 * np.pi * dt.month / 12)
        row['dow_sin'] = np.sin(2 * np.pi * dt.dayofweek / 7)
        row['dow_cos'] = np.cos(2 * np.pi * dt.dayofweek / 7)
        
        # Event Encoding
        row['Event_Encoded'] = self.le_event.transform([str(row['Event_Name'])])[0]
        
        # Interactions
        row['temp_humidity'] = temp * humidity
        row['heat_index_sq'] = row['ACT_HEAT_INDEX'] ** 2
        row['cool_factor_sq'] = row['COOL_FACTOR'] ** 2

        # Lags & Rolling (For simplicity in GUI, we use existing values from CSV row 
        # or calculate simple ones. Real inference would need a window of history.)
        # Here we assume the CSV row already contains basic lags/rolling if pre-processed, 
        # but since we are using Integrated_Load_Data_Final.csv which might not have them,
        # we try to grab them or mock them for the demo.
        
        # Ensure all required features exist (fill with 0 if missing)
        for col in self.feature_cols:
            if col not in row:
                row[col] = 0.0
                
        # Return as DataFrame with correct columns and order
        return pd.DataFrame([row])[self.feature_cols]

    def make_prediction(self):
        try:
            ts_str = self.timestamp_option.get()
            base_row = self.dataset[self.dataset['DATETIME'].dt.strftime('%Y-%m-%d %H:%M') == ts_str].iloc[0]
            
            temp = self.temp_slider.get()
            hum = self.hum_slider.get()
            
            features_df = self.feature_engineering(base_row, temp, hum)
            self.current_features = features_df # Store for explanation
            
            p10 = self.models['P10'].predict(features_df)[0]
            p50 = self.models['P50'].predict(features_df)[0]
            p90 = self.models['P90'].predict(features_df)[0]
            
            self.p10_card.configure(text=f"{p10:.1f}")
            self.p50_card.configure(text=f"{p50:.1f}")
            self.p90_card.configure(text=f"{p90:.1f}")
            
            self.update_status(f"Prediction updated for {ts_str}")
            
        except Exception as e:
            self.update_status(f"Prediction Error: {str(e)}")

    def show_explanation(self):
        if not hasattr(self, 'current_features'):
            self.update_status("Error: Make a prediction first.")
            return

        try:
            self.update_status("Calculating SHAP values...")
            self.update() # Refresh UI
            
            shap_values = self.explainer(self.current_features)
            
            # Clear old plot
            for widget in self.plot_frame.winfo_children():
                widget.destroy()

            # Create SHAP Plot
            fig, ax = plt.subplots(figsize=(10, 6), dpi=100)
            
            # Waterfall for the single prediction
            shap.plots.waterfall(shap_values[0], max_display=10, show=False)
            
            plt.title("SHAP Feature Contribution (P50 Model)")
            plt.tight_layout()

            canvas = FigureCanvasTkAgg(fig, master=self.plot_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True)
            
            self.update_status("Explanation generated.")
            
        except Exception as e:
            self.update_status(f"Explanation Error: {str(e)}")

    def update_status(self, msg):
        self.status_bar.configure(text=f"Status: {msg}")

    def change_appearance_mode_event(self, new_appearance_mode: str):
        ctk.set_appearance_mode(new_appearance_mode)

if __name__ == "__main__":
    app = LoadForecasterGUI()
    app.mainloop()

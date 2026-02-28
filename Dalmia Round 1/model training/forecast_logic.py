import pandas as pd
import numpy as np
import lightgbm as lgb
import pickle
import os

class LoadForecaster:
    def __init__(self, model_dir='.'):
        self.model_dir = model_dir
        self.models = {}
        self.feature_cols = []
        self.le_event = None
        self.load_artifacts()

    def load_artifacts(self):
        # Load Quantile Models
        for q in ['P10', 'P50', 'P90']:
            model_path = os.path.join(self.model_dir, f'lgbm_quantile_{q}.txt')
            if os.path.exists(model_path):
                self.models[q] = lgb.Booster(model_file=model_path)
            else:
                raise FileNotFoundError(f"Model file {model_path} not found.")

        # Load Feature Columns
        feature_path = os.path.join(self.model_dir, 'feature_columns.txt')
        if os.path.exists(feature_path):
            with open(feature_path, 'r') as f:
                self.feature_cols = [line.strip() for line in f.readlines()]
        else:
            raise FileNotFoundError("feature_columns.txt not found.")

        # Load Label Encoder for Event_Name
        le_path = os.path.join(self.model_dir, 'label_encoder_event.pkl')
        if os.path.exists(le_path):
            with open(le_path, 'rb') as f:
                self.le_event = pickle.load(f)
        else:
            raise FileNotFoundError("label_encoder_event.pkl not found.")

    def engineer_time_features(self, df):
        df = df.copy()
        df['DATETIME'] = pd.to_datetime(df['DATETIME'], format='mixed', dayfirst=True)
        df['hour'] = df['DATETIME'].dt.hour
        df['minute'] = df['DATETIME'].dt.minute
        df['day_of_week'] = df['DATETIME'].dt.dayofweek
        df['day_of_month'] = df['DATETIME'].dt.day
        df['month'] = df['DATETIME'].dt.month
        df['year'] = df['DATETIME'].dt.year
        df['week_of_year'] = df['DATETIME'].dt.isocalendar().week.astype(int)
        df['quarter'] = df['DATETIME'].dt.quarter
        df['time_slot'] = df['hour'] * 4 + df['minute'] // 15
        df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
        
        # Cyclical features
        df['hour_sin'] = np.sin(2 * np.pi * df['hour'] / 24)
        df['hour_cos'] = np.cos(2 * np.pi * df['hour'] / 24)
        df['month_sin'] = np.sin(2 * np.pi * (df['month'] - 1) / 12)
        df['month_cos'] = np.cos(2 * np.pi * (df['month'] - 1) / 12)
        df['dow_sin'] = np.sin(2 * np.pi * df['day_of_week'] / 7)
        df['dow_cos'] = np.cos(2 * np.pi * df['day_of_week'] / 7)
        
        return df

    def predict_48h(self, history_df, future_weather_df):
        """
        history_df: Should contain at least 1 week of historical LOAD and weather.
        future_weather_df: 48 hours of weather forecast (192 intervals of 15 min).
        """
        # Ensure DATETIME is sorted
        history_df['DATETIME'] = pd.to_datetime(history_df['DATETIME'], format='mixed', dayfirst=True)
        history_df = history_df.sort_values('DATETIME').tail(1000)
        
        # Start predictions
        current_data = history_df.copy()
        predictions = []
        
        # Target timestamps (next 48 hours)
        last_time = current_data['DATETIME'].max()
        prediction_times = pd.date_range(start=last_time + pd.Timedelta(minutes=15), periods=192, freq='15min')
        
        # Determine fallback label (often 'Normal Day' or similar)
        fallback_label = 'Normal Day' if 'Normal Day' in self.le_event.classes_ else self.le_event.classes_[0]

        for i, target_time in enumerate(prediction_times):
            # 1. Get weather for this step
            weather_step = future_weather_df[future_weather_df['DATETIME'] == target_time]
            if weather_step.empty:
                weather_step = history_df.tail(1).copy() 
                weather_step['DATETIME'] = target_time
            
            # 2. Create row for this time step
            row = weather_step.copy()
            row = self.engineer_time_features(row)
            
            # 3. Handle Event_Encoded - Use fallback if label unseen
            event_val = row['Event_Name'].iloc[0] if 'Event_Name' in row.columns else fallback_label
            if event_val not in self.le_event.classes_:
                event_val = fallback_label
            
            row['Event_Encoded'] = self.le_event.transform([event_val])[0]
            
            # 4. Compute Lags from current_data
            row['lag_15min'] = current_data['LOAD'].iloc[-1]
            row['lag_1hr'] = current_data['LOAD'].iloc[-4] if len(current_data) >= 4 else current_data['LOAD'].mean()
            row['lag_1day'] = current_data['LOAD'].iloc[-96] if len(current_data) >= 96 else current_data['LOAD'].mean()
            row['lag_1week'] = current_data['LOAD'].iloc[-672] if len(current_data) >= 672 else current_data['LOAD'].mean()
            
            # 5. Compute Rolling Stats
            row['rolling_mean_1hr'] = current_data['LOAD'].tail(4).mean()
            row['rolling_std_1hr'] = current_data['LOAD'].tail(4).std() if len(current_data) >= 2 else 0
            row['rolling_mean_1day'] = current_data['LOAD'].tail(96).mean()
            row['rolling_std_1day'] = current_data['LOAD'].tail(96).std() if len(current_data) >= 2 else 0
            row['rolling_mean_1week'] = current_data['LOAD'].tail(672).mean()
            
            # 6. Differences
            row['load_diff_15min'] = row['lag_15min'] - (current_data['LOAD'].iloc[-2] if len(current_data) >= 2 else row['lag_15min'])
            row['load_diff_1hr'] = row['lag_15min'] - (current_data['LOAD'].iloc[-5] if len(current_data) >= 5 else row['lag_15min'])
            row['load_diff_1day'] = row['lag_15min'] - (current_data['LOAD'].iloc[-97] if len(current_data) >= 97 else row['lag_15min'])
            
            # 7. Interactions
            row['temp_humidity'] = row['ACT_TEMP'] * row['ACT_HUMIDITY']
            row['heat_index_sq'] = row['ACT_HEAT_INDEX']**2
            row['cool_factor_sq'] = row['COOL_FACTOR']**2
            
            # 8. Predict
            X = row[self.feature_cols]
            p10 = self.models['P10'].predict(X)[0]
            p50 = self.models['P50'].predict(X)[0]
            p90 = self.models['P90'].predict(X)[0]
            
            # 9. Update state (using p50 forecast for recursive lags)
            row['LOAD'] = p50
            row['P10'] = p10
            row['P50'] = p50
            row['P90'] = p90
            
            next_entry = pd.DataFrame({'DATETIME': [target_time], 'LOAD': [p50]})
            current_data = pd.concat([current_data, next_entry], ignore_index=True).tail(1000)
            predictions.append(row[['DATETIME', 'P10', 'P50', 'P90']])
            
        return pd.concat(predictions, ignore_index=True)
    def predict_single(self, datetime_str, temp, humidity, rain, heat_index, cool_factor, event_name, holiday_ind, base_load=1200):
        """
        Predicts load for a single timestamp with manual parameter overrides.
        base_load is used to mock lag features when no history is available.
        """
        dt = pd.to_datetime(datetime_str)
        
        # 1. Create a dummy row with the inputs
        data = {
            'DATETIME': [dt],
            'ACT_TEMP': [temp],
            'ACT_HUMIDITY': [humidity],
            'ACT_RAIN': [rain],
            'ACT_HEAT_INDEX': [heat_index],
            'COOL_FACTOR': [cool_factor],
            'Event_Name': [event_name],
            'Holiday_Ind': [holiday_ind]
        }
        df = pd.DataFrame(data)
        df = self.engineer_time_features(df)
        
        # 2. Handle Event Encoding
        fallback_label = 'Normal Day' if 'Normal Day' in self.le_event.classes_ else self.le_event.classes_[0]
        if event_name not in self.le_event.classes_:
            event_name = fallback_label
        df['Event_Encoded'] = self.le_event.transform([event_name])[0]
        
        # 3. Interactions
        df['temp_humidity'] = temp * humidity
        df['heat_index_sq'] = heat_index**2
        df['cool_factor_sq'] = cool_factor**2

        # 4. Mock lag & rolling features if model requires them
        lag_cols = ['lag_15min', 'lag_1hr', 'lag_1day', 'lag_1week',
                    'rolling_mean_1hr', 'rolling_mean_1day', 'rolling_mean_1week']
        std_cols = ['rolling_std_1hr', 'rolling_std_1day']
        diff_cols = ['load_diff_15min', 'load_diff_1hr', 'load_diff_1day']
        for col in lag_cols:
            if col in self.feature_cols:
                df[col] = base_load
        for col in std_cols:
            if col in self.feature_cols:
                df[col] = 0
        for col in diff_cols:
            if col in self.feature_cols:
                df[col] = 0
        
        # 5. Predict
        X = df[self.feature_cols]
        results = {
            'P10': round(self.models['P10'].predict(X)[0], 2),
            'P50': round(self.models['P50'].predict(X)[0], 2),
            'P90': round(self.models['P90'].predict(X)[0], 2)
        }
        return results

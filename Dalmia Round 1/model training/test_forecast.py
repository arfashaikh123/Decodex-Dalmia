import pandas as pd
import numpy as np
from forecast_logic import LoadForecaster
import os

def test_forecast():
    # 1. Setup paths
    model_dir = os.getcwd()
    forecaster = LoadForecaster(model_dir=model_dir)
    
    # 2. Load some real history to start from
    data_path = 'Integrated_Load_Data_Final.csv'
    if not os.path.exists(data_path):
        print(f"Data file {data_path} not found in {model_dir}")
        return
        
    df = pd.read_csv(data_path)
    df['DATETIME'] = pd.to_datetime(df['DATETIME'], format='mixed', dayfirst=True)
    
    history = df.sort_values('DATETIME').head(1002) # Use a chunk of history
    
    # 3. Create dummy weather forecast for 48 hours
    last_time = history['DATETIME'].max()
    future_times = pd.date_range(start=last_time + pd.Timedelta(minutes=15), periods=192, freq='15min')
    
    future_weather = pd.DataFrame({
        'DATETIME': future_times,
        'ACT_HEAT_INDEX': [history['ACT_HEAT_INDEX'].mean()] * 192,
        'ACT_HUMIDITY': [history['ACT_HUMIDITY'].mean()] * 192,
        'ACT_RAIN': [0] * 192,
        'ACT_TEMP': [history['ACT_TEMP'].mean()] * 192,
        'COOL_FACTOR': [history['COOL_FACTOR'].mean()] * 192,
        'Holiday_Ind': [0] * 192,
        'Event_Name': ['Normal Day'] * 192
    })
    
    # 4. Run forecast
    print("Starting 48-hour forecast...")
    predictions = forecaster.predict_48h(history, future_weather)
    
    print("Forecast completed!")
    print(predictions.head())
    print(predictions.tail())
    
    # 5. Summary check
    assert len(predictions) == 192, f"Expected 192 predictions, got {len(predictions)}"
    assert all(col in predictions.columns for col in ['DATETIME', 'P10', 'P50', 'P90'])
    print("✅ 48-hour forecast test passed.")

if __name__ == "__main__":
    test_forecast()

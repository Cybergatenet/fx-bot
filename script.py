# Python Script (adaptive_ml_predictor.py)

import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
import joblib

# Initialize MT5 connection
mt5.initialize()

# Fetch historical data
def get_historical_data(symbol, timeframe, n=1000):
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, n)
    df = pd.DataFrame(rates)
    return df[['open', 'high', 'low', 'close']]

# Prepare data for ML model
def prepare_data(df):
    scaler = MinMaxScaler()
    scaled_data = scaler.fit_transform(df)
    X, y = [], []
    for i in range(50, len(scaled_data)-3):
        X.append(scaled_data[i-50:i])
        y.append(scaled_data[i:i+3, 3])  # predict next 3 closing prices
    return np.array(X), np.array(y), scaler

# Train LSTM model
def train_lstm(X, y):
    model = Sequential([
        LSTM(50, activation='relu', input_shape=(X.shape[1], X.shape[2])),
        Dense(3)
    ])
    model.compile(optimizer='adam', loss='mse')
    model.fit(X, y, epochs=10, batch_size=32)
    return model

# Predict next 3 candles
def predict_next_candles(model, recent_data, scaler):
    recent_scaled = scaler.transform(recent_data)[-50:].reshape(1,50,4)
    prediction = model.predict(recent_scaled)
    # Reverse scaling only on 'close'
    close_scaler = scaler.scale_[3]
    close_min = scaler.min_[3]
    predicted_close = (prediction[0] - close_min) / close_scaler
    return predicted_close

# Main Function (train and predict adaptively)
def adaptive_ml(symbol="EURUSD", timeframe=mt5.TIMEFRAME_M5):
    df = get_historical_data(symbol, timeframe)
    X, y, scaler = prepare_data(df)
    model = train_lstm(X, y)

    # Save model and scaler
    model.save('adaptive_model.h5')
    joblib.dump(scaler, 'scaler.gz')

    # Predict
    next_closes = predict_next_candles(model, df[-50:], scaler)
    print("Predicted next 3 candle closes:", next_closes)

    # Write predictions to file for MQL5 EA
    np.savetxt("predictions.csv", next_closes, delimiter=",")
    
if __name__ == "__main__":
    adaptive_ml()
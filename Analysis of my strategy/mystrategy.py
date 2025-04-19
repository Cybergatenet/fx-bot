import MetaTrader5 as mt5
import pandas as pd
import time

# Connect to MetaTrader 5
if not mt5.initialize():
    print("Failed to initialize MetaTrader5")
    mt5.shutdown()

# Set up the symbol and timeframe
symbol = "XAUUSD"
timeframe = mt5.TIMEFRAME_H1

# Function to retrieve and calculate moving averages
def get_moving_averages(data):
    data['MA_2'] = data['close'].rolling(window=2).mean()
    data['MA_5'] = data['close'].rolling(window=5).mean()
    data['MA_100'] = data['close'].rolling(window=100).mean()
    return data

# Function to determine trading signals
def generate_signal(data):
    last_row = data.iloc[-1]
    prev_row = data.iloc[-2]
    
    if last_row['close'] > last_row['MA_100']:
        # Check for bullish crossover
        if prev_row['MA_2'] < prev_row['MA_5'] and last_row['MA_2'] > last_row['MA_5']:
            return 'buy'
    elif last_row['close'] < last_row['MA_100']:
        # Check for bearish crossover
        if prev_row['MA_2'] > prev_row['MA_5'] and last_row['MA_2'] < last_row['MA_5']:
            return 'sell'
    return None

# Main loop to execute strategy
while True:
    # Retrieve H1 data
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, 150)
    data = pd.DataFrame(rates)
    
    # Convert time in seconds to a datetime format
    data['time'] = pd.to_datetime(data['time'], unit='s')
    
    # Calculate moving averages
    data = get_moving_averages(data)
    
    # Generate signal
    signal = generate_signal(data)
    
    # Execute trade based on signal
    if signal == 'buy':
        print("Buy Signal Generated")
        # Add your order execution code here
    elif signal == 'sell':
        print("Sell Signal Generated")
        # Add your order execution code here
    
    # Sleep to avoid constant polling
    time.sleep(60 * 60)  # Runs every hour

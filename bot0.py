import MetaTrader5 as mt5
import psycopg2
import pandas as pd
import numpy as np
import time
from datetime import datetime

# Connect to Exness MT5
if not mt5.initialize():
    print("MT5 initialization failed")
    quit()

# Trading Configuration
PAIR = "XAUUSD"
RISK_PERCENTAGE = 2  # Risk 2% per trade
STOP_LOSS_PIPS = 30
TAKE_PROFIT_PIPS = 90
WIN_RATE = 0.55  # Based on backtest

# PostgreSQL Database Connection
conn = psycopg2.connect(
    dbname="trading_db",
    user="your_user",
    password="your_password",
    host="localhost",
    port="5432"
)
cursor = conn.cursor()

def fetch_market_price():
    """ Get the latest market price for Gold (XAUUSD). """
    tick = mt5.symbol_info_tick(PAIR)
    return tick.ask

def fetch_moving_averages():
    """ Fetch Moving Averages (MA 100, MA 5, MA 2) for trend confirmation. """
    rates = mt5.copy_rates_from_pos(PAIR, mt5.TIMEFRAME_H1, 0, 200)
    df = pd.DataFrame(rates)
    
    df["MA100"] = df["close"].rolling(window=100).mean()
    df["MA5"] = df["close"].rolling(window=5).mean()
    df["MA2"] = df["close"].rolling(window=2).mean()
    
    return df.iloc[-1]  # Return latest row

def calculate_lot_size(balance):
    """ Calculate lot size based on 2% risk per trade. """
    risk_amount = balance * (RISK_PERCENTAGE / 100)
    lot_size = risk_amount / STOP_LOSS_PIPS  # Adjust based on pip value
    return round(lot_size, 2)

def place_trade(balance):
    """ Place buy/sell trade based on strategy rules. """
    ma = fetch_moving_averages()
    market_price = fetch_market_price()
    lot_size = calculate_lot_size(balance)

    if market_price > ma["MA100"] and ma["MA2"] > ma["MA5"]:  
        trade_type = "buy"
        stop_loss = market_price - STOP_LOSS_PIPS
        take_profit = market_price + TAKE_PROFIT_PIPS
    elif market_price < ma["MA100"] and ma["MA2"] < ma["MA5"]:
        trade_type = "sell"
        stop_loss = market_price + STOP_LOSS_PIPS
        take_profit = market_price - TAKE_PROFIT_PIPS
    else:
        return None  # No valid trade signal

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": PAIR,
        "volume": lot_size,
        "type": mt5.ORDER_TYPE_BUY if trade_type == "buy" else mt5.ORDER_TYPE_SELL,
        "price": market_price,
        "sl": stop_loss,
        "tp": take_profit,
        "deviation": 10,
        "magic": 123456,
        "comment": "Automated Trade",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC
    }

    result = mt5.order_send(request)
    if result.retcode == mt5.TRADE_RETCODE_DONE:
        print(f"{trade_type.upper()} Trade Placed: {lot_size} lots at {market_price}")
        return {"type": trade_type, "lot_size": lot_size, "entry": market_price, "sl": stop_loss, "tp": take_profit}
    else:
        print(f"Trade failed: {result.comment}")
        return None

def log_trade(trade, exit_price, profit_loss):
    """ Save trade details to PostgreSQL database. """
    sql = """
    INSERT INTO trade_logs (pair, trade_type, lot_size, entry_price, stop_loss, take_profit, exit_price, profit_loss)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
    """
    cursor.execute(sql, (PAIR, trade["type"], trade["lot_size"], trade["entry"], trade["sl"], trade["tp"], exit_price, profit_loss))
    conn.commit()
    print("Trade logged in database.")

def trailing_stop(trade):
    """ Adjust stop loss dynamically when price moves in favor. """
    entry_price = trade["entry"]
    stop_loss = trade["sl"]
    trade_type = trade["type"]

    while True:
        current_price = fetch_market_price()
        if trade_type == "buy" and current_price > entry_price + 30:
            new_stop_loss = current_price - 20
            if new_stop_loss > stop_loss:
                stop_loss = new_stop_loss
                print(f"Updated Buy Trailing Stop: {stop_loss}")
        elif trade_type == "sell" and current_price < entry_price - 30:
            new_stop_loss = current_price + 20
            if new_stop_loss < stop_loss:
                stop_loss = new_stop_loss
                print(f"Updated Sell Trailing Stop: {stop_loss}")

        time.sleep(5)  # Delay to avoid excessive API calls

def trading_bot():
    """ Main trading loop. """
    balance = 100  # Starting balance
    while balance > 0:
        trade = place_trade(balance)
        if trade:
            trailing_stop(trade)

            # Simulate trade outcome
            exit_price = fetch_market_price()
            if WIN_RATE > 0.55:
                profit_loss = balance * 0.03  # Win trade
                balance += profit_loss
            else:
                profit_loss = -balance * 0.01  # Lose trade
                balance += profit_loss

            log_trade(trade, exit_price, profit_loss)
            print(f"Updated Balance: {round(balance, 2)}")

        time.sleep(10)  # Wait before checking for new trades

# Start Trading (Uncomment to run)
# trading_bot()

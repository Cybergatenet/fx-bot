CREATE TABLE trade_logs (
    id SERIAL PRIMARY KEY,
    trade_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    pair VARCHAR(10),
    trade_type VARCHAR(10),
    lot_size FLOAT,
    entry_price FLOAT,
    stop_loss FLOAT,
    take_profit FLOAT,
    exit_price FLOAT,
    profit_loss FLOAT
);

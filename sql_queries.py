# sql_queries.py

CREATE_PORTFOLIOS_TABLE = '''
CREATE TABLE IF NOT EXISTS portfolios (
    id INTEGER PRIMARY KEY,
    name TEXT,
    currency TEXT,
    deleted INTEGER DEFAULT 0
)
'''

CREATE_TRANSACTIONS_TABLE = '''
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY,
    portfolio_id INTEGER,
    coin_id TEXT,
    amount REAL,
    price_per_coin REAL,
    date TEXT,
    transaction_type TEXT,
    FOREIGN KEY (portfolio_id) REFERENCES portfolios(id)
)
'''

CREATE_COINS_TABLE = '''
CREATE TABLE IF NOT EXISTS coins (
    id INTEGER PRIMARY KEY,
    coin_id TEXT,
    coin_data TEXT,
    last_updated TEXT
)
'''

CREATE_COINSIDS_TABLE = '''
CREATE TABLE IF NOT EXISTS coins_ids (
    coin_id TEXT PRIMARY KEY,
    symbol TEXT,
    name TEXT
)
'''
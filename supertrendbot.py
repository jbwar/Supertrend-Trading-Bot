## Import all libraries, config files
import ccxt
import config
import schedule
import pandas as pd
pd.set_option("display.max_rows", None, "display.max_columns", None)

import warnings
warnings.filterwarnings('ignore')

import numpy as np
from datetime import datetime
import time


## Establish exchange and API
exchange = ccxt.coinbasepro({
    'apiKey': config.coinbase_api_public,
    'secret': config.coinbase_api_secret,
    'password': config.coinbase_api_passphrase
})


## Define true range tr function
def tr(data):
    data['previous_close'] = data['close'].shift(1)
    data['high-low'] = abs(data['high'] - data['low'])
    data['high-pc'] = abs(data['high'] - data['previous_close'])
    data['low-pc'] = abs(data['low'] - data['previous_close'])

    tr = data[['high-low', 'high-pc', 'low-pc']].max(axis=1)

    return tr

## Define atr function, period is by default 14 for average true range
def atr(data, period):
    data['tr'] = tr(data)
    atr = data['tr'].rolling(period).mean()

    return atr

## Define supertrend function
def supertrend(df, period=7, multiplier=3):
    hl2 = (df['high'] + df['low']) / 2     # define hl2 to calc upper and lower band
    df['atr'] = atr(df, period)
    # basic upper band = ((high + low) / 2) + (multiplier * atr)
    df['upperband'] = hl2 + (multiplier * df['atr'])
    # basic lower band = ((high + low) / 2) - (multiplier * atr)
    df['lowerband'] = hl2 - (multiplier * df['atr'])
    df['in_uptrend'] = True

    for current in range(1, len(df.index)):
        previous = current - 1
        print(current)

        if df['close'][current] > df['upperband'][previous]:
            df['in_uptrend'][current] = True
        elif df['close'][current] < df ['lowerband'] [previous]:
            df['in_uptrend'][current] = False
        else:
            df['in_uptrend'][current] = df['in_uptrend'][previous]

            if df['in_uptrend'][current] and df['lowerband'][current] < df['lowerband'][previous]:
                df['lowerband'][current] = df['lowerband'][previous]

            if not df['in_uptrend'][current] and df['upperband'][current] > df['upperband'][previous]:
                df['upperband'][current] = df['upperband'][previous]

    return df

## Define variable that determines if a position is already open
in_position = False

def check_buy_sell_signals(df):
    global in_position

    print('checking for buys and sells')
    print(df.tail(5))
    last_row_index = len(df.index) - 1
    previous_row_index = last_row_index - 1

    print(last_row_index)
    print(previous_row_index)

    if not df['in_uptrend'][previous_row_index] and df['in_uptrend'][last_row_index]:
        if not in_position:
            print("changed to uptrend, buy")
            # order = exchange.create_market_buy_order('ETH/USD', 0.01)
            # print(order)
            # in_position = True
        else:
            print('already in position, nothing to do')
    if df['in_uptrend'][previous_row_index] and not df['in_uptrend'][last_row_index]:
        if in_position:
            print('changed to downtrend, sell')
            # order = exchange.create_market_sell_order('ETH/USD', 0.01)
            # print(order)
            # in_position = False
        else:
            print("you aren't in position, nothing to sell")


def run_bot():
    print("Fetching new bars for {datetime.now().isoformat()}")
    bars = exchange.fetch_ohlcv('ETH/USD', timeframe='6h', limit=100)
    df = pd.DataFrame(bars[:-1], columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    #print(df)

    supertrend_data = supertrend(df)

    check_buy_sell_signals(supertrend_data)

schedule.every(1).hour.do(run_bot)


while True:
    schedule.run_pending()
    time.sleep(1)
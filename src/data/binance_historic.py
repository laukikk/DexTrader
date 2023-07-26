import os
from time import ctime
import datetime
import pandas as pd
from binance.client import Client


def get_historical_klines(symbol, interval, start_date):
    client = Client('API_KEY', 'API_SECRET')
    candlesticks = client.get_historical_klines(symbol, interval, start_date)
    return [[ctime(candlestick[0]/1000)] + candlestick[1:6] for candlestick in candlesticks]


def get_historic_data(symbol, interval, days=2):
    end_date = datetime.datetime.now()
    start_date = end_date - datetime.timedelta(days=days)
    start_date_str = start_date.strftime("%d %b, %Y")

    candlesticks = get_historical_klines(
        symbol=symbol, interval=interval, start_date=start_date_str)
    
    df = pd.DataFrame(candlesticks, columns=['Date', 'Open', 'High', 'Low', 'Close', 'Volume'])
    for col in df.columns:
        if col != 'Date':
            df[col] = df[col].astype(float)

    file_path = os.path.join(r'data\binance\historic', f"{symbol}_{end_date.strftime('%d%b%Y')}_{interval}.csv")
    df.to_csv(file_path, index=False)
    return df


if __name__ == '__main__':
    symbol = 'BTCUSDT'
    interval = '15m'
    get_historic_data(symbol=symbol, interval=interval)
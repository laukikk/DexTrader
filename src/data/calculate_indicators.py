import pandas as pd

from src.utils.indicators import *
from ta.momentum import StochRSIIndicator

class Indicators:
    def __init__(self):
        self.match_ind = {
            'supertrend': self.__get_SuperTrend,
            'sma': self.__get_SMA,
            'ema': self.__get_EMA,
            'macd': self.__get_MACD,
            'stoch_rsi': self.__get_StochasticRSI,
            'rsi': self.__get_RSI,
            'vwap': self.__get_VWAP,
            'bband': self.__get_BBand,
            'atr': self.__get_ATR
        }

    def get_indicators(self, df: pd.DataFrame, indicators: dict):
        '''Parent function that calls all the functions to calculate all the indicators
        present in the indicators dictionary
        
        Args:
            df (pd.DataFrame): Dataframe with OHLCV data
            indicators (dict): Dictionary with the indicators to calculate
        
        Returns:
            df (pd.DataFrame): Dataframe with OHLCV data and calculated indicators
        '''
        for parameter in indicators:
            if '-' in parameter:
                indicator, num = parameter.split('-')
                df = self.match_ind[indicator](df, indicators[parameter], num)
            else:
                try:
                    indicator = parameter
                    df = self.match_ind[indicator](df, indicators[parameter])
                except KeyError:
                    pass

        return df
    
    def __get_SuperTrend(self, src: pd.DataFrame, value: dict, num: int=0):
        df = src.copy()
        if num != 0:
            df[f'ST_{num}'] = SuperTrend(src, value['atr'], value['multiplier'])[0]
            df[f'STX_{num}'] = SuperTrend(src, value['atr'], value['multiplier'])[1]
        else:
            df[f'ST'] = SuperTrend(src, value['atr'], value['multiplier'])[0]
            df[f'STX'] = SuperTrend(src, value['atr'], value['multiplier'])[1]
        return df
    
    def __get_SMA(self, src: pd.DataFrame, value: int, num: int=0):
        df = src.copy()
        column_name = f'SMA_{num}' if num != 0 else 'SMA'
        df = SMA(df, 'Close', column_name, value)
        return df
    
    def __get_EMA(self, src: pd.DataFrame, value: int, num: int=0):
        df = src.copy()
        column_name = f'EMA_{num}' if num != 0 else 'EMA'
        df = EMA(df, 'Close', column_name, value)
        return df
    
    def __get_MACD(self, src: pd.DataFrame, value: dict):
        df = src.copy()
        try:
            df = MACD(df, value['ema_fast'], value['ema_slow'], value['signal'])
        except:
            df = MACD(df)
        return df
    
    def __get_StochasticRSI(self, src: pd.DataFrame, value: dict):
        df = src.copy()
        stochInd = StochRSIIndicator(df.Close, window=value)
        df['sRSI_d'] = stochInd.stochrsi_d()*100
        df['sRSI_k'] = stochInd.stochrsi_k()*100

        return df
    
    def __get_RSI(self, src: pd.DataFrame, value: dict):
        df = src.copy()
        df = RSI(df, period=value['rsi'])
        return df
    
    def __get_VWAP(self, src: pd.DataFrame, value: dict):
        '''Volume Weighted Average Price (VWAP)
        
        Args:
            src (pd.DataFrame): Dataframe with OHLCV data
            value (dict): Dictionary with the parameters to calculate the indicator
            
        Returns:
            df (pd.DataFrame): Dataframe with OHLCV data and calculated indicator
        '''
        df = src.copy()
        v = df['Volume'].values
        tp = (df['Low'] + df['Close'] + df['High']).div(3).values
        return df.assign(VWAP=(tp * v).cumsum() / v.cumsum())
    
    def __get_BBand(self, src: pd.DataFrame, value: dict):
        df = src.copy()
        df = BBand(df, period=value['period'], multiplier=value['multiplier'])
        return df
    
    def __get_ATR(self, src: pd.DataFrame, value: dict):
        df = src.copy()
        df = ATR(df, period=value['atr'])
        df.drop('TR', inplace=True, axis=1)
        return df

if __name__ == '__main__':
    import yaml
    import sys
    sys.path.append('..')


    src = pd.read_csv(r'data\binance\historic\BTCUSDT_21Apr2023_15m.csv')
    indicators = Indicators()

    parameters = yaml.safe_load(open(r'parameters.yaml'))
    df = indicators.get_indicators(src, parameters['triplesupertrend'])

    df.to_csv('test.csv')
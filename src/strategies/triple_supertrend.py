from binance.client import Client
from binance.enums import *

from .strategy import Strategy

class TripleSupertrendStrategy(Strategy):
    def __init__(self, df, parameters):
        super().__init__(df, parameters)
        
        
    def make_prediction(self):
        row = self.df.iloc[-1]
        if min(row.sRSI_d, row.sRSI_k) < self.parameters['rsi_oversold']:
            print('OVER SOLD')
            super_trend = [row.ST_9_3, row.ST_8_2, row.ST_7_1]
            super_trend_val = []
            for val in super_trend:
                if row.Close > val:
                    super_trend_val.append(val)
            super_trend_val.sort(reverse=True)

            if row.Close > row.EMA and (row.sRSI_d < row.sRSI_k and len(super_trend_val) > 1):
                availableBalance = self._get_available_balance()
                quantity = self._calculate_quantity(self.config, row, availableBalance)
                stopLoss = max(self.parameters['stop_loss_long']
                            * row.Close, super_trend_val[1])
                stopLoss = round(stopLoss, 2)
                takeProfit = row.Close + (row.Close - stopLoss) * 1.5
                takeProfit = round(takeProfit, 2)

                print(
                    f'Placing order: LONG at price: {row.Close} and quantity: {quantity}')
                print(f'Stop Loss: {stopLoss} \nTake Profit: {takeProfit}')
                orderIds = self._execute_trade_binance(SIDE_BUY, quantity=quantity,
                                            symbol=self.config['TRADE_SYMBOL'], positionSide='LONG', stopLoss=stopLoss, takeProfit=takeProfit)
                
                self._save_trade(self.config, row, 'LONG', quantity, availableBalance)
                return orderIds
            return False

        elif max(row.sRSI_d, row.sRSI_k) > self.parameters['RSI_OVERBOUGHT']:
            print('OVER BOUGHT')
            super_trend = [row.ST_9_3, row.ST_8_2, row.ST_7_1]
            super_trend_val = []
            for val in super_trend:
                if row.Close < val:
                    super_trend_val.append(val)
            super_trend_val.sort()

            if row.Close < row.EMA and (row.sRSI_d > row.sRSI_k and len(super_trend_val) > 1):
                availableBalance = self._get_available_balance()
                quantity = self._calculate_quantity(self.config, row, availableBalance)
                stopLoss = min(self.parameters['STOP_LOSS_SHORT']
                            * row.Close, super_trend_val[1])
                stopLoss = round(stopLoss, 2)
                takeProfit = row.Close + (row.Close - stopLoss) * 1.5
                takeProfit = round(takeProfit, 2)

                print(
                    f'Placing order: SHORT at price: {row.Close} and quantity: {quantity}')
                print(f'Stop Loss: {stopLoss} \nTake Profit: {takeProfit}')
                orderIds = self._execute_trade_binance(SIDE_SELL, quantity=quantity,
                                            symbol=self.config['TRADE_SYMBOL'], positionSide='SHORT', stopLoss=stopLoss, takeProfit=takeProfit)

                self._save_trade(self.config, row, 'LONG', quantity, availableBalance)
                return orderIds
            return False

        else:
            print('STRATEGY NOT IMPLEMENTED: RSI RANGE')
            return False
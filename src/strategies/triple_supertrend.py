from binance.enums import *

from .strategy import Strategy

class TripleSupertrendStrategy(Strategy):
    def __init__(self, parameters):
        super().__init__(parameters)
        self.strategy_parameters = self.parameters['strategy']
        

    def make_trade(self, type="trade", row=None):
        if row.empty==None: row = self.df_indicators.iloc[-1]

        # LONG
        if min(row.sRSI_d, row.sRSI_k) < self.strategy_parameters['rsi_oversold']:
            self.logger.debug('LONG signal')
            super_trend = [row.ST_3, row.ST_2, row.ST_1]
            super_trend_val = []
            for val in super_trend:
                if row.Close > val:
                    super_trend_val.append(val)
            super_trend_val.sort(reverse=True)

            if row.Close > row.EMA and (row.sRSI_d < row.sRSI_k and len(super_trend_val) > 1):
                self.logger.info('LONG entry')
                stopLoss = max(self.strategy_parameters['stop_loss_long']
                            * row.Close, super_trend_val[1])
                stopLoss = self._round_price(stopLoss)
                takeProfit = row.Close + (row.Close - stopLoss) * 1.5
                takeProfit = self._round_price(takeProfit)

                if type == "trade":
                    availableBalance = self._get_available_balance()
                    quantity = self._calculate_quantity(self.config, row, availableBalance)
                    self.logger.info(
                        f'Placing order: LONG at price: {row.Close} and quantity: {quantity}')
                    self.logger.info(f'Stop Loss: {stopLoss} \nTake Profit: {takeProfit}')
                    orderIds = self._execute_trade_binance(SIDE_BUY, quantity=quantity,
                                                symbol=self.config['TRADE_SYMBOL'], positionSide='LONG', stopLoss=stopLoss, takeProfit=takeProfit)
                    
                    self._save_trade(self.config, row, 'LONG', quantity, availableBalance)
                    return orderIds
                elif type == "backtest":
                    return {'side': 'LONG', 'entry': row.Close, 'quantity': None, 'stop_loss': stopLoss, 'take_profit': takeProfit}
                    
            return False

        # SHORT
        elif max(row.sRSI_d, row.sRSI_k) > self.strategy_parameters['rsi_overbought']:
            self.logger.debug('SHORT signal')
            super_trend = [row.ST_3, row.ST_2, row.ST_1]
            super_trend_val = []
            for val in super_trend:
                if row.Close < val:
                    super_trend_val.append(val)
            super_trend_val.sort()

            if row.Close < row.EMA and (row.sRSI_d > row.sRSI_k and len(super_trend_val) > 1):
                self.logger.info('SHORT entry')
                stopLoss = min(self.strategy_parameters['stop_loss_short']
                            * row.Close, super_trend_val[1])
                stopLoss = self._round_price(stopLoss)
                takeProfit = row.Close + (row.Close - stopLoss) * 1.5
                takeProfit = self._round_price(takeProfit)

                if type == "trade":
                    availableBalance = self._get_available_balance()
                    quantity = self._calculate_quantity(self.config, row, availableBalance)
                    self.logger.info(
                        f'Placing order: SHORT at price: {row.Close} and quantity: {quantity}')
                    self.logger.info(f'Stop Loss: {stopLoss} \nTake Profit: {takeProfit}')
                    orderIds = self._execute_trade_binance(SIDE_SELL, quantity=quantity,
                                                symbol=self.config['TRADE_SYMBOL'], positionSide='SHORT', stopLoss=stopLoss, takeProfit=takeProfit)

                    self._save_trade(self.config, row, 'LONG', quantity, availableBalance)
                    return orderIds
                elif type == "backtest":
                    return {'side': 'SHORT', 'entry': row.Close, 'quantity': None, 'stop_loss': stopLoss, 'take_profit': takeProfit}
            return False

        else:
            return False
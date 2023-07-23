import logging
from binance.client import Client
from binance.enums import *

from src.data.calculate_indicators import *
from ..keys import BINANCE_API_KEY, BINANCE_API_SECRET


class Strategy:
    ''' Parent Strategy class (All other strategies inherit from this class)

    Attributes:
        df (pandas.DataFrame): Dataframe with OHLCV data
        config (dict): Config file
        balance (float): Balance to trade with
    '''
    def __init__(self, df, config):
        self.config = config
        self.parameters = self.config[self.config['strategy_name']]
        self.indicators = Indicators()
        self.df = self.indicators.get_indicators(df, self.parameters)

        self.client = Client(BINANCE_API_KEY, BINANCE_API_SECRET)

    def _execute_trade_binance(self, side, quantity, symbol, positionSide, stopLoss, takeProfit):
        ''' Executes a trade on Binance
        
        Args:
            side (str): Side of the order (BUY or SELL)
            quantity (float): Quantity of the order
            symbol (str): Symbol to trade
            positionSide (str): Position side (LONG or SHORT)
            stopLoss (float): Stop loss price
            takeProfit (float): Take profit price

        Returns:
            Order ID, StopLoss Order ID, TakeProfit Order ID
        '''
        try:
            side_tpsl = 'BUY' if side == 'SELL' else 'SELL'
            self.client.futures_cancel_all_open_orders(symbol=symbol)
            order = self.client.futures_create_order(
                symbol=symbol, side=side, type=ORDER_TYPE_LIMIT_MAKER, quantity=quantity, isolated=True, positionSide=positionSide)
            order_stop_loss = self.client.futures_create_order(
                symbol=symbol, side=side_tpsl, type=FUTURE_ORDER_TYPE_STOP_MARKET, quantity=quantity, positionSide=positionSide, stopPrice=stopLoss, timeInForce=TIME_IN_FORCE_GTC)
            order_take_profit = self.client.futures_create_order(
                symbol=symbol, side=side_tpsl, type=FUTURE_ORDER_TYPE_TAKE_PROFIT_MARKET, quantity=quantity, positionSide=positionSide, stopPrice=takeProfit, timeInForce=TIME_IN_FORCE_GTC)
            print(order)
            logging.info(f"Order created: {order}, stop loss order ID: {order_stop_loss['orderId']}, take profit order ID: {order_take_profit['orderId']}")

        except Exception as e:
            logging.error(f"Error creating order: {e}")
            print("an exception occured - {}".format(e))
            return False

        return order['orderId'], order_stop_loss['orderId'], order_take_profit['orderId']

    def _execute_trade_backtest(self):
        pass

    def make_prediction(self):
        pass

    def backtest(self):
        pass

    def run(self):
        self.df.to_csv('res.csv')
        # print(self.df)

    def _get_available_balance(self, asset: str='USDT'):
        ''' Gets available balance from Binance account '''
        try:
            balance = self.client.futures_account_balance()
            availableBalance = -1
            for i in balance:
                if i['asset'] == asset:
                    availableBalance = float(i['availableBalance'])
                    break
            return availableBalance

        except Exception as e:
            logging.error(f"Error getting available balance: {e}")
            print("an exception occured - {}".format(e))
            return False
        
    def _get_current_position(self, symbol: str):
        ''' Gets current position from Binance account '''
        try:
            position = self.client.futures_position_information(symbol=symbol)
            return position

        except Exception as e:
            logging.error(f"Error getting current position: {e}")
            print("an exception occured - {}".format(e))
            return False
    
    def _calculate_quantity(self, config: dict, row: pd.Series, availableBalance: float):
        ''' Calculates the quantity to trade based on the available balance '''
        try:
            toUseBalance = availableBalance * 0.98
            quantity = toUseBalance / float(row['Close']) * config['leverage']
            return quantity

        except Exception as e:
            logging.error(f"Error calculating quantity: {e}")
            print("an exception occured - {}".format(e))
            return False
        
    def _save_trade(self, config, row, trade_type, quantity, balance):
        ''' Saves trade to a csv file '''
        try:
            with open('trades.csv', 'a') as f:
                f.write(f"{row['date']}, {config['trade_symbol']}, {row['Close']}, {trade_type}, {quantity}, {balance}\n")

        except Exception as e:
            logging.error(f"Error saving trade: {e}")
            print("an exception occured - {}".format(e))
            return False
        
    def _calculate_sl_tp(self, config, row, trade_type):
        ''' Calculates the stop loss and take profit prices '''
        try:
            if trade_type == 'BUY':
                stopLoss = row['Close'] * (1 - config['stop_loss'])
            else: # trade_type == 'SELL':
                stopLoss = row['Close'] * (1 + config['stop_loss'])
            return stopLoss

        except Exception as e:
            logging.error(f"Error calculating stop loss: {e}")
            print("an exception occured - {}".format(e))
            return False
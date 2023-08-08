import logging
from binance.client import Client
from binance.enums import *
from tqdm import tqdm

from src.data.calculate_indicators import *
from ..keys import BINANCE_API_KEY, BINANCE_API_SECRET


class Strategy:
    ''' Parent Strategy class (All other strategies inherit from this class)

    Attributes:
        df (pandas.DataFrame): Dataframe with OHLCV data
        config (dict): Config file
    '''
    def __init__(self, df, config):
        self.config = config
        self.parameters = self.config[self.config['strategy_name']]
        self.indicators = Indicators()
        self.df = self.indicators.get_indicators(df, self.parameters)
        self.trades = pd.DataFrame(columns=['date', 'symbol', 'side', 'quantity', 'entry', 'stop_loss', 'take_profit', 'result', '%pnl', 'pnl', 'balance', 'order_id', 'stop_loss_order_id', 'take_profit_order_id'])

        self.client = Client(BINANCE_API_KEY, BINANCE_API_SECRET)

    def _round_price(self, num: float):
        ''' Returns a number with 4 significant digits'''
        sig_req = 4
        try:
            l,r = str(num).split('.')
        except ValueError:
            return num
        if l != '0':
            return round(num, max(sig_req-len(l), 2))
        else:
            zero_count = 0
            for i in r:
                if i == '0':
                    zero_count += 1
                else:
                    break
            return round(num, max(4, zero_count+sig_req))

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

    def make_trade(self):
        '''updated by the child class'''
        pass

    def __execute_trade_backtest(self, date, trade_parameters, close_price, balance, result):
        if trade_parameters['side'] == "LONG":
            pnl = (close_price - trade_parameters['entry']) * balance / trade_parameters['entry']
        else:
            pnl = (trade_parameters['entry'] - close_price) * balance / trade_parameters['entry']

        pnl_percent = (pnl / balance) * 100
        balance += pnl

        return {
            'date': date,
            'symbol':  self.config['trade_symbol'],
            'side': trade_parameters['side'],
            'quantity': trade_parameters['quantity'],
            'entry': trade_parameters['entry'],
            'stop_loss': trade_parameters['stop_loss'],
            'take_profit': trade_parameters['take_profit'],
            'result': result,
            '%pnl': pnl_percent,
            'pnl': pnl,
            'balance': balance,
            'order_id': None,
            'stop_loss_order_id': None,
            'take_profit_order_id': None
        }



    def backtest(self, balance=1000) -> pd.DataFrame:
        isPositionOpen = False
        trade_parameters = None
        self.df.to_csv('indicators.csv')

        print('Backtesting...')
        for i in tqdm(range(len(self.df))):
            if not isPositionOpen:
                if self.df.iloc[i].isnull().sum() != 0:
                    continue

                trade = self.make_trade(type="backtest", row=self.df.iloc[i])

                if trade:
                    if self.config['type'] == "spot":
                        if trade['side'] == "LONG":
                            isPositionOpen = True
                            trade_parameters = trade

            elif isPositionOpen:
                print('-----position------')
                close_price = self.df.iloc[i].Close
                if trade_parameters['side'] == "LONG":
                    if close_price <= trade_parameters['stop_loss']:
                        print('long stop loss hit')
                        self.trades = self.trades.append(
                            self.__execute_trade_backtest(self.df.iloc[i].Date, trade_parameters, close_price, balance, 'stop_loss'),
                            ignore_index=True
                        )
                        isPositionOpen = False
                        trade_parameters = {}

                    elif close_price >= trade_parameters['take_profit']:
                        print('long take profit hit')
                        self.trades = self.trades.append(
                            self.__execute_trade_backtest(self.df.iloc[i].Date, trade_parameters, close_price, balance, 'take_profit'),
                            ignore_index=True
                        )
                        isPositionOpen = False
                        trade_parameters = {}

                elif trade_parameters['side'] == "SHORT":
                    if close_price >= trade_parameters['stop_loss']:
                        print('short stop loss hit')
                        self.trades = self.trades.append(
                            self.__execute_trade_backtest(self.df.iloc[i].Date, trade_parameters, close_price, balance, 'stop_loss'),
                            ignore_index=True
                        )
                        isPositionOpen = False
                        trade_parameters = {}

                    elif close_price <= trade_parameters['take_profit']:
                        print('short take profit hit')
                        self.trades = self.trades.append(
                            self.__execute_trade_backtest(self.df.iloc[i].Date, trade_parameters, close_price, balance, 'take_profit'),
                            ignore_index=True
                        )
                        isPositionOpen = False
                        trade_parameters = {}

        return self.trades

    def run(self):
        trades = self.backtest()
        trades.to_csv(f"backtest.csv", index=False)


    def _get_available_futures_balance(self, asset: str='USDT'):
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
        
    def _get_available_balance(self, asset: str, type:str='free'):
        ''' Gets available balance from Binance account
        
        Args:
            asset (str): Asset to get balance from
            type (str): Type of balance (free or locked)
        '''
        try:
            return self.client.get_asset_balance(asset=asset)[type]

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
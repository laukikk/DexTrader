import os
from datetime import datetime
from tqdm import tqdm
import seaborn as sns
import matplotlib.pyplot as plt

from binance.client import Client
from binance.enums import *

from ..utils.logging_config import configure_logging
from src.data.calculate_indicators import *
from src.data import binance_historic as binanceData
from ..keys import BINANCE_API_KEY, BINANCE_API_SECRET

sns.set_style("darkgrid")

class Strategy:
    ''' Parent Strategy class (All other strategies inherit from this class)

    Attributes:
        df (pandas.DataFrame): Dataframe with OHLCV data
        config (dict): Config file
    '''
    def __init__(self, config):
        self.indicators = Indicators()
        self.client = Client(BINANCE_API_KEY, BINANCE_API_SECRET)
        self.logger = configure_logging()

        self.config = config
        self.trades = pd.DataFrame()
        self.balance = None
        self.parameters = self.config[self.config['strategy_name']]

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
            self.logger.info(f"Order created: {order}, stop loss order ID: {order_stop_loss['orderId']}, take profit order ID: {order_take_profit['orderId']}")

        except Exception as e:
            self.logger.error(f"Error creating order: {e}")
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
        leverage = None

        if self.config['type'] == "futures":
            leverage = self.config['leverage']
            pnl *= leverage
            pnl_percent *= leverage

        self.balance = balance + pnl

        new_trade = {
            'date': date,
            'symbol':  self.config['trade_symbol'],
            'side': trade_parameters['side'],
            'quantity': trade_parameters['quantity'],
            'leverage': leverage,
            'entry': trade_parameters['entry'],
            'stop_loss': trade_parameters['stop_loss'],
            'take_profit': trade_parameters['take_profit'],
            'result': result,
            'pnl_percent': pnl_percent,
            'pnl': pnl,
            'balance': self.balance,
            'order_id': None,
            'stop_loss_order_id': None,
            'take_profit_order_id': None
        }

        if self.trades.empty:
            self.trades = pd.DataFrame([new_trade], columns=new_trade.keys())
        else:
            new_trade_df = pd.DataFrame([new_trade], columns=self.trades.columns)
            self.trades = pd.concat([self.trades, new_trade_df], ignore_index=True)

    def backtest(self, balance=1000) -> pd.DataFrame:
        print('BACKTESTING...')
        is_position_open = False
        trade_parameters = None
        self.balance = balance

        self.logger.info('Backtesting...')
        for i in tqdm(range(len(self.df_indicators))):
            if not is_position_open:
                if self.df_indicators.iloc[i].isnull().sum() != 0:
                    continue

                trade = self.make_trade(type="backtest", row=self.df_indicators.iloc[i])

                # only eliminates trades that are not meant to be executed
                # considered: spot, futures
                if trade:
                    if self.config['type'] == "spot":
                        if trade['side'] == "SHORT":
                            continue

                    is_position_open = True
                    trade_parameters = trade

            elif is_position_open:
                close_price = self.df_indicators.iloc[i].Close
                if trade_parameters['side'] in ["LONG", "SHORT"]:
                    if (trade_parameters['side'] == "LONG" and close_price >= trade_parameters['take_profit']) or \
                        (trade_parameters['side'] == "SHORT" and close_price <= trade_parameters['take_profit']):
                        self.logger.info(f'{trade_parameters["side"]} TakeProfit hit')
                        self.__execute_trade_backtest(self.df_indicators.iloc[i]['Date'], trade_parameters, close_price, self.balance, 'profit')
                        is_position_open = False
                        trade_parameters = {}
                    
                    elif (trade_parameters['side'] == "LONG" and close_price <= trade_parameters['stop_loss']) or \
                    (trade_parameters['side'] == "SHORT" and close_price >= trade_parameters['stop_loss']):
                        self.logger.info(f'{trade_parameters["side"]} StopLoss hit')
                        self.__execute_trade_backtest(self.df_indicators.iloc[i]['Date'], trade_parameters, close_price, self.balance, 'loss')
                        is_position_open = False
                        trade_parameters = {}

        return self.trades

    def run(self):
        start = datetime.now()
        current_date = datetime.now().strftime("%d%b%y")
        file_name = f"trades/backtest/{self.config['strategy_name']}/backtest_{current_date}_{self.config['type']}_{self.config['trade_symbol']}_{self.config['timeframe']}"

        self.df_ohlc = binanceData.get_historic_data(symbol=self.config['trade_symbol'], 
                                                    interval=self.config['time_interval'], 
                                                    days=self.config['timeframe'])
        self.df_indicators = self.indicators.get_indicators(self.df_ohlc, self.parameters)
        trades = self.backtest()
        try:
            trades.to_csv(file_name + ".csv", index=False)
        except OSError:
            os.makedirs(os.path.dirname(file_name))
            trades.to_csv(file_name, index=False)

        print(f'Time taken: {datetime.now() - start}')
        self.__draw_trade_result(trades, file_name)


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
            self.logger.error(f"Error getting available balance: {e}")
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
            self.logger.error(f"Error getting available balance: {e}")
            return False
        
    def _get_current_position(self, symbol: str):
        ''' Gets current position from Binance account '''
        try:
            position = self.client.futures_position_information(symbol=symbol)
            return position

        except Exception as e:
            self.logger.error(f"Error getting current position: {e}")
            return False
    
    def _calculate_quantity(self, config: dict, row: pd.Series, availableBalance: float):
        ''' Calculates the quantity to trade based on the available balance '''
        try:
            toUseBalance = availableBalance * 0.98
            quantity = toUseBalance / float(row['Close']) * config['leverage']
            return quantity

        except Exception as e:
            self.logger.error(f"Error calculating quantity: {e}")
            return False
        
    def _save_trade(self, config, row, trade_type, quantity, balance):
        ''' Saves trade to a csv file '''
        try:
            with open('trades.csv', 'a') as f:
                f.write(f"{row['date']}, {config['trade_symbol']}, {row['Close']}, {trade_type}, {quantity}, {balance}\n")

        except Exception as e:
            self.logger.error(f"Error saving trade: {e}")
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
            self.logger.error(f"Error calculating stop loss: {e}")
            return False
        

    def __draw_trade_result(self, trades, file_name):
        ''' Draws the trade result '''
        try:
            trades.reset_index(inplace=True)
            total_profits = len(trades[trades['result'] == 'profit'])
            total_losses = len(trades[trades['result'] == 'loss'])
            pnl_percent = trades['pnl_percent'].iloc[-1]
            final_balance = trades['balance'].iloc[-1]
            
            plt.figure(figsize=(10, 8))
            plt.suptitle(f'''{self.config["strategy_name"]} - {self.config["type"]} - {self.config["trade_symbol"]} - {self.config["timeframe"]} - {self.config["time_interval"]}
                            Total trades: {len(trades)}   Profits: {total_profits}   Losses: {total_losses}   PnL: {pnl_percent:.2f}%   Final Balance: {final_balance:.2f}''', y=1)

            plt.subplot(2, 1, 1)
            plt.title('Logarithmic scale', y=1.0, pad=-14)
            plt.yscale("log")
            sns.lineplot(trades['balance'], color='#424242')
            sns.scatterplot(data=trades, x="index", y="balance", hue="side", palette=['red', 'blue'], s=10)

            plt.subplot(2, 1, 2)
            plt.title('Linear scale', y=1.0, pad=-14)
            sns.lineplot(trades['balance'], color='#424242')
            sns.scatterplot(data=trades, x="index", y="balance", hue="side", palette=['red', 'blue'], s=10)

            plt.savefig(file_name + ".png")
            plt.show()
            plt.close()

        except Exception as e:
            self.logger.error(f"Error drawing trade result: {e}")
            print(f"Error drawing trade result: {e}")
            return False
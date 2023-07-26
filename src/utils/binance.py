from binance.client import Client
from binance.enums import *
import keys
import json

f = open('data.json',)
data = json.load(f)
symbol = data['TRADE_SYMBOL']

client = Client(keys.BINANCE_API_KEY, keys.BINANCE_API_SECRET)
# client.futures_change_leverage(symbol=symbol, leverage=5)


def order_futures(side1, side2, symbol, quantity, positionSide, stopLoss, takeProfit):
    try:
        # client.futures_cancel_all_open_orders(symbol=symbol)
        order = client.futures_create_order(
            symbol=symbol, side=side1, type=ORDER_TYPE_LIMIT_MAKER, quantity=quantity, isolated=True, positionSide=positionSide)
        order_stop_loss = client.futures_create_order(
            symbol=symbol, side=side2, type=FUTURE_ORDER_TYPE_STOP_MARKET, quantity=quantity, positionSide=positionSide, stopPrice=stopLoss, timeInForce=TIME_IN_FORCE_GTC)
        order_take_profit = client.futures_create_order(
            symbol=symbol, side=side2, type=FUTURE_ORDER_TYPE_TAKE_PROFIT_MARKET, quantity=quantity, positionSide=positionSide, stopPrice=takeProfit, timeInForce=TIME_IN_FORCE_GTC)
        print(order)

    except Exception as e:
        print("An error occured while placing the Futures Order - {}".format(e))
        return False

    return order, order_stop_loss, order_take_profit

def order(symbol, quantity, price, stopLoss, takeProfit):
    try:
        order = client.create_order(symbol, side=SIDE_BUY, type=ORDER_TYPE_LIMIT,
            timeInForce=TIME_IN_FORCE_GTC, quantity=quantity, price=price)
        order_stop_loss = client.create_order(symbol, side=SIDE_SELL, type=ORDER_TYPE_STOP_LOSS,
            timeInForce=TIME_IN_FORCE_GTC, quantity=quantity, stopPrice=stopLoss)
        order_take_profit = client.create_order(symbol, side=SIDE_SELL, type=ORDER_TYPE_TAKE_PROFIT,
            timeInForce=TIME_IN_FORCE_GTC, quantity=quantity, stopPrice=takeProfit)
        print(order)
         
    except Exception as e:
        print("An error occured while placing the Spot Order - {}".format(e))
        return False
    
    return order, order_stop_loss, order_take_profit
    

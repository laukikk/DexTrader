from binance.client import Client
from binance.enums import *
import keys
import json

f = open('data.json',)
data = json.load(f)
symbol = data['TRADE_SYMBOL']

client = Client(keys.BINANCE_API_KEY, keys.BINANCE_API_SECRET)
# client.futures_change_leverage(symbol=symbol, leverage=5)


def order(side1, side2, quantity, symbol, positionSide, stopLoss, takeProfit):
    try:
        client.futures_cancel_all_open_orders(symbol=symbol)
        order = client.futures_create_order(
            symbol=symbol, side=side1, type=ORDER_TYPE_LIMIT_MAKER, quantity=quantity, isolated=True, positionSide=positionSide)
        order_stop_loss = client.futures_create_order(
            symbol=symbol, side=side2, type=FUTURE_ORDER_TYPE_STOP_MARKET, quantity=quantity, positionSide=positionSide, stopPrice=stopLoss, timeInForce=TIME_IN_FORCE_GTC)
        order_take_profit = client.futures_create_order(
            symbol=symbol, side=side2, type=FUTURE_ORDER_TYPE_TAKE_PROFIT_MARKET, quantity=quantity, positionSide=positionSide, stopPrice=takeProfit, timeInForce=TIME_IN_FORCE_GTC)
        print(order)

    except Exception as e:
        print("an exception occured - {}".format(e))
        return False

    return order_stop_loss['orderId'], order_take_profit['orderId']

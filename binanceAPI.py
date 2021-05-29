import time
import hashlib
import requests
import hmac
import config
from enum import Enum, auto
from urllib.parse import urlencode

class BinanceAPI:
    
    BASE_URL = "https://testnet.binance.vision/api/v1"
    BASE_URL_V3 = "https://testnet.binance.vision/api/v3"
    COINS_SYMBOLS = None

    class OrderType(Enum):
        LIMIT = auto()
        MARKET_QUANTITY = auto()
        MARKET_FOR = auto()

    def __init__(self, key, secret):
        self.key = key
        self.secret = secret
        BinanceAPI.COINS_SYMBOLS = frozenset(self._all_symbols()) 

    def get_open_orders(self):
        return self._get("%s/openOrders" % (self.BASE_URL_V3))
    
    def cancel_all_open_orders(self, fcoin, scoin):
        symbol = self._get_symbol(fcoin, scoin)
        if symbol is not False:
            self._delete("%s/openOrders" % (self.BASE_URL_V3), {"symbol" : symbol})
            return True
        return "Given pair of coins is not listed on binance"

    def get_price(self, symbol):
        if symbol in self.COINS_SYMBOLS:
            return float(self._get_no_sign("%s/avgPrice" % (self.BASE_URL_V3), {"symbol" : symbol})['price'])
        return -1.0
    
    def get_coin_amount(self, coin_name="BTC"):
        path = "%s/account" % (self.BASE_URL_V3)
        account = self._get(path)
        for coin_dict in account["balances"]:
            if coin_dict["asset"] == coin_name:
                return float(coin_dict["free"])
        return 0.0

    def get_wallet(self):
        l = []
        account = self._get("%s/account" % (self.BASE_URL_V3))
        for coin_dict in account["balances"]:
            s = "%s: f: %s l: %s" % (coin_dict["asset"], coin_dict["free"], coin_dict["locked"])
            l.append(s)
        return l

    # MARKET BUY BEGIN
    def __buy_coin(self, bcoin, ammount, opcoin, ordertype):
        if bcoin + opcoin in self.COINS_SYMBOLS:
            params = self._order(bcoin + opcoin, ammount, "BUY", ordertype)
            order = self._post("%s/order" % (self.BASE_URL_V3), params)

            if order.get('msg') is not None:
                return "Cannot buy %s for %s. Reason: %s" % (bcoin, opcoin, order['msg'])
            if order.get('status') != 'FILLED':
                return "Cannot buy %s for %s. Order status: %s" % (bcoin, opcoin, order['status'])
        
            return (float(order['executedQty']), bcoin, float(order['cummulativeQuoteQty']), opcoin)
        elif opcoin + bcoin in self.COINS_SYMBOLS:
            if ordertype == self.OrderType.MARKET_QUANTITY:
                return self.sell_coin_for(opcoin, ammount, bcoin)
            return self.sell_coin(opcoin, ammount, bcoin)
        return "Cannot buy %s for %s. Reason: Given pair is not listed on Binance." % (bcoin, opcoin)

    def buy_coin(self, bcoin, ammount, opcoin):
        return self.__buy_coin(bcoin, ammount, opcoin, self.OrderType.MARKET_QUANTITY)
    
    def buy_coin_for(self, bcoin, ammount, opcoin):
        return self.__buy_coin(bcoin, ammount, opcoin, self.OrderType.MARKET_FOR)
    # MARKET BUY END

    # MARKET SELL BEGIN
    def __sell_coin(self, scoin, ammount, bcoin, ordertype):
        if scoin + bcoin in self.COINS_SYMBOLS:
            params = self._order(scoin + bcoin, ammount, "SELL", ordertype)
            order = self._post("%s/order" % (self.BASE_URL_V3), params)

            if order.get('msg') is not None:
                return "Cannot sell %s for %s. Reason: %s" % (scoin, bcoin, order['msg'])
            if order.get('status') != 'FILLED':
                return "Cannot sell %s for %s. Order status: %s" % (scoin, bcoin, order['status']) 
            
            return (float(order['cummulativeQuoteQty']), bcoin, float(order['executedQty']), scoin)
        elif bcoin + scoin in self.COINS_SYMBOLS:
            if ordertype == self.OrderType.MARKET_QUANTITY:
                return self.buy_coin_for(bcoin, ammount, scoin)
            return self.buy_coin(bcoin, ammount, scoin)
        return "Cannot sell %s for %s. Reason: Given pair is not listed on Binance." % (scoin, bcoin)

    def sell_coin(self, scoin, ammount, bcoin):
        return self.__sell_coin(scoin, ammount, bcoin, self.OrderType.MARKET_QUANTITY)
    
    def sell_coin_for(self, scoin, ammount, bcoin):
        return self.__sell_coin(scoin, ammount, bcoin, self.OrderType.MARKET_FOR)
    # MARKET SELL END

    # LIMIT ORDERS
    def __limit_order(self, bcoin, ammount, scoin, price, side):
        params = dict()
        trade_pair = ("buy", bcoin, scoin)
        if bcoin + scoin in self.COINS_SYMBOLS:
            if side == "BUY":
                params = self._order(bcoin + scoin, ammount, "BUY", self.OrderType.LIMIT, price)
            else:
                params = self._order(bcoin + scoin, ammount * price, "BUY", self.OrderType.LIMIT, 1.0 / price)
        elif scoin + bcoin in self.COINS_SYMBOLS:
            if side == "SELL":
                params = self._order(scoin + bcoin, ammount, "SELL", self.OrderType.LIMIT, price)
            else:
                params = self._order(scoin + bcoin, ammount * price, "SELL", self.OrderType.LIMIT, 1.0 / price)
            trade_pair = ("sell", scoin, bcoin)
        else:
            return "Cannot limit %s %s for %s. Reason: Given pair is not listed on Binance" % trade_pair

        order = self._post("%s/order" % (self.BASE_URL_V3), params)

        if order.get('msg') is not None:
            return "Cannot limit %s %s for %s. Reason: %s" % tuple(list(trade_pair) + [order['msg']])
        order_status = order.get('status')
        if order_status != "NEW" and order_status != "FILLED":
            return "Cannot limit %s %s for %s. Order status: %s" % tuple(list(trade_pair) + [order['status']])
        
        return True
    
    def limit_buy(self, bcoin, ammount, opcoin, price):
        return self.__limit_order(bcoin, ammount, opcoin, price, "BUY")

    def limit_sell(self, scoin, ammount, bcoin, price):
        return self.__limit_order(bcoin, ammount, scoin, price, "SELL")
    # LIMIT ORDERS END

    def _all_symbols(self):
        l = []
        exchange_info = self._get_no_sign("%s/exchangeInfo" % (self.BASE_URL_V3))
        for symbol_dict in exchange_info['symbols']:
            l.append(symbol_dict['symbol'])
        return l

    def _get_no_sign(self, path, params={}):
        query = urlencode(params)
        url = "%s?%s" % (path, query)
        return requests.get(url, timeout=30, verify=True).json()
    
    def _sign(self, params={}):
        data = params.copy()
        ts = int(1000 * time.time())
        data.update({"timestamp": ts})
        h = urlencode(data)
        b = bytearray()
        b.extend(self.secret.encode())
        signature = hmac.new(b, msg=h.encode('utf-8'), digestmod=hashlib.sha256).hexdigest()
        data.update({"signature": signature})
        return data

    def _get(self, path, params={}):
        params.update({"recvWindow": config.recv_window})
        query = urlencode(self._sign(params))
        url = "%s?%s" % (path, query)
        header = {"X-MBX-APIKEY": self.key}
        return requests.get(url, headers=header, \
            timeout=30, verify=True).json()

    def _post(self, path, params={}):
        params.update({"recvWindow": config.recv_window})
        query = urlencode(self._sign(params))
        header = {"X-MBX-APIKEY": self.key}
        return requests.post(path, headers=header, data=query, \
            timeout=30, verify=True).json()
    
    def _delete(self, path, params={}):
        params.update({"recvWindow": config.recv_window})
        query = urlencode(self._sign(params))
        header = {"X-MBX-APIKEY": self.key}
        return requests.delete(path, headers=header, data=query, \
            timeout=30, verify=True).json()

    def _order(self, symbol, ammount, side, ordertype, price = None):
        params = {}
        params["type"] = "MARKET"

        if ordertype == self.OrderType.LIMIT:
            params["type"] = "LIMIT"
            params["price"] = price
            params["timeInForce"] = "GTC"
            params["quantity"] = ammount
        elif ordertype == self.OrderType.MARKET_FOR:
            params["quoteOrderQty"] = ammount
        else:
            params["quantity"] = ammount
        
        params["symbol"] = symbol
        params["side"] = side

        return params

    def _get_symbol(self, first_coin, second_coin):
        if first_coin + second_coin in self.COINS_SYMBOLS:
            return first_coin + second_coin
        elif second_coin + first_coin in self.COINS_SYMBOLS:
            return second_coin + first_coin
        return False
import time
import hashlib
import requests
import hmac
import json
import config
from enum import Enum, auto
from urllib.parse import urlencode

class BinanceAPI:
    
    #Spot test URLS
    BASE_URL = "https://testnet.binance.vision/api/v1"
    BASE_URL_V3 = "https://testnet.binance.vision/api/v3"
    COINS_SYMBOLS = None


    class OrderType(Enum):
        QUANTITY = auto()
        QUOUTE_ORDER_QTY = auto()

    def __init__(self, key, secret):
        self.key = key
        self.secret = secret
        BinanceAPI.COINS_SYMBOLS = frozenset(self.all_symbols())
        
    def get_server_time(self):
        path = "%s/time" % (self.BASE_URL_V3)
        return self._get_no_sign(path)

    def get_open_orders(self):
        return self._get("%s/openOrders" % (self.BASE_URL_V3))
    
    def sell_coin_for(self, scoin, bcoin, quantity):
        params = self._order(scoin + bcoin, quantity, "SELL", self.OrderType.QUOUTE_ORDER_QTY)
        return self._post("%s/order" % (self.BASE_URL_V3), params)

    def sell_coin(self, scoin, bcoin, quantity):
        if quantity <= 0.0:
            print("Quantity has to be positve number")
            return None
        if self.get_coin_amount(scoin) < quantity:
            print("You don't have enough %s to sell" % (scoin))
            return None
        
        invert_flag = False
        order = None
        if scoin + bcoin in self.COINS_SYMBOLS:
            params = self._order(scoin + bcoin, quantity, "SELL", self.OrderType.QUANTITY)
            order = self._post("%s/order" % (self.BASE_URL_V3), params)
        elif bcoin + scoin in self.COINS_SYMBOLS:
            order = self.buy_coin_for(bcoin, scoin, quantity)
            invert_flag = True
        else:
            print("Trade is not possible. There are not %s/%s offers" % (bcoin, scoin))
            return None

        if order.get('msg') is not None:
            print("We cannot sell %s for %s. Reason: %s" % (scoin, bcoin, order['msg']))
            return None
        if order.get('status') != 'FILLED':
            print("We cannot sell %s for %s. Order status: %s" % (scoin, bcoin, order['status']))
            return None
        
        result = (float(order['executedQty']), scoin, float(order['cummulativeQuoteQty']), bcoin)
        if invert_flag:
            result = (float(order['cummulativeQuoteQty']), scoin, float(order['executedQty']), bcoin)
        print(result)
        return result

    def buy_coin_for(self, bcoin, scoin, quantity):
        params = self._order(bcoin + scoin, quantity, "BUY", self.OrderType.QUOUTE_ORDER_QTY)
        return self._post("%s/order" % (self.BASE_URL_V3), params)

    def buy_coin(self, bcoin, scoin, quantity):
        if quantity <= 0.0:
            print("Quantity has to be positve number")
            return None
        order = None
        invert_flag = False
        if bcoin + scoin in self.COINS_SYMBOLS:
            params = self._order(bcoin + scoin, quantity, "BUY", self.OrderType.QUANTITY)
            order = self._post("%s/order" % (self.BASE_URL_V3), params)
        elif scoin + bcoin in self.COINS_SYMBOLS:
            order = self.sell_coin_for(scoin, bcoin, quantity)
            invert_flag = True
        else:
            print("Trade is not possible. There are not %s/%s offers" % (bcoin, scoin))
            return None

        if order.get('msg') is not None:
            print("We cannot buy %s for %s. Reason: %s" % (bcoin, scoin, order['msg']))
            return None
        if order.get('status') != 'FILLED':
            print("We cannot buy %s for %s. Order status: %s" % (bcoin, scoin, order['status']))
            return None
        
        result = (float(order['executedQty']), bcoin, float(order['cummulativeQuoteQty']), scoin)
        if invert_flag:
            result = (float(order['cummulativeQuoteQty']), bcoin, float(order['executedQty']), scoin)
        print(result)
        return result

    def get_price(self, symbol):
        if symbol in self.COINS_SYMBOLS:
            return float(self._get_no_sign("%s/avgPrice" % (self.BASE_URL_V3), {"symbol" : symbol})['price'])
        return -1.0

    def all_symbols(self):
        l = []
        exchange_info = self._get_no_sign("%s/exchangeInfo" % (self.BASE_URL_V3))
        for symbol_dict in exchange_info['symbols']:
            l.append(symbol_dict["symbol"])
        return l
    
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
        url = "%s" % (path)
        header = {"X-MBX-APIKEY": self.key}
        return requests.post(url, headers=header, data=query, \
            timeout=30, verify=True).json()

    def _order(self, market, quantity, side, ordertype):
        params = {}
         
        if ordertype == self.OrderType.QUANTITY:
            params["quantity"] = '%.8f' % (quantity)
        else:
            params["quoteOrderQty"] = '%.8f' % (quantity)
        params["type"] = "MARKET"
        params["symbol"] = market
        params["side"] = side
        
        return params
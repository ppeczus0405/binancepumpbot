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

    # BUY/SELL BEGIN 
    
    def buy_coin(bcoin, ammount, opcoin):
        pass
    
    def buy_coin_for(bcoin, ammount, opcoin):
        pass

    def sell_coin(scoin, ammount, bcoin):
        pass
    
    def sell_coin_for(scoin, ammout, bcoin):
        pass

    def limit_sell(scoin, ammount, price, bcoin):
        pass

    # BUY/SELL END

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
        url = "%s" % (path)
        header = {"X-MBX-APIKEY": self.key}
        return requests.post(url, headers=header, data=query, \
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




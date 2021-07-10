import requests
import config
import json
from enum import Enum, auto
from urllib.parse import urlencode


class OrderType(Enum):
    LIMIT = auto()
    MARKET = auto()


class OrderSide(Enum):
    BUY = auto()
    SELL = auto()


class BinanceAPI:
    
    BASE_URL = "https://www.binance.com"
    BASE_API_URL = "https://api.binance.com/api/v3"
    COINS_SYMBOLS = frozenset()
    TICK_STEP_DICT = dict()

    def __init__(self, key, secret, timeout=20, verify=True):
        self.req_timeout = timeout
        self.req_verify = verify
        self.key = key
        self.secret = secret
        self.headers = dict()
        self.__fill_symbols_dicts()
        self.__process_template(config.binance_header)

    def _get(self, url, params={}):
        request_headers = dict()
        request_headers.update(self.headers)
        request_url = "%s?%s" % (url, urlencode(params))
        return requests.get(request_url, headers=request_headers,
                            verify=self.req_verify, timeout=self.req_timeout).json()

    def _post(self, url, params={}):
        request_headers = dict()
        request_headers.update(self.headers)
        return requests.post(url, headers=request_headers, json=json.dumps(params),
                             verify=self.req_verify, timeout=self.req_timeout).json()

    def market_order(self, symbol, side, size=0, funds=0):
        if size > 0:
            order_params = self._order(symbol, side, OrderType.MARKET, size=size)
        else:
            order_params = self._order(symbol, side, OrderType.MARKET, funds=funds)
        url = "%s/%s" % (BinanceAPI.BASE_URL, "/bapi/mbx/v1/private/mbxgateway/order/place")
        return self._post(url, order_params)

    def _order(self, symbol, side, order_type, size=0, funds=0, price=0):
        params = dict()
        params['side'] = "BUY" if side == OrderSide.BUY else "SELL"
        params['symbol'] = symbol
        params['type'] = "MARKET"
        size_tick, price_tick = BinanceAPI.TICK_STEP_DICT[symbol]

        if funds > 0:
            params["quoteOrderQty"] = "%0.8f" % funds
        else:
            params['quantity'] = self._fix_value_to_pass_filters(size, size_tick)

        if order_type == OrderType.LIMIT:
            params['type'] = "LIMIT"
            params['timeInForce'] = "GTC"
            params['price'] = self._fix_value_to_pass_filters(price, price_tick)

        return params

    def _fix_value_to_pass_filters(self, val, correction):
        val = str(val)
        dot = val.find('.')
        if dot == -1:
            return val + '.' + '0' * (len(correction) - 2)
        if correction[0] == '1':
            return val[:dot + 1] + '0' * (len(correction) - 2)
        after_dot_val = val[dot + 1:]
        after_dot_correction = correction[2:]
        one_pos = after_dot_correction.find('1')
        if one_pos >= len(after_dot_val) - 1:
            after_dot_val += '0' * (len(after_dot_correction) - len(after_dot_val))
        else:
            after_dot_val = after_dot_val[:one_pos + 1] + '0' * (len(after_dot_correction) - one_pos - 1)
        return val[:dot + 1] + after_dot_val

    def __process_template(self, template):
        for line in template.split("\n"):
            if self.__line_is_necessary(line):
                line_words = line.split(" ")
                header = line_words[0][:-1]
                header_content = line[len(header) + 2:]
                self.headers[header] = header_content

    def __line_is_necessary(self, line):
        return (line.find("Referer") == -1 and
                line.find("Content-Length") == -1 and
                line.find("Origin") == -1 and
                line.find("Host") == -1 and
                line.find("POST") == -1)

    def __fill_symbols_dicts(self):
        all_symbols = []
        exchange_info = self._get("%s/exchangeInfo" % BinanceAPI.BASE_API_URL)
        for symbol_dict in exchange_info['symbols']:
            symbol = symbol_dict['symbol']
            all_symbols.append(symbol)
            size_tick = price_tick = 0.0
            for filter_dict in symbol_dict['filters']:
                if filter_dict['filterType'] == 'PRICE_FILTER':
                    price_tick = filter_dict['tickSize']
                elif filter_dict['filterType'] == 'LOT_SIZE':
                    size_tick = filter_dict['stepSize']
            BinanceAPI.TICK_STEP_DICT[symbol] = (size_tick, price_tick)
        BinanceAPI.COINS_SYMBOLS = frozenset(all_symbols)

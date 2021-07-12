# Pump
expected_profit = 50  # Profit in percent. For example if you want make 150$ from 100$ set to 50.
coin = "BTC"
coins_to_pump = 0.05

# Binance config
binance_header = """POST /bapi/mbx/v1/private/mbxgateway/order/place HTTP/1.1
Host: www.binance.com
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0
Accept: */*
Accept-Language: pl,en-US;q=0.7,en;q=0.3
Accept-Encoding: gzip, deflate, br
Referer: https://www.binance.com/en/trade/XRP_BTC?layout=pro&type=spot
lang: en
x-ui-request-trace: xx
x-trace-id: xx
bnc-uuid: xx
content-type: application/json
device-info: xx
clienttype: web
fvideo-id: xx
csrftoken: xx
Content-Length: 64
Origin: https://www.binance.com
DNT: 1
Connection: keep-alive
Cookie: xx"""

# Telegram config
telegram_api_id = 123
telegram_api_hash = "Telegram API hash"
telegram_chat_name = "WallStreetBets - Pumps"
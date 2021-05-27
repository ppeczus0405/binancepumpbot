import config
import time
from binanceAPI import BinanceAPI


if __name__ == "__main__":
    client = BinanceAPI(config.binance_api_key, config.binance_api_secret)
    print("All symbols: %s" % (" ".join(BinanceAPI.COINS_SYMBOLS)))

    while True:
        print("\n".join(client.get_wallet()))
        operation = input("Do you want SELL(s) or BUY(b): ")
        if operation != "s" and operation != "b":
            continue
        
        order = None
        bc = ""
        sc = ""
        q = float(input("Quantity: "))
        if operation == "s":
            sc = input("Selled coin name: ")
            bc = input("For: ")
            order = client.sell_coin(sc, bc, q)
        else:
            bc = input("Buyed coin name: ")
            sc = input("For: ")
            order = client.buy_coin(bc, sc, q)
        
        if order is not None:
            print(order)
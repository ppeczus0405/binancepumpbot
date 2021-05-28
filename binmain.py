import config
from binanceAPI import BinanceAPI

if __name__ == "__main__":
    client = BinanceAPI(config.binance_api_key, config.binance_api_secret)
    print("All symbols: %s" % (" ".join(BinanceAPI.COINS_SYMBOLS)))

    while True:
        print("\n".join(client.get_wallet()))
        operation = input("Do you want BUY_AMMOUNT(ba), BUY_FOR(bf), SELL_AMMOUNT(sa), SELL_FOR(sf): ")
        if operation not in ("ba, bf, sa, sf"):
            continue
        
        order = None
        bc = ""
        sc = ""
        q = float(input("Quantity: "))
        if operation == "ba":
            bc = input("Buyed coin name: ")
            sc = input("For: ")
            order = client.buy_coin(bc, q, sc)
        elif operation == "bf":
            bc = input("Buyed coin name: ")
            sc = input("For: ")
            order = client.buy_coin_for(bc, q, sc)
        if operation == "sa":
            sc = input("Selled coin name: ")
            bc = input("For: ")
            order = client.sell_coin(sc, q, bc)
        if operation == "sf":
            sc = input("Selled coin name: ")
            bc = input("For: ")
            order = client.sell_coin_for(sc, q, bc)
        print(order)
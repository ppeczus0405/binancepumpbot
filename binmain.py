import config
from binanceAPI import BinanceAPI

if __name__ == "__main__":
    client = BinanceAPI(config.binance_api_key, config.binance_api_secret)
    print("All symbols: %s" % (" ".join(BinanceAPI.COINS_SYMBOLS)))

    while True:
        print("\n".join(client.get_wallet()))
        print("Open orders: ")
        print(client.get_open_orders())
        inp = "Do you want BUY_AMMOUNT(ba), BUY_FOR(bf), SELL_AMMOUNT(sa), SELL_FOR(sf), "
        input_text = inp + "LIMIT_BUY(lb), LIMIT_SELL(ls), CANCEL_ALL(ca): "
        operation = input(input_text)
        if operation not in ("ba", "bf", "sa", "sf", "lb", "ls", "ca"):
            continue
        
        order = None
        bc = ""
        sc = ""
        if operation == "ba":
            q = float(input("Quantity: "))
            bc = input("Buyed coin name: ")
            sc = input("For: ")
            order = client.buy_coin(bc, q, sc)
        elif operation == "bf":
            q = float(input("Quantity: "))
            bc = input("Buyed coin name: ")
            sc = input("For: ")
            order = client.buy_coin_for(bc, q, sc)
        elif operation == "sa":
            q = float(input("Quantity: "))
            sc = input("Selled coin name: ")
            bc = input("For: ")
            order = client.sell_coin(sc, q, bc)
        elif operation == "sf":
            q = float(input("Quantity: "))
            sc = input("Selled coin name: ")
            bc = input("For: ")
            order = client.sell_coin_for(sc, q, bc)
        elif operation == "lb":
            q = float(input("Quantity: "))
            bc = input("Buyed coin name: ")
            sc = input("For: ")
            price = float(input("Price: "))
            order = client.limit_buy(bc, q, sc, price)
        elif operation == "ls":
            q = float(input("Quantity: "))
            sc = input("Selled coin name: ")
            bc = input("For: ")
            price = float(input("Price: "))
            order = client.limit_sell(sc, q, bc, price)
        elif operation == "ca":
            sym = input("Symbol: ")
            order = client.cancel_all_open_orders(sym)
        print(order)
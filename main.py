from telethon import TelegramClient
from binanceAPI import BinanceAPI
import config
import time

pumped_coin = None
telegram_client = TelegramClient("peczi", config.telegram_api_id, config.telegram_api_hash)

async def get_pumped_coin():
    # Getting chat id to explore messages
    global pumped_coin
    chatid = None
    async for dialog in telegram_client.iter_dialogs():
        if dialog.name == config.telegram_chat_name:
            chatid = dialog.id
    if chatid is None:
        print("Cannot find chat named: %s" % (telegram_chat_name))
        return

    # Searching coin name in last message in chat
    i = 0
    while pumped_coin is None:
        print("Looking for coin name(%d) ..." % (i))
        # Get last message and divide into words
        async for message in telegram_client.iter_messages(chatid, 1):
            all_words = message.text.split(" ")
            for word in all_words:
                # If message has '#' it is a coin name
                if '#' in word:
                    position = word.find('#') + 1
                    for index in range(position, len(word)):
                        if not word[index].isalpha():
                            pumped_coin = word[position:index]
                            break
                    break
        i = i + 1
        time.sleep(config.message_update_time)


def do_work():
    global pumped_coin
    # Initialize BinAPI client
    print("Initializing BinanceAPI client...")
    client = BinanceAPI(config.binance_api_key, config.binance_api_secret)
    print("\n".join(client.get_wallet()))
    if(input("It's your wallet?(y or n): ") != "y"):
        print("Cannot initialize properly client. Please check your API keys")
        return
    print("Succesfully initialize client")
    # End of initialization
    
    with telegram_client:
        telegram_client.loop.run_until_complete(get_pumped_coin())
    print("Succesfully find coin: %s" % (pumped_coin))

    pump_coins = config.coins_to_pump
    coin = config.coin

    print("I'm trying to buy %s for %f %s" % (pumped_coin, pump_coins, coin))

    buy_order = client.buy_coin(pumped_coin, coin, pump_coins)
    if buy_order is None:
        print("It's not possible to buy coins now. Try later")
        return
    (bamount, bcoin, samount, scoin) = buy_order
    print("You succesfully buyed %f %s for %f %s" % buy_order)

    stop_condition = True
    while(stop_condition):
        c = input("Sell coins?(y or n): ")
        if(c == "y"):
            c = input("Are you sure?(y or n): ")
            if c == "y":
                stop_condition = False

    sell_order = client.sell_coin(pumped_coin, coin, bamount * 0.95)
    if sell_order is None:
        print("It's impossible to sell coins")
        return
    print("You succesfully selled %f %s for %f %s" % sell_order)
        

if __name__ == "__main__":
    do_work()
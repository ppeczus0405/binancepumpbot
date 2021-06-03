from telethon import TelegramClient, events
from binanceAPI import BinanceAPI
import config
import logging
import time
logging.basicConfig(format='[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s',
                    level=logging.WARNING)

pumped_coin = None
bin_client = None
telegram_client = TelegramClient("peczi", config.telegram_api_id, config.telegram_api_hash)

# Telegram section
async def get_last_messages(chatid, n):
    l = [message.text async for message in telegram_client.iter_messages(chatid, n)]
    l.reverse()
    return l

async def get_chat_id():
    async for dialog in telegram_client.iter_dialogs():
        if dialog.name == config.telegram_chat_name:
            return dialog.id
    return None

async def is_pumped_coin_inside(message):
    global pumped_coin
    all_words = message.split(" ")
    for word in all_words:
        if '#' in word:
            position = word.find('#') + 1
            for index in range(position, len(word)):
                if not word[index].isalpha():
                    pumped_coin = word[position:index]
                    return True
    return False

async def message_handler(event):
    if await is_pumped_coin_inside(event.raw_text):
        await telegram_client.disconnect()

async def telegram_initialize():
    chatid = await get_chat_id()
    if chatid is None:
        print("Given chat name('%s') is invalid. Please verify config file" % (config.telegram_chat_name))
        return

    # Chat validation(last 3 messages)
    messages = tuple(await get_last_messages(chatid, 3))
    c = input("3.'%s'\n2.'%s'\n1.'%s'\nThat 3 messages are last in your chatbox?(y or n): " % (messages))
    if c != "y":
        print("You expect another chat than '%s'. Please verify config file" % (config.telegram_chat_name))
        return
    
    telegram_client.add_event_handler(message_handler, events.NewMessage(chats=chatid))
    print("Wating for a pump message...")
    await telegram_client.run_until_disconnected()
# End Telegram section

def binance_initialize():
    global bin_client

    print("Initializing BinanceAPI client...")
    bin_client = BinanceAPI(config.binance_api_key, config.binance_api_secret)
    print("\n".join(bin_client.get_wallet()))
    if(input("It's your wallet?(y or n): ") != "y"):
        return False
    return True

def get_pumped_coin():
    with telegram_client:
        telegram_client.loop.run_until_complete(telegram_initialize())

def do_function_and_wait(func, args):
    start = time.process_time()
    result = func(*args)
    response_time = (time.process_time() - start) * 1000
    if response_time < config.request_time:
        time.sleep(config.request_time - response_time)
    return result

def pump():
    print("Pumped coin: %s" % (pumped_coin))
    print("Let's pump!")
    
    # BEGIN buying coin
    buy_args = [pumped_coin, config.coins_to_pump, config.coin]
    pump_buy = bin_client.buy_coin_for(*buy_args)
    while type(pump_buy) != tuple:
        print(pump_buy) 
        pump_buy = do_function_and_wait(bin_client.buy_coin_for, buy_args)
    print("Succesfully buyed %f %s for %f %s" % pump_buy)
    # END buying coin

    # Limit sell coin with expected profit
    price = pump_buy[2] / pump_buy[0]
    lsell_args = [pumped_coin, pump_buy[0], config.coin, price * (1.0 + config.expected_profit / 100.0)]
    pump_lsell = bin_client.limit_sell(*lsell_args)
    while pump_lsell != True:
        print(pump_lsell)
        pump_lsell = do_function_and_wait(bin_client.limit_sell, lsell_args)
    print("Succesfully placed limit sell with %f%% profit" % (config.expected_profit))
    # END limit sell

    # Panic sell
    want_to_sell = False
    symbol = bin_client.get_symbol(pumped_coin, config.coin)
    profit = lambda x : x - price if symbol == pumped_coin + config.coin else (1.0 / x) - price
    while not want_to_sell:
        actual_profit = profit(bin_client.get_price(symbol)) * 100
        inp = input("Actual profit: %f%%. Confirm 's' to sell: " % (actual_profit))
        if inp == 's':
            want_to_sell = True
    bin_client.cancel_all_open_orders(pumped_coin, config.coin)
    remaining_ammount = bin_client.get_coin_amount(pumped_coin)
    panic_sell_args = [pumped_coin, remaining_ammount, config.coin]
    panic_sell = bin_client.sell_coin(*panic_sell_args)
    while type(panic_sell) != tuple:
        print(panic_sell)
        panic_sell = do_function_and_wait(bin_client.sell_coin, panic_sell_args)
    result_tuple = (panic_sell[2], panic_sell[3], panic_sell[0], panic_sell[1])
    print("Succesfully selled %f %s for %f %s" % result_tuple)

if __name__ == "__main__":
    if(binance_initialize()):
        print("Succesfully initialize binance client")
        get_pumped_coin()
        if pumped_coin is not None:
            pump()
    else:
        print("Cannot initialize properly client. Please check your API keys")
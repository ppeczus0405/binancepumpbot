from telethon import TelegramClient, events
from binanceAPI import BinanceAPI, OrderSide
import config
import random
import logging
import _thread
logging.basicConfig(format='[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s',
                    level=logging.WARNING)

panic_sell_flag = True
pumped_coin = None
symbol = None
bin_client = None
base_coin_amount = 0.0
pump_candidates = frozenset()
telegram_client = TelegramClient("peczi", config.telegram_api_id, config.telegram_api_hash)


# Telegram section
async def get_last_messages(chat_id, n):
    message_list = [message.text async for message in telegram_client.iter_messages(chat_id, n)]
    message_list.reverse()
    return message_list


async def get_chat_id():
    async for dialog in telegram_client.iter_dialogs():
        if dialog.name == config.telegram_chat_name:
            return dialog.id
    return None


async def is_pumped_coin_inside(message):
    global pumped_coin
    global symbol
    all_words = message.split(" ")
    for word in all_words:
        if '#' in word:
            position = word.find('#') + 1
            end = position
            while end < len(word):
                if not word[end].isalnum():
                    break
                end = end + 1
            potential_candidate = word[position:end].upper()
            potential_symbol = potential_candidate + config.coin
            if potential_symbol in pump_candidates:
                symbol = potential_symbol
                pumped_coin = potential_candidate
                return True
    return False


async def message_handler(event):
    if await is_pumped_coin_inside(event.raw_text):
        await telegram_client.disconnect()


async def telegram_initialize():
    chat_id = await get_chat_id()
    if chat_id is None:
        print("Given chat name('%s') is invalid. Please verify config file" % config.telegram_chat_name)
        return

    # Chat validation(last 3 messages)
    messages = tuple(await get_last_messages(chat_id, 3))
    c = input("3.'%s'\n2.'%s'\n1.'%s'\nThat 3 messages are last in your chatbox?(y or n): " % messages)
    if c != "y":
        print("You expect another chat than '%s'. Please verify config file" % config.telegram_chat_name)
        return
    
    telegram_client.add_event_handler(message_handler, events.NewMessage(chats=chat_id))
    print("Wating for a pump message...")
    await telegram_client.run_until_disconnected()
# End Telegram section


def placing_order_test():
    print("### Testing placing orders ###")
    test_asset = input("Give asset name to test placing orders: ")
    symbol_associated_with_asset = list(filter(lambda x: x.find(test_asset) != -1,
                                               list(BinanceAPI.COINS_SYMBOLS)))
    if not symbol_associated_with_asset:
        return False, "There is no associated symbol with given asset listed on Binance"
    test_limit_symbol = random.choice(symbol_associated_with_asset)
    print("I'm trying to place limit order on symbol # %s #" % test_limit_symbol)
    test_asset_amount = bin_client.get_coin_amount(test_asset) * 0.95
    test_limit_price = bin_client.get_symbol_price(test_limit_symbol) * 0.95
    test_limit_size = test_asset_amount / test_limit_price
    side = OrderSide.BUY
    if test_limit_symbol.find(test_asset) == 0:
        side = OrderSide.SELL
        test_limit_price *= 1.1
        test_limit_size = test_asset_amount
    test_order = bin_client.create_limit_order(test_limit_symbol, side, test_limit_size, test_limit_price)
    if type(test_order) is not int:
        return False, test_order
    check = input("Test limit order placed. Are you ready for pump? (y or n): ")
    bin_client.delete_order(test_limit_symbol, test_order)
    if check != 'y':
        return False, "User is not ready to pump"
    return True


def binance_initialize():
    global bin_client
    global base_coin_amount
    global pump_candidates

    print("Initializing BinanceAPI client...")
    print("Your wallet: ")
    bin_client = BinanceAPI(config.binance_header, timeout=4, verify=True)
    candidates = list()
    for symbol in BinanceAPI.COINS_SYMBOLS:
        if symbol.find(config.coin) != -1:
            candidates.append(symbol)
    pump_candidates = frozenset(candidates)
    wallet = bin_client.get_account_overview()
    for asset in wallet:
        print("%s: %f" % (asset, wallet[asset]))
    order_validation = placing_order_test()
    while order_validation is not True:
        print("---> %s <---" % order_validation[1])
        if order_validation[1] == "User is not ready to pump":
            return False
        order_validation = placing_order_test()
    final_check = input("Do you want pump for %f %s with %f%% profit? (y or n): " % (config.coins_to_pump, config.coin,
                                                                                     config.expected_profit))
    if final_check != 'y':
        print("User is not ready to pump")
        return False
    base_coin_amount = bin_client.get_coin_amount(config.coin) * 0.99
    if base_coin_amount < config.coins_to_pump:
        print("You have %f %s. It is less than you intended for pump" % (base_coin_amount, config.coin))
        return False
    print("You are well prepared to pump. Let's go!")
    return True


def get_pumped_coin():
    with telegram_client:
        telegram_client.loop.run_until_complete(telegram_initialize())


def get_panic_sell_start_signal():
    global panic_sell_flag
    input("Press ENTER to start panic selling coins.\n")
    panic_sell_flag = False


def panic_sell_signal_manually(profit, symbol):
    want_to_sell = False
    while not want_to_sell:
        actual_profit = profit(bin_client.get_price(symbol)) 
        inp = input("Actual profit: %f%%. Confirm 's' to sell: " % actual_profit)
        if inp == 's':
            want_to_sell = True


def pump():
    market_buy = bin_client.create_market_order(symbol, OrderSide.BUY, funds=config.coins_to_pump)
    if type(market_buy) is not tuple:
        print("Failed during trying market buy. Error message: %s" % market_buy)
        return False

    bought_coins, sold_coins = market_buy
    bought_coins *= 0.99
    sold_coins *= 0.99
    print("Successfully bought %f %s for %f %s" % (bought_coins, pumped_coin,
                                                   sold_coins, config.coin))

    # Limit sell coins
    price = sold_coins / bought_coins
    limit_price = price * (1 + config.expected_profit / 100.0)
    print("I'm trying to place limit sell order")
    limit_sell = bin_client.create_limit_order(symbol, OrderSide.SELL, bought_coins, limit_price)
    if type(limit_sell) is int:
        print("Successfully placed limit sell with %f%% profit" % config.expected_profit)
    else:
        print("Failed during trying place limit sell. Error message: %s" % limit_sell)

    def profit(x):
        return (x - price) * 100 / price

    # Multithreading for upgrade panic sell
    try:
        _thread.start_new_thread(get_panic_sell_start_signal, tuple())
        while panic_sell_flag:
            print("Actual profit: %f%%." % profit(bin_client.get_symbol_price(symbol)))
    except Exception:
        print("Unable to start new thread.")
        panic_sell_signal_manually(profit)

    # Cancel all orders on pair
    print("Canceling limit order")
    bin_client.delete_order(symbol, limit_sell)

    # Market sell coins
    print("I'm trying to sell remaining amount of coins")
    market_sell_amount = bin_client.get_coin_amount(pumped_coin) * 0.99
    market_sell = bin_client.create_market_order(symbol, OrderSide.SELL, size=market_sell_amount)
    while type(market_sell) is not tuple:
        market_sell_amount = bin_client.get_coin_amount(pumped_coin) * 0.99
        market_sell = bin_client.create_market_order(symbol, OrderSide.SELL, size=market_sell_amount)

    print("Successfully ended pump")
    return True


if __name__ == "__main__":
    if binance_initialize():
        get_pumped_coin()
        pump()
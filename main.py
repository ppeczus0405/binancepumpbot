from telethon import TelegramClient
from binanceAPI import BinanceAPI
import config
import time

pumped_coin = None
bin_client = None
telegram_client = TelegramClient("peczi", config.telegram_api_id, config.telegram_api_hash)

# Telegram section

async def get_last_messages(chatid, n):
    l = [message.text async for message in telegram_client.iter_messages(chatid, n)]
    return l

async def get_chat_id():
    async for dialog in telegram_client.iter_dialogs():
        if dialog.name == config.telegram_chat_name:
            return dialog.id
    return None

async def searching_pumped_coin():
    global pumped_coin

    # Finding chat id
    chatid = await get_chat_id()
    if chatid is None:
        print("Given chat name('%s') is invalid. Please verify config file" % (config.telegram_chat_name))
        return

    # Chat validation(last 3 messages)
    messages = tuple(await get_last_messages(chatid, 3))
    c = input("1.'%s'\n2.'%s'\n3.'%s'\nThat 3 messages are last in your chatbox?(y or n): " % (messages))
    if c != "y":
        print("Given chat name('%s') is invalid. Please verify config file" % (config.telegram_chat_name))
        return

    # Searching coin name in last message in chat
    i = 0
    while pumped_coin is None:
        print("Looking for coin name(%d) ..." % (i))
        # Get last message and divide into words
        message = (await get_last_messages(chatid, 1))[0]
        all_words = message.split(" ")
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
        telegram_client.loop.run_until_complete(searching_pumped_coin())

def pump():
    pass

if __name__ == "__main__":
    if(binance_initialize()):
        print("Succesfully initialize binance client")
        get_pumped_coin()
        if(pumped_coin is not None):
            print("Succesfully find pumped coin: %s" % (pumped_coin))
            pump()
    else:
        print("Cannot initialize properly client. Please check your API keys")
from telethon import TelegramClient, events
from binanceAPI import BinanceAPI
import config
import time
import logging
logging.basicConfig(format='[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s',
                    level=logging.WARNING)

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
        print("Expected another chat than '%s'. Please verify config file" % (config.telegram_chat_name))
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

def pump():
    pass

if __name__ == "__main__":
    if(binance_initialize()):
        print("Succesfully initialize binance client")
        get_pumped_coin()
        print("Pumped coin: %s" % (pumped_coin))
        print("Let's pump!")
        
        # ---- PUMP ----        
        pump()
        # ---- PUMP ----
    else:
        print("Cannot initialize properly client. Please check your API keys")
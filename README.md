It's a binance bot for earn money on pumps.

To start earn money (: you have to:
- install all dependencies: telethon, requests (for example with 'pip3 install dependency')
- generate telegram api keys and paste in config
- generate trade request header(It's working on the latest version of Mozilla Firefox, I have no idea how with other browsers):
    - Go to trade section on binance(you have to be logged in)
    - Choose any cryptocurrency you are able to buy
    - Open Web Developpers Tools and select network tab
    - Buy cryptocurrency and find request associated
    - Copy requests header and paste into config file(You have example request header in config)
- set expected profit
- before the pump message execute bot(python3 main.py)
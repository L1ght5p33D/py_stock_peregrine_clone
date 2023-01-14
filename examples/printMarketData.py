import json
import sys
import time
import math
import ccxt
import asyncio


exchange = getattr(ccxt, "coinbasepro")()

print(exchange)

# marks = exchange.fetch_markets()

marks = exchange.fetch_markets()


for market in marks:
    baseCoin = market["base"]
    minimumOfBase = market["limits"]["amount"]["min"]
    print("Base" + str(baseCoin))
    print("Min:::" + str(minimumOfBase))


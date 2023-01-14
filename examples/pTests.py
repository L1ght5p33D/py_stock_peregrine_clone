
from pprint import pprint
import asyncio
from peregrinearb import load_exchange_graph, print_profit_opportunity_for_path, bellman_ford

from peregrinearb.async_build_markets import async_get_exchanges_for_market
import asyncio

import ccxt


# loop = asyncio.get_event_loop()
# graph = loop.run_until_complete(load_exchange_graph('hitbtc'))
#
# print("bellman graph")
# print(graph)
#
# paths = bellman_ford(graph, 'BTC', unique_paths=True)
#
# print("paths")
# print(paths)
# for path in paths:
#     print("path path")
#     print(path)
#     print_profit_opportunity_for_path(graph, path)


# def getExchanges():

    # print(ccxta.exchanges)

    # exchange = getattr(ccxta, 'hitbtc')()
    #
    # print("got exchange id")
    #
    # print(exchange.id)
    #
    # print("exchnage api")
    # print(exchange.api)

exchange_id = 'binance'
# exchange_class = getattr(ccxt, exchange_id)
# exchange = exchange_class({
#     'apiKey': 'K-14dddf343a5917c8a0b5a6d26f8b5ea8909ca67c',
#     'secret': 'S-49a2aa5e5fc4c898806da7a8ffe88c8bcbf7962b',
#     'timeout': 30000,
#     'enableRateLimit': True,
# })


exchange = getattr(ccxt, exchange_id)()
# pprint(exchange.fetch_ticker("BTC/USD"))

pprint(exchange.load_markets())
# bl = exchange.fetch_balance ()

# pprint(bl)
# mks = exchange.fetch_markets()
# ob = exchange.fetch_order_book("BTC/USD")
# pprint(ob)
# pprint(exchange.describe())
# ob = exchange.fetch_ticker("BTC/USDT")
#
# pprint(ob)
# mks = exchange.load_markets()
#
# pprint(mks)
# tickers = exchange.fetch_tickers()
#
# pprint(tickers)

# getExchanges()

# async def testExchange():
#     exchange = getattr(ccxt, 'hitbtc')()
#
#     print(exchange)
#
#     print("the api enpoints")
#
#     print(exchange["api"])
#
#     await exchange.close()
#
# loop = asyncio.get_event_loop()
# graph = loop.run_until_complete(testExchange())

import requests
import ccxt
from peregrinearb import bellman_ford
import math
import networkx as nx
import time
import ccxt
import warnings

def _add_weighted_edge_to_graph_SYNC(ccxtFxTickers,  market_name: str, graph: nx.DiGraph, log=True, fee=0.0,
                                      suppress=None, ticker=None, depth=False):
    """
    :param log: If the edge weights given to the graph should be the negative logarithm of the ask and bid prices. This
    is necessary to calculate arbitrage opportunities.

    :param suppress: A list or set which tells which types of warnings to not throw. Accepted elements are 'markets'.

    :param depth: If True, also adds an attribute 'depth' to each edge which represents the current volume of orders
    available at the price represented by the 'weight' attribute of each edge.

    """
    ticker = ccxtFxTickers[market_name]

    fee_scalar = 1 - fee

    try:
        ticker_bid = ticker['bid']
        ticker_ask = ticker['ask']
        if depth:
            bid_volume = ticker['bidVolume']
            ask_volume = ticker['askVolume']
    # ask and bid == None if this market is non existent.
    except TypeError:
        return

    # Exchanges give asks and bids as either 0 or None when they do not exist.
    # todo: should we account for exchanges upon which an ask exists but a bid does not (and vice versa)? Would this
    # cause bugs?
    if ticker_ask == 0 or ticker_bid == 0 or ticker_ask is None or ticker_bid is None:
        return
    try:
        base_currency, quote_currency = market_name.split('/')
    # if ccxt returns a market in incorrect format (e.g FX_BTC_JPY on BitFlyer)
    except ValueError:
        return

    if log:
        if depth:
            graph.add_edge(base_currency, quote_currency, weight=-math.log(fee_scalar * ticker_bid),
                           depth=bid_volume)
            graph.add_edge(quote_currency, base_currency, weight=-math.log(fee_scalar * 1 / ticker_ask),
                           depth=ask_volume)
        else:
            graph.add_edge(base_currency, quote_currency, weight=-math.log(fee_scalar * ticker_bid))
            graph.add_edge(quote_currency, base_currency, weight=-math.log(fee_scalar * 1 / ticker_ask))
    else:
        if depth:
            graph.add_edge(base_currency, quote_currency, weight=fee_scalar * ticker_bid, depth=bid_volume)
            graph.add_edge(quote_currency, base_currency, weight=fee_scalar * 1 / ticker_ask, depth=ask_volume)
        else:
            graph.add_edge(base_currency, quote_currency, weight=fee_scalar * ticker_bid)
            graph.add_edge(quote_currency, base_currency, weight=fee_scalar * 1 / ticker_ask)

def load_exchange_graph_SYNC(ccxtFxTickers, name=True, fees=False, suppress=None, depth=False) -> nx.DiGraph:
    """
    Returns a Networkx DiGraph populated with the current ask and bid prices for each market in graph (represented by
    edges). If depth, also adds an attribute 'depth' to each edge which represents the current volume of orders
    available at the price represented by the 'weight' attribute of each edge.
    """

    fee = 0.000

    graph = nx.DiGraph()

    tickers = ccxtFxTickers

    for market_name, ticker in tickers.items():
        _add_weighted_edge_to_graph_SYNC(tickers, market_name, graph,
                                         log=True, fee=fee, suppress=suppress, ticker=ticker, depth=depth)


    return graph

def print_profit_opportunity_for_path_withSaveVals(graph, path,  starting_amount, round_to=None, depth=False):
    if not path:
        return
    f = open("profitTestRecordFOREX.txt", "a+")
    f.write("FOREX profit opportunity\n")
    f.close()

    print("Starting with {} in {}".format(starting_amount, path[0]))

    for i in range(len(path)):
        revRate = ""
        rate = 0
        if i + 1 < len(path):
            start = path[i]
            end = path[i + 1]

            if depth:
                volume = min(starting_amount, math.exp(-graph[start][end]['depth']))
                starting_amount = math.exp(-graph[start][end]['weight']) * volume
            else:
                starting_amount *= math.exp(-graph[start][end]['weight'])

            if round_to is None:
                rate = math.exp(-graph[start][end]['weight'])
                resulting_amount = starting_amount
            else:
                rate = round(math.exp(-graph[start][end]['weight']), round_to)
                resulting_amount = round(starting_amount, round_to)

            printed_line = "{} to {} at {} = {}".format(start, end, rate, resulting_amount)

            f = open("profitTestRecord.txt", "a+")
            f.write(printed_line + "\n\n")
            f.close()

            print(printed_line)


# fxPairsList = ['EUR/USD', 'USD/JPY', 'GBP/USD', 'EUR/GBP', 'USD/CHF', 'EUR/JPY', 'EUR/CHF', 'USD/CAD', 'AUD/USD', 'GBP/JPY', 'AUD/CAD', 'AUD/CHF', 'AUD/JPY', 'AUD/NZD', 'CAD/CHF', 'CAD/JPY', 'CHF/JPY', 'EUR/AUD', 'EUR/CAD', 'EUR/NOK', 'EUR/NZD', 'GBP/CAD', 'GBP/CHF', 'NZD/JPY', 'NZD/USD', 'USD/NOK', 'USD/SEK']

# url = "https://financialmodelingprep.com/api/v3/forex"
#
# # headers = {"accept": "text/html"}
#
# r = requests.get(url)
# print(r.text)
# forexMarketsObj = r.json()
#
# forexPairsList = []
# ccxtForexTickers= {}
#
# for key, val in forexMarketsObj.items():
#     if key == "forexList":
#         print("found fl key")
#         fl = val
#
#         for fxTickerItem in fl:
#             ccxtForexTickers[fxTickerItem["ticker"]] ={
#                     "ask" : fxTickerItem["ask"],
#                     "askVolume" : 100,
#                     "average" : None,
#                     "bid" : fxTickerItem["bid"],
#             }
#
#             forexPairsList.append(fxTickerItem["ticker"])
#
# # print("list complete")
# # print(forexPairsList)
#
# for pair in fxPairsList:
#
#     pairParts = pair.split("/")
#
#     base = pairParts[0]
#     currency = pairParts[1]
#
#     id = base + currency
#
#     fxMarketItem = {
#         "active": True,
#         "base"  : base,
#         "baseId": base,
#         "id" : id,
#         "info": {
#             "commodity": base,
#             "currency" : currency,
#
#         }
#     }
#
# for pair in fxPairsList:
#
#     pairParts = pair.split("/")
#
#     base = pairParts[0]
#     currency = pairParts[1]
#
#     id = base + currency
#
#     fxMarketItem = {
#         "active": True,
#         "base"  : base,
#         "baseId": base,
#         "id" : id,
#         "info": {
#             "commodity": base,
#             "currency" : currency,
#
#         }
#     }

# FMGbaseList = ['AED', 'AFN', 'ALL', 'AMD', 'ANG', 'AOA', 'ARS', 'AUD', 'AWG', 'AZN', 'BAM', 'BBD', 'BDT', 'BGN', 'BHD', 'BIF', 'BMD', 'BND', 'BOB', 'BRL', 'BSD', 'BTN', 'BWP', 'BYR', 'BZD', 'CAD', 'CDF', 'CHF', 'CLF', 'CLP', 'CNY', 'COP', 'CRC', 'CUP', 'CVE', 'CZK', 'DJF', 'DKK', 'DOP', 'DZD', 'EGP', 'ETB', 'EUR', 'FJD', 'FKP', 'GBP', 'GEL', 'GHS', 'GIP', 'GMD', 'GNF', 'GTQ', 'GYD', 'HKD', 'HNL', 'HRK', 'HTG', 'HUF', 'IDR', 'ILS', 'INR', 'IQD', 'IRR', 'ISK', 'JEP', 'JMD', 'JOD', 'JPY', 'KES', 'KGS', 'KHR', 'KMF', 'KPW', 'KRW', 'KWD', 'KYD', 'KZT', 'LAK', 'LBP', 'LKR', 'LRD', 'LSL', 'LTL', 'LVL', 'LYD', 'MAD', 'MDL', 'MGA', 'MKD', 'MMK', 'MNT', 'MOP', 'MRO', 'MUR', 'MVR', 'MWK', 'MXN', 'MYR', 'MZN', 'NAD', 'NGN', 'NIO', 'NOK', 'NPR', 'NZD', 'OMR', 'PAB', 'PEN', 'PGK', 'PHP', 'PKR', 'PLN', 'PYG', 'QAR', 'RON', 'RSD', 'RUB', 'RWF', 'SAR', 'SBD', 'SCR', 'SDG', 'SEK', 'SGD', 'SHP', 'SLL', 'SOS', 'SRD', 'STD', 'SVC', 'SYP', 'SZL', 'THB', 'TJS', 'TMT', 'TND', 'TOP', 'TRY', 'TTD', 'TWD', 'TZS', 'UAH', 'UGX', 'USD', 'UYU', 'UZS', 'VEF', 'VND', 'VUV', 'WST', 'XAF', 'XCD', 'XDR', 'XOF', 'XPF', 'YER', 'ZAR', 'ZMK', 'ZWL']

FMGbaseList = ["THB","PHP","CZK","BRL","CHF","INR","ISK","HRK","PLN","NOK","USD","CNY","RUB","SEK","MYR","SGD","ILS","TRY","BGN","NZD","HKD","RON","EUR","MXN","CAD","AUD","GBP","KRW","IDR","JPY","DKK","ZAR","HUF"]

ccxtForexTickers= {}


baseIndex = 0

while baseIndex < len(FMGbaseList):


    url = f"https://api.exchangeratesapi.io/latest?base={FMGbaseList[baseIndex]}"
    r = requests.get(url)
    print(r.text)
    forexMarketObj = r.json()


    fxPairBase = ""
    for key, val in forexMarketObj.items():
        if key == "base":
            print("found base key")
            print(val)
            fxPairBase = val
        if key == "rates":
            print("found rates key")
            for fxPairCurrency, fxPairRate in val.items():
                concatPairName = fxPairBase + "/" + fxPairCurrency

                ccxtForexTickers[concatPairName] = {
                        "ask" : fxPairRate,
                        "bid" : fxPairRate,
                }


    baseIndex += 10

    time.sleep(.5)

print(ccxtForexTickers)


startCapital = 100

print("Running Bellman for FOREX  ")

graph = load_exchange_graph_SYNC(ccxtForexTickers, fees=True)
paths = bellman_ford(graph, 'USD', unique_paths=True)

for path in paths:
    print("Path :::" + str(path))
    print_profit_opportunity_for_path_withSaveVals(graph, path, startCapital)
calcPath = True




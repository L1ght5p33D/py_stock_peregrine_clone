from pprint import pprint
import json
import time
import traceback
import math
import ccxt
from peregrinearb import bellman_ford
from storedMarketData import storedMarketData
import sys
sys.path.append('../rightBTCarbBot')
from syncPeregrineMethods import load_exchange_graph_SYNC

############ ARB PROFITS SEEN ####################

    # bitfinex
    # okcoinusd    (error?) (2x prfofit)




exchangeList = ccxt.exchanges
exchangeIndex = 0
exchangeName = ""
startCoinAmount = 10

startCoinsList = []
endCoinsList = []


gMarketData = []

def buildMarksList(marks):
    markList = []
    for markItemKey, markItemVal in marks.items():
        markList.append(markItemKey)
    return markList


def print_profit_opportunity_for_path_withSaveVals(exchangeName, graph, path, round_to=None, depth=False, starting_amount=startCoinAmount):
    global startCoinsList
    global endCoinsList
    startCoinsList = []
    endCoinsList = []
    if not path:
        return

    f = open("profitTestRecord.txt", "a+")
    f.write("Profit opportunity for exchange ::: "+ str(exchangeName) +  "\n")
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

            startCoinsList.append(start)
            endCoinsList.append(end)

            marketPairUnordered = startCoinsList[-1] + "/" + endCoinsList[-1]

            if marketPairUnordered not in gMarketData:
                marketPairOrdered = endCoinsList[-1] + "/" + startCoinsList[-1]
                revRate = " reversed rate :: non confirmed pair:: order price ::: " + str(1 / rate) + " market list price ::: " + str(rate)

                if marketPairOrdered in gMarketData:
                    revRate = "reversed pair order rate ::: " + str(1 / rate) + " market list price ::: " + str(rate)

            printed_line = "{} to {} at {} = {}".format(start, end, rate, resulting_amount)

            f = open("profitTestRecord.txt", "a+")
            f.write(printed_line + revRate + "\n\n")
            f.close()


            # todo: add a round_to option for depth
            if depth:
                printed_line += " with {} of {} traded".format(volume, start)

            print(printed_line)
            print(revRate)


def calcMinBuyIn():
    global startCoinsList
    global endCoinsList
    global gMarketData
    print("calculating min buy in")
    transferIndex = 0

    allCoinsList = []

    buyMinList = []
    buyMinMax = 0

    for transferStart in startCoinsList:

        marketNamefw = startCoinsList[transferIndex] + "/" + endCoinsList[transferIndex]
        marketNamebk = endCoinsList[transferIndex] + "/" + startCoinsList[transferIndex]

        if (marketNamefw in gMarketData) and (marketNamefw not in allCoinsList) :
            allCoinsList.append(marketNamefw)

        if (marketNamebk in gMarketData) and (marketNamebk not in allCoinsList):
            allCoinsList.append(marketNamebk)


    for coinTrade in allCoinsList:
        for markItemKey, markItemVal in gMarketData.items():
            if markItemKey == coinTrade:
                minBuyPrice = markItemVal["limits"]["price"]["min"]
                minBuyCurrency = markItemVal["quote"]

                f = open("profitTestRecord.txt", "a+")
                f.write("Min buy ::: " + str(coinTrade) + " ::: " + str(minBuyPrice) + " " + str(minBuyCurrency) + "\n")
                f.close()

                print("Min buy ::: " +str(coinTrade) + " ::: " + str(minBuyPrice) + " " + str(minBuyCurrency) )


def calcNewArbOpportunity(exchange, marketData):

    nextCoinAmt = 0
    global startCoinAmount
    iteratedStartCoinAmount = startCoinAmount
    global startCoinsList
    global endCoinsList
    # global gMarketData
    global exchangeIndex

    exchangeObj = exchange.describe()
    exchangeName = exchangeObj["id"]

    saveFee = ""
    fee = 0
    transferIndex = 0

    try:
        # fee = exchange.fees['trading']['maker']
        fee = exchange.fees['trading']["taker"]
    except:
        fee = .2
    print("found fee as:::" + str(fee) + "\n")
    saveFee = fee
    if fee > 0:
        fee = - (fee)

    print("########### Transfer Start ############ \n")
    for transferStart in startCoinsList:
        print("#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~# \n")

        marketNamefw = startCoinsList[transferIndex] + "/" + endCoinsList[transferIndex]
        marketNamebk = endCoinsList[transferIndex] + "/" + startCoinsList[transferIndex]
        markList = buildMarksList(marketData)


        if marketNamefw in markList:
            fetchedOrders = exchange.fetch_order_book(marketNamefw)
            # pprint(sym)
            #use the bid for this order
            bid = fetchedOrders["bids"][0][0]
            #ask for calculating spread
            ask = fetchedOrders["asks"][0][0]
            print("Trade name " + str(marketNamefw))
            print("Bid (for order) ::: " + str(bid) + " ::: available order amount ::: " + str(fetchedOrders["bids"][0][1]))

            coinToUSD = startCoinsList[transferIndex] + "/USD"
            usdToTransferCoin = endCoinsList[transferIndex] + "/USD"
            if coinToUSD in storedMarketData[exchangeName]:
                ctUSDTick = exchange.fetch_ticker(coinToUSD)
                print(startCoinsList[transferIndex] +  " value in USD :::: " + str(ctUSDTick["ask"]))
            elif usdToTransferCoin in storedMarketData[exchangeName]:
                usdTransferTick = exchange.fetch_ticker(usdToTransferCoin)
                print(startCoinsList[transferIndex] + " value in USD :::: " + str( usdTransferTick["bid"]))

            print("second bid ::: " + str(fetchedOrders["bids"][1][0]) + " ::: amount ::: " + str(fetchedOrders["bids"][1][1]))
            print("ask ::: "+ str(ask) + "\n")
            tradeValue = ( iteratedStartCoinAmount * bid)

            nextCoinAmt = tradeValue + (fee * tradeValue)

        elif marketNamebk in markList:
            fetchedOrders = exchange.fetch_order_book(marketNamebk)
            sym = exchange.fetch_ticker(marketNamebk)
            ask = sym["ask"]
            bid = sym["bid"]
            # pprint(sym)
            print("trade  name" + str(marketNamebk))
            print("ask (for order) ::: " + str(ask) + " ::: amount ::: " + str(fetchedOrders["asks"][0][1]))
            coinToUSD = startCoinsList[transferIndex] + "/USD"
            usdToTransferCoin = endCoinsList[transferIndex] + "/USD"
            if coinToUSD in storedMarketData[exchangeName]:
                ctUSDTick = exchange.fetch_ticker(coinToUSD)
                print(startCoinsList[transferIndex] +  " value in USD :::: " + str(ctUSDTick["ask"]))
            elif usdToTransferCoin in storedMarketData[exchangeName]:
                usdTransferTick = exchange.fetch_ticker(usdToTransferCoin)
                print(startCoinsList[transferIndex] + " value in USD :::: " + str( usdTransferTick["bid"]))

            print("second ask ::: " + str(fetchedOrders["asks"][1][0]) + " ::: amount ::: " + str(fetchedOrders["asks"][1][1]))
            print("bid ::: " + str(bid) + "\n")
            tradeValue = iteratedStartCoinAmount / ask
            nextCoinAmt = tradeValue + (fee * tradeValue)
        iteratedStartCoinAmount = nextCoinAmt
        transferIndex += 1

    print("final coin amount = " + str(nextCoinAmt)+"\n\n")

    # simulateOrderFlowAndCalcProfit(exchange, "glob", "glob", "glob")

    if (nextCoinAmt > startCoinAmount):
        calcMinBuyIn()
        f = open("profitTestRecord.txt", "a+")

        f.write(str(exchange) + " is profitable\n " + " with calculated fees ::: " + str(saveFee) + "\n")
        f.write(" starting value::: " + str(startCoinAmount) + " ending value ::: " + str(nextCoinAmt) + "\n\n")
        f.close()
        try:
            exchange.close()
        except:
            pass
        return True
    else:
        print("next coin not greater")
        try:
            exchange.close()
        except:
            pass
        return False




def testProfitabilityOfExchanges(exchanges, useAuth, authKey, authSec):
    global gMarketData
    global exchangeIndex
    global startCoinAmount
    global exchangeName
    exchange = ""

    loadMarketsList = ""
    startCoinAmount = 10
    global startCoinsList
    startCoinsList = []
    global endCoinsList
    endCoinsList = []


    print("staring prof test")
    loadExc = False

    if exchanges == "all":
        exchangeName = exchangeList[exchangeIndex]
        exchange = getattr(ccxt, exchangeName)()
        try:
            loadMarketsList = storedMarketData[exchangeName]
            gMarketData = loadMarketsList
            loadExc = True
        except:
            print(" exchange loading encountered some error")

    else:
        exchangeName = exchanges
        if useAuth == True:
            exchange_id = exchanges
            exchange_class = getattr(ccxt, exchange_id)
            exchange = exchange_class({
                'apiKey': authKey,
                'secret': authSec,
                'timeout': 30000,
                'enableRateLimit': True,
            })
            loadMarketsList = storedMarketData[exchangeName]
            gMarketData = loadMarketsList
            loadExc = True
        else:
            exchangeName = exchanges
            exchange = getattr(ccxt, exchangeName)()
            loadMarketsList = storedMarketData[exchangeName]
            gMarketData = loadMarketsList
            loadExc = True


    calcPath=False

    if loadExc == True:
        try:
            print("Running Bellman for exchange ::: " + str(exchangeName))

            graph = load_exchange_graph_SYNC(exchange= exchange, name=False, fees=True, depth = True)

            paths = bellman_ford(graph, 'BTC', unique_paths=True, ensure_profit=True)

            opp = False
            for path in paths:
                opp = True
                startCoinsList = []
                endCoinsList = []

                print("Exchange ::: " + exchangeName)
                print("Path ::: " + str(path))
                print_profit_opportunity_for_path_withSaveVals(exchangeName, graph, path)

                print(" ############ Arbitrage Analysis #############")

                calcNewArbOpportunity(exchange, loadMarketsList)
                try:
                    exchange.close()
                except:
                    print("no close method")

                if exchanges == "all":
                    exchangeIndex += 1
                    testProfitabilityOfExchanges("all")
                    try:
                        exchange.close()
                    except:
                        print("no close method")
            if opp is False:
                print("no arbitrage found")

        except:
            errTrace = traceback.format_exc()
            print("error ::: " + str(errTrace))






testProfitabilityOfExchanges("binance", False, None, None)


# testProfitabilityOfExchanges("rightbtc", False, None, None)
# testProfitabilityOfExchanges("exmo",
#                              True,
# 'K-14dddf343a5917c8a0b5a6d26f8b5ea8909ca67c',
# 'S-49a2aa5e5fc4c898806da7a8ffe88c8bcbf7962b'
#                              )




# def simulateOrderFlowAndCalcProfit(exchange,startl, endl, gmarket):
#     global startCoinsList
#     global endCoinsList
#     global gMarketData
#
#     if startl != "glob":
#         startCoinsList = startl
#     if endl != "glob":
#         endCoinsList = endl
#     if gmarket != "glob":
#         gMarketData = storedMarketData["exmo"]
#
#     startDollars = 100
#
#     iteratedAmount = startDollars
#
#     transferIndex = 0
#
#
#
#     if endCoinsList[len(startCoinsList)-1] != "USD":
#         endCoinsList.append("USD")
#
#     if (startCoinsList[0] != "USD"):
#         startCoinsList.insert(0, "USD")
#
#     fee = exchange.fees['trading']['taker']
#     if fee > 0:
#         fee = - (fee)
#
#     while transferIndex < len(startCoinsList):
#         print("while loop iter 1")
#         marketNamefw = startCoinsList[transferIndex] + "/" + endCoinsList[transferIndex]
#         marketNamebk = endCoinsList[transferIndex] + "/" + startCoinsList[transferIndex]
#
#         if marketNamefw in gMarketData:
#             print("primary forward trade")
#             tick = exchange.fetch_ticker(marketNamefw)
#             bid = tick["bid"]
#             print("simulate bid fw :: " + str(bid))
#             tradeValue = (iteratedAmount * bid)
#
#             nextCoinAmt = (tradeValue ) + (fee * tradeValue)
#             iteratedAmount = nextCoinAmt
#             print("prim fw iter")
#             print(iteratedAmount)
#             transferIndex += 1
#
#         if marketNamebk in gMarketData:
#             print("primary backwards trade")
#             tick = exchange.fetch_ticker(marketNamebk)
#             ask = tick["ask"]
#             print("simulate ask :: " + str(ask))
#             tradeValue = (iteratedAmount / ask)
#             nextCoinAmt = (tradeValue ) + (fee * tradeValue)
#             iteratedAmount = nextCoinAmt
#             print("prim bk iter")
#             print(iteratedAmount)
#             transferIndex += 1
#
#         if (marketNamebk not in gMarketData) and (marketNamefw not in gMarketData):
#             print("found a graph error? no market for transfer")
#
#             usdAsFiat = startCoinsList[transferIndex] + "/USD"
#             fiatToNextTransfer = endCoinsList[transferIndex] + "/USD"
#
#             if (usdAsFiat in gMarketData) or (fiatToNextTransfer in gMarketData):
#                 tick = exchange.fetch_ticker(usdAsFiat)
#                 bid = tick["bid"]
#                 print("simulate bid :: " + str(bid))
#                 tradeValue = (iteratedAmount * bid)
#                 nextCoinAmt = (tradeValue) + (fee * tradeValue)
#                 iteratedAmount = nextCoinAmt
#                 print("fiat convert iter")
#                 print(iteratedAmount)
#
#
#                 if fiatToNextTransfer in gMarketData:
#                     tick = exchange.fetch_ticker(fiatToNextTransfer)
#                     ask = tick["ask"]
#
#                     print("simulate ask :: " + str(ask))
#
#                     tradeValue = (iteratedAmount / ask)
#
#                     nextCoinAmt = (tradeValue) + (fee * tradeValue)
#
#                     iteratedAmount = nextCoinAmt
#                     print("fiat reverse iter")
#                     print(iteratedAmount)
#
#                     transferIndex += 1
#             else:
#                 print("Fatal error 1 no usd to fiat")
#                 break
#
#
#
#     print("Final simulated Calculated amounts :::")
#     print(iteratedAmount)


# stc = ["USD", "BTC", "ZEC"]
# endc = ["BTC", "ZEC", "USD"]
# simulateOrderFlowAndCalcProfit(getattr(ccxt, "okcoinusd")(),stc, endc, "local")
# testChain = ['EOS', 'PTI', 'BTC', 'EOS']
# # # testChain = ['BTC', 'ETZ', 'USDT', 'XRP', 'BTC']
# testExchange = "exmo"
#
# def calcChainProfit(exchangeName, chain):
#     global startCoinsList
#     global endCoinsList
#
#     startCoins = []
#     endCoins = []
#
#     transferIndex = 0
#     while transferIndex < (len(chain) - 1):
#         startCoins.append(testChain[transferIndex])
#         endCoins.append(testChain[transferIndex + 1])
#         transferIndex += 1
#
#     exchange = getattr(ccxt, exchangeName)()
#     fetchMarketList = exchange.load_markets()
#
#     startCoinsList = startCoins
#     endCoinsList = endCoins
#
#     calcNewArbOpportunity(exchange, fetchMarketList)
#
#
#
# calcChainProfit(testExchange, testChain)

# while True:
#     time.sleep(10)
#     testProfitabilityOfExchanges("okcoinusd")



# while True:
#     time.sleep(6)

#
#     chainIsProfitable = calcNewArbOpportunity()
#
#     if chainIsProfitable:
#         print("rebuy")
#
#     else:
#         break



# symbolsList = []
# orderbook1 = ""
#
#
# print(marks)
#
# for markItem in marks:
#     symbolsList.append(markItem['symbol'])
#
#     orderbook1 = exchange.fetch_order_book('BTC')
#
#     bid = orderbook1['bids'][0][0] if len(orderbook1['bids']) > 0 else None
#
#     ask = orderbook1['asks'][0][0] if len(orderbook1['asks']) > 0 else None
#     print("###################BIDS###########################")
#     print(bid)
#     print("################ASKS##############################")
#     print(ask)
#
#     print("#################TICKER###########################")
#     sym = exchange.fetch_ticker('BTC')
#     print(sym)
#     break
#
# print(orderbook1)
#
# def checkCurrentOrdersForSymbol(symb):




# # def getCoinPrices(coinArgList):
# #
# #     for coin in coinArgList:
# #         exchange = getattr(ccxt, coin)()
# #         orderbook = exchange.fetch_order_book(exchange.symbols[0])
# #         print("###################BIDS###########################")
# #         print(orderbook['bids'])
# #         print("################ASKS##############################")
# #         print(orderbook['asks'])
# #
# #         # bid = orderbook['bids'][0][0] if len(orderbook['bids']) > 0 else None
# #         # ask = orderbook['asks'][0][0] if len(orderbook['asks']) > 0 else None
# #         # spread = (ask - bid) if (bid and ask) else None
# #         # print(exchange.id, 'market price', {'bid': bid, 'ask': ask, 'spread': spread})
# #         # startCoinPrice =
# #
# #
# # testList = []
# # testList.append(startCoin)
# #
# # def runArbProfitTest(testlist):
# #     getCoinPrices(testlist)
# #
# # runArbProfitTest(testList)

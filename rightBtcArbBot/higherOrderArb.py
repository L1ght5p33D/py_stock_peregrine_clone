from pprint import pprint
import json
import time
import traceback
import math
import ccxt
from peregrinearb import bellman_ford

import sys

sys.path.append('../rightBTCarbBot')
from syncPeregrineMethods import load_exchange_graph_SYNC

exchangeList = ccxt.exchanges

testChain = ['BTC', 'OOT', 'ETH', 'BTC']

startCoinsList = []
endCoinsList = []

exchangeName = "rightbtc"

startCoinAmount = 10

exchange = getattr(ccxt, exchangeName)()

gMarketData = []

# a map of (key) the trade that needs higher orders and (val) how many orders to add
higherOrderTransfers = {}
runSecondOrderArbitrage = False


def buildMarksList(marks):
    markList = []
    for markItemKey, markItemVal in marks.items():
        markList.append(markItemKey)
    return markList


def calcMinBuyInForChain():
    global runSecondOrderArbitrage
    global higherOrderTransfers
    global startCoinsList
    global endCoinsList
    global gMarketData

    transferIndex = 0
    allTradesList = []
    revList = []
    minBuyUSD = 0
    highestBidMin = 0
    availableOrderAmount = float("inf")

    print("calculating min buy in")

    for transferStart in startCoinsList:
        marketNamefw = startCoinsList[transferIndex] + "/" + endCoinsList[transferIndex]
        marketNamebk = endCoinsList[transferIndex] + "/" + startCoinsList[transferIndex]

        if (marketNamefw in gMarketData) and (marketNamefw not in allTradesList):
            allTradesList.append(marketNamefw)
        if (marketNamebk in gMarketData) and (marketNamebk not in allTradesList):
            allTradesList.append(marketNamebk)
            revList.append(marketNamebk)
        transferIndex += 1

    volumeIsAdequate = True
    for coinTrade in allTradesList:
        print(coinTrade)
        fetchedOrders = exchange.fetch_order_book(coinTrade)
        for markItemKey, markItemVal in gMarketData.items():
            if markItemKey == coinTrade:
                minBuyAmount = markItemVal["limits"]["amount"]["min"]
                tradeSplit = coinTrade.split("/")
                try:
                    fiatToUSD = tradeSplit[0] + "/USDT"
                    if fiatToUSD in gMarketData:
                        currTicker = exchange.fetch_ticker(fiatToUSD)
                        minBuyUSD = minBuyAmount * currTicker["bid"]
                        print("min buy in usdt :::: " + str(minBuyUSD))

                        if minBuyUSD > highestBidMin:
                            highestBidMin = minBuyUSD

                except:
                    print("min Fiat is not available to convert to USDT")

                orderUsesAsk = True

                if coinTrade in revList:
                    # going to do a buy
                    availableOrderAmount = fetchedOrders["asks"][0][1]

                else:
                    # going to do a sell
                    availableOrderAmount = fetchedOrders["bids"][0][1]
                    orderUsesAsk = False

                if (availableOrderAmount) < minBuyAmount:
                    print("Transfer is NOT SUIABLE for arbitrage. BID VOLUME TOO LOW")

                    orderIndex = 1
                    cumulativeAmount = availableOrderAmount

                    while cumulativeAmount < minBuyAmount:
                        if orderUsesAsk == True:
                            cumulativeAmount += fetchedOrders["asks"][orderIndex][1]
                        if orderUsesAsk == False:
                            cumulativeAmount += fetchedOrders["bids"][orderIndex][1]
                        orderIndex += 1

                    runSecondOrderArbitrage = True
                    # The converntion will start at  "1st order index", "second order index" means top two orders, etc.
                    higherOrderTransfers[coinTrade] = (orderIndex + 1)
                    volumeIsAdequate = False
                else:
                    print("Transfer is suitable. Bid volume is adequate")

    if volumeIsAdequate == True:
        print("highest min buy in USDT ::: " + str(minBuyUSD))
        f = open("profitTestRecord.txt", "a+")
        f.write("Highest min buy in USDT for chain ::: " + str(minBuyUSD) + "\n")
        f.close()
    else:
        print("Chain is NOT SUITABLE. Volume is TOO LOW")
        f = open("profitTestRecord.txt", "a+")
        f.write("Chain is NOT SUITABLE. Volume is TOO LOW\n")
        f.close()


def calcMaxBuyInForChain():
    global startCoinsList
    global endCoinsList
    global gMarketData

    transferIndex = 0

    allTradesList = []
    lowestMaxBuyUSD = float("inf")
    revList = []

    print("calculating max buy in")

    for transferStart in startCoinsList:

        marketNamefw = startCoinsList[transferIndex] + "/" + endCoinsList[transferIndex]
        marketNamebk = endCoinsList[transferIndex] + "/" + startCoinsList[transferIndex]

        if (marketNamefw in gMarketData) and (marketNamefw not in allTradesList):
            allTradesList.append(marketNamefw)

        if (marketNamebk in gMarketData) and (marketNamebk not in allTradesList):
            allTradesList.append(marketNamebk)
            revList.append(marketNamebk)
        transferIndex += 1

    transferIndex = 0

    for coinTrade in allTradesList:
        print(coinTrade)
        for markItemKey, markItemVal in gMarketData.items():
            if markItemKey == coinTrade:
                fetchedOrders = exchange.fetch_order_book(coinTrade)
                tradeSplit = coinTrade.split("/")

                if coinTrade in revList:
                    # going to do a buy
                    maxOrder = fetchedOrders["asks"][0][0] * fetchedOrders["asks"][0][1]
                    print("max order buy in fiat :::")
                    print(maxOrder)

                else:
                    # going to do a sell
                    maxOrder = fetchedOrders["bids"][0][0] * fetchedOrders["bids"][0][1]
                    print("max order sell in fiat :::")
                    print(maxOrder)

                try:
                    fiatToUSD = tradeSplit[0] + "/USDT"

                    if fiatToUSD in gMarketData:
                        currTicker = exchange.fetch_ticker(fiatToUSD)
                        # multiply the volume amount of the current highest bid for the coin by the ask price to convert it to USD
                        maxBuyUSD = fetchedOrders["bids"][0][1] * currTicker["ask"]
                        if maxBuyUSD < lowestMaxBuyUSD:
                            lowestMaxBuyUSD = maxBuyUSD
                        print(fiatToUSD + " ::: max trade in usdt :::: " + str(maxBuyUSD))
                except:
                    try:
                        fiatToUSD = tradeSplit[1] + "/USDT"

                        if fiatToUSD in gMarketData:
                            currTicker = exchange.fetch_ticker(fiatToUSD)
                            # multiply the volume amount of the current highest bid for the coin by the ask price to convert it to USD
                            maxBuyUSD = fetchedOrders["bids"][0][1] * currTicker["ask"]

                            if maxBuyUSD < lowestMaxBuyUSD:
                                lowestMaxBuyUSD = maxBuyUSD

                            print(fiatToUSD + " ::: max trade in usdt :::: " + str(maxBuyUSD))
                    except:
                        print("max Fiat is not available to convert to USDT")

            transferIndex += 1

    f = open("profitTestRecord.txt", "a+")
    f.write("Lowest max buy in USDT for transfer chain ::: " + str(lowestMaxBuyUSD) + "\n")
    f.close()


def calculateArbitraryOrderProfit(transferName, bidOrAsk, orderBook, prevCoinAmount):
    global exchange

    iteratedStartCoinAmount = prevCoinAmount
    nextCoinAmt = 0

    exchangeObj = exchange.describe()
    fee = 0
    transferIndex = 0

    try:
        # fee = exchange.fees['trading']['maker']
        fee = exchange.fees['trading']["taker"]
    except:
        fee = .2
    if fee > 0:
        fee = - (fee)

    arbOrder = 1

    while arbOrder <= higherOrderTransfers[transferName]:

        fetchedOrders = orderBook

        bid = fetchedOrders["bids"][arbOrder - 1][0]
        ask = fetchedOrders["asks"][arbOrder - 1][0]

        if bidOrAsk == "bid":
            tradeValue = (iteratedStartCoinAmount * bid)

            print("ORDER" + f"[{arbOrder}]" + "trade name " + str(transferName))
            print("ORDER" + f"[{arbOrder}]" + "bid (for order) ::: " + str(bid) + " ::: amount ::: " + str(
                fetchedOrders["bids"][arbOrder - 1][1]))
            print("ORDER" + f"[{arbOrder}]" + "iter coin amt :: " + str(iteratedStartCoinAmount))
            nextCoinAmt = (tradeValue) + (fee * tradeValue)
            iteratedStartCoinAmount = nextCoinAmt

        elif bidOrAsk == "ask":
            tradeValue = iteratedStartCoinAmount / (ask)
            print("ORDER" + f"[{arbOrder}]" + "trade  name" + str(transferName))
            print("ORDER" + f"[{arbOrder}]" + "ask (for order) ::: " + str(ask) + " ::: amount ::: " + str(
                fetchedOrders["asks"][arbOrder - 1][1]))
            print("ORDER" + f"[{arbOrder}]" + "iter coin amt :: " + str(iteratedStartCoinAmount))
            nextCoinAmt = (tradeValue) + (fee * tradeValue)
            iteratedStartCoinAmount = nextCoinAmt

        arbOrder += 1

        print("ORDER" + f"[{arbOrder}]" + "final coin amount = " + str(nextCoinAmt) + "\n\n")

        return nextCoinAmt


def calcNewArbOpportunity(marketData):
    nextCoinAmt = 0
    global startCoinAmount
    iteratedStartCoinAmount = startCoinAmount
    global startCoinsList
    global endCoinsList
    global exchange

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
    print("found fee as:::" + str(fee))
    saveFee = fee
    if fee > 0:
        fee = - (fee)

    calcMinBuyInForChain()
    calcMaxBuyInForChain()

    while transferIndex < len(startCoinsList):
        print("transfer start")

        marketNamefw = startCoinsList[transferIndex] + "/" + endCoinsList[transferIndex]
        marketNamebk = endCoinsList[transferIndex] + "/" + startCoinsList[transferIndex]

        markList = buildMarksList(marketData)

        if marketNamefw in markList:

            fetchedOrders = exchange.fetch_order_book(marketNamefw)
            # pprint(sym)
            # use the bid for this order
            bid = fetchedOrders["bids"][0][0]
            # ask for calculating spread
            ask = fetchedOrders["asks"][0][0]
            print("trade name " + str(marketNamefw))
            print("bid (for order) ::: " + str(bid) + " ::: amount ::: " + str(fetchedOrders["bids"][0][1]))
            print("second bid ::: " + str(fetchedOrders["bids"][1][0]) + " ::: amount ::: " + str(
                fetchedOrders["bids"][1][1]))
            print("ask ::: " + str(ask) + "\n")
            print("iter coin amt :: " + str(iteratedStartCoinAmount))
            tradeValue = (iteratedStartCoinAmount * bid)
            print("trade value bid ::: " + str(tradeValue))

            if marketNamefw in higherOrderTransfers:
                print(" entering higher order transfer calculation ")
                nextCoinAmt = calculateArbitraryOrderProfit(marketNamefw, "bid", fetchedOrders, nextCoinAmt)
            else:
                nextCoinAmt = (tradeValue) + (fee * tradeValue)
                print("next coin bid :: " + str(nextCoinAmt))



        elif marketNamebk in markList:
            # sym = exchange.fetch_ticker(marketNamebk)
            # ask = sym["ask"]
            # bid = sym["bid"]
            # pprint(sym)
            fetchedOrders = exchange.fetch_order_book(marketNamebk)
            bid = fetchedOrders["bids"][0][0]
            ask = fetchedOrders["asks"][0][0]
            print("trade  name" + str(marketNamebk))
            print("ask (for order) ::: " + str(ask) + " ::: amount ::: " + str(fetchedOrders["asks"][0][1]))
            print("second ask ::: " + str(fetchedOrders["asks"][1][0]) + " ::: amount ::: " + str(
                fetchedOrders["asks"][1][1]))
            print("bid ::: " + str(bid) + "\n")
            tradeValue = iteratedStartCoinAmount / (ask)
            print("trade value ask ::: " + str(tradeValue))

            if marketNamebk in higherOrderTransfers:
                nextCoinAmt = calculateArbitraryOrderProfit(marketNamebk, "ask", fetchedOrders, nextCoinAmt)
            else:
                nextCoinAmt = (tradeValue) + (fee * tradeValue)
                print("next coin ask :: " + str(nextCoinAmt))

        iteratedStartCoinAmount = nextCoinAmt
        print("amount of fiat at this step of chain ::: " + str(nextCoinAmt))
        transferIndex += 1

    print("final coin amount = " + str(nextCoinAmt) + "\n\n")

    if (nextCoinAmt > startCoinAmount):

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
        f = open("profitTestRecord.txt", "a+")

        f.write("Chain is NOT profitable\n")
        f.write(" starting value::: " + str(startCoinAmount) + " ending value ::: " + str(nextCoinAmt) + "\n\n")
        f.close()

        try:
            exchange.close()
        except:
            pass
        return False


def calcChainProfit(exchangeName, chain):
    global gMarketData
    global startCoinsList
    global endCoinsList

    startCoins = []
    endCoins = []

    transferIndex = 0
    while transferIndex < (len(chain) - 1):
        startCoins.append(testChain[transferIndex])
        endCoins.append(testChain[transferIndex + 1])
        transferIndex += 1
    startCoinsList = startCoins
    endCoinsList = endCoins

    print("coins lists")
    print(startCoinsList)
    print(endCoinsList)


    exchange = getattr(ccxt, exchangeName)()
    fetchMarketList = exchange.load_markets()
    gMarketData = fetchMarketList

    calcNewArbOpportunity(fetchMarketList)


calcChainProfit("rightbtc", testChain)
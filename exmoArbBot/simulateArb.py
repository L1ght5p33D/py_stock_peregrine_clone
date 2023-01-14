from pprint import pprint
import json
import time
import traceback
import math
import ccxt
from peregrinearb import bellman_ford

import sys
sys.path.append('../rightBTCarbBot')
sys.path.append('../examples')
from storedMarketData import storedMarketData
from syncPeregrineMethods import load_exchange_graph_SYNC


exchangeList = ccxt.exchanges



# testChain = ['BTC', 'USDT', 'ETZ', 'BTC']

# testChain = ['ETP', 'BTC', 'USD', 'XRP', 'ETP']

testChain = ['USDT', 'BTC', 'KICK', 'USDT']

transferAllCoins = False
startCoinAmount = .0001


startCoinsList = []
endCoinsList = []


gMarketData = []

exchangeName = ""

# a map of (key) the trade that needs higher orders and (val) how many orders to add
higherOrderTransfers = {}
runSecondOrderArbitrage = False


def exchangeConnect(exchangename, auth, authkey, authsec):
    global exchangeName
    global  exchange


    exchangeName = exchangename

    if auth == True:

        exchange_class = getattr(ccxt, exchangename)

        exchange = exchange_class({
            'apiKey': authkey,
            'secret': authsec,
            'timeout': 30000,
            'enableRateLimit': True,
        })
    else:
        exchange = getattr(ccxt, exchangename)






exchangeConnect("exmo",
                True,
'K-14dddf343a5917c8a0b5a6d26f8b5ea8909ca67c',
'S-49a2aa5e5fc4c898806da7a8ffe88c8bcbf7962b'
                )


# exchangeConnect("rightbtc", False, None, None)



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

        if (marketNamefw in gMarketData) and (marketNamefw not in allTradesList) :
            allTradesList.append(marketNamefw)
        if (marketNamebk in gMarketData) and (marketNamebk not in allTradesList):
            allTradesList.append(marketNamebk)
            revList.append(marketNamebk)
        transferIndex +=1



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

                if availableOrderAmount < minBuyAmount:
                    print("BID VOLUME LOW ::: require second or higher order arbitrage")

                    orderIndex = 1
                    cumulativeAmount = availableOrderAmount

                    while cumulativeAmount < minBuyAmount:
                        if orderUsesAsk == True:
                            cumulativeAmount += fetchedOrders["asks"][orderIndex][1]
                        if orderUsesAsk == False:
                            cumulativeAmount += fetchedOrders["bids"][orderIndex][1]
                        orderIndex +=1


                    runSecondOrderArbitrage = True
                    # The converntion will start at  "1st order index", "second order index" means top two orders, etc.
                    higherOrderTransfers[coinTrade] = (orderIndex + 1)
                    volumeIsAdequate = False



                else:
                    print("Transfer is suitable. Bid volume is adequate for first order arbitrage")

    if volumeIsAdequate == True:
        print("highest min buy in USDT ::: " + str(minBuyUSD) + "\n")
        f = open("profitTestRecord.txt", "a+")
        f.write("Highest min buy in USDT for chain ::: " + str(minBuyUSD) + "\n")
        f.close()
    else:
        print("Chain requires higher order arbitrage \n")
        f = open("profitTestRecord.txt", "a+")
        f.write("Chain requires higher order arbitrage\n")
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

def calculateHigherOrderTransferProfit(transferName, bidOrAsk, orderBook, prevCoinAmount):
    global exchange
    iteratedCoinAmount = prevCoinAmount
    tradeCoinAmount = 0

    exchangeObj = exchange.describe()
    fee = 0
    transferIndex = 0

    optimalTransfer = 0
    if bidOrAsk == "ask":
        optimalTransfer = prevCoinAmount / orderBook["asks"][0][0]
    if bidOrAsk == "bid":
        optimalTransfer = prevCoinAmount * orderBook["bids"][0][0]
    print("\n")
    print("Higher order transfer starting amount ::: " + str(prevCoinAmount) +
          "\n" + "equivalent if all transferred with first order ::: " + str(optimalTransfer)

                                                                               )
    try:
        # fee = exchange.fees['trading']['maker']
        fee = exchange.fees['trading']["taker"]
    except:
        fee = .2
    if fee > 0:
        fee = - (fee)

    arbOrder = 1


    convertedCoinAmount = 0


    while arbOrder <= higherOrderTransfers[transferName]:

        fetchedOrders = orderBook

        bid = fetchedOrders["bids"][arbOrder-1][0]
        ask = fetchedOrders["asks"][arbOrder-1][0]

        bidAmt = fetchedOrders["bids"][arbOrder - 1][1]
        askAmt = fetchedOrders["asks"][arbOrder -1][1]

        if bidOrAsk == "bid":

            if convertedCoinAmount + bidAmt >= prevCoinAmount:
                bidAmt = bidAmt - convertedCoinAmount

            tradeValue = bidAmt * bid

            print("ORDER"+f"[{arbOrder}]"+"trade name " + str(transferName))
            print("ORDER"+f"[{arbOrder}]"+"bid (for order) ::: " + str(bid) + " ::: amount ::: " + str(fetchedOrders["bids"][arbOrder-1][1]))
            print("ORDER"+f"[{arbOrder}]"+"iter coin amt :: " + str(iteratedCoinAmount))

            tradeCoinAmount = (tradeValue) + (fee * tradeValue)

            iteratedCoinAmount += tradeCoinAmount

            convertedCoinAmount += bidAmt


        elif bidOrAsk == "ask":

            if convertedCoinAmount + askAmt >= prevCoinAmount:
                askAmt = bidAmt - convertedCoinAmount

            tradeValue = askAmt / ask

            print("ORDER"+f"[{arbOrder}]"+"trade  name" + str(transferName))
            print("ORDER"+f"[{arbOrder}]"+"ask (for order) ::: " + str(ask) + " ::: amount ::: " + str(fetchedOrders["asks"][arbOrder-1][1]))
            print("ORDER" + f"[{arbOrder}]" + "iter coin amt :: " + str(iteratedCoinAmount))

            tradeCoinAmount = (tradeValue) + (fee * tradeValue)

            iteratedCoinAmount += tradeCoinAmount

            convertedCoinAmount += askAmt

        arbOrder +=1



    print("ORDER"+f"[{arbOrder}]"+"final coin amount = " + str(iteratedCoinAmount) + "\n\n")

    return iteratedCoinAmount



def calcNewArbOpportunity(marketData):
    global startCoinAmount
    iteratedCoinAmount = startCoinAmount
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

    for transferCoin in startCoinsList:
        print("transfer start")

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
            print("trade name " + str(marketNamefw))
            print("bid (for order) ::: " + str(bid) + " ::: amount ::: " + str(fetchedOrders["bids"][0][1]))
            print("second bid ::: " + str(fetchedOrders["bids"][1][0]) + " ::: amount ::: " + str(fetchedOrders["bids"][1][1]))
            print("ask ::: "+ str(ask) )
            print(f"amount of {startCoinsList[transferIndex]} in this step ::: " + str(iteratedCoinAmount) )
            tradeValue = ( iteratedCoinAmount * bid ) + (fee * iteratedCoinAmount)


            if iteratedCoinAmount > (fetchedOrders["bids"][0][1]):
                print(" first bid does not have adequate volume")
                orderIndex = 1
                bidVolume = 0
                while bidVolume <= iteratedCoinAmount:
                    bidVolume += fetchedOrders["bids"][orderIndex - 1][1]
                    orderIndex +=1
                higherOrderTransfers[marketNamefw] = orderIndex



            if marketNamefw in higherOrderTransfers:
                print(" entering higher order transfer calculation ")
                iteratedCoinAmount = calculateHigherOrderTransferProfit(marketNamefw, "bid", fetchedOrders, iteratedCoinAmount)
            else:
                iteratedCoinAmount = tradeValue + ( fee * tradeValue )

            print("\n")

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
            print("second ask ::: " + str(fetchedOrders["asks"][1][0]) + " ::: amount ::: " + str(fetchedOrders["asks"][1][1]))
            print("bid ::: " + str(bid))
            tradeValue = ( iteratedCoinAmount / ask ) + ( iteratedCoinAmount * fee )


            if iteratedCoinAmount > (fetchedOrders["asks"][0][1] / fetchedOrders["asks"][0][0]):
                print(" first ask does not have adequate volume")
                orderIndex = 1
                askVolume = 0
                while askVolume < iteratedCoinAmount:
                    askVolume += fetchedOrders["asks"][orderIndex - 1][1]
                    orderIndex +=1
                higherOrderTransfers[marketNamebk] = orderIndex

            if marketNamebk in higherOrderTransfers:
                iteratedStartCoinAmount = calculateHigherOrderTransferProfit(marketNamebk, "ask", fetchedOrders, iteratedCoinAmount)
            else:
                iteratedStartCoinAmount = tradeValue + ( fee * tradeValue )
            print("\n")

        transferIndex += 1

    print("final coin amount = " + str(iteratedCoinAmount)+"\n\n")


    if (iteratedCoinAmount > startCoinAmount):


        f = open("profitTestRecord.txt", "a+")

        f.write(str(exchange) + " is profitable\n " + " with calculated fees ::: " + str(saveFee) + "\n")
        f.write(" starting value::: " + str(startCoinAmount) + " ending value ::: " + str(iteratedStartCoinAmount) + "\n\n")
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
        f.write(" starting value::: " + str(startCoinAmount) + " ending value ::: " + str(iteratedStartCoinAmount) + "\n\n")
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

    print("Transfer Lists :::")
    print(startCoinsList)
    print(endCoinsList)
    print("\n")

    f = open("profitTestRecord.txt", "a+")
    f.write(f"Exmo Chain ::: {startCoinsList}, {endCoinsList} ")
    f.close()

    exchange = getattr(ccxt, exchangeName)()

    if exchangeName in storedMarketData:
        fetchMarketList = storedMarketData[exchangeName]
    else:
        fetchMarketList = exchange.load_markets()
    gMarketData = fetchMarketList

    calcNewArbOpportunity(fetchMarketList)


calcChainProfit(exchangeName, testChain)
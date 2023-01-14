
import sys
from pprint import pprint
import json
import sys
import time
import traceback

import ccxt

sys.path.append('../examples')
from testArbOpProfit import testProfitabilityOfExchanges


gMarketData = {}


def testRightBTCArb():
    testProfitabilityOfExchanges("rightbtc")


testRightBTCArb()









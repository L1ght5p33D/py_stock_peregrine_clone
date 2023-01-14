
import math
import networkx as nx
import ccxt
import warnings

def _add_weighted_edge_to_graph_SYNC(exchange: ccxt.Exchange, market_name: str, graph: nx.DiGraph, log=True, fee=0,
                                      suppress=None, ticker=None, depth=False):
    """
    Returns a Networkx DiGraph populated with the current ask and bid prices for each market in graph (represented by
    edges).
    :param exchange: A ccxt Exchange object
    :param market_name: A string representing a cryptocurrency market formatted like so:
    '{base_currency}/{quote_currency}'
    :param graph: A Networkx DiGraph upon
    :param log: If the edge weights given to the graph should be the negative logarithm of the ask and bid prices. This
    is necessary to calculate arbitrage opportunities.
    :param fee: The fee applied to the base currency represented as a decimal.
    :param suppress: A list or set which tells which types of warnings to not throw. Accepted elements are 'markets'.
    :param ticker: A dictionary representing a market as returned by ccxt's Exchange's fetch_ticker method
    :param depth: If True, also adds an attribute 'depth' to each edge which represents the current volume of orders
    available at the price represented by the 'weight' attribute of each edge.
    :return:
    """
    if ticker is None:
        try:
            ticker = exchange.fetch_ticker(market_name)
        # any error is solely because of fetch_ticker
        except:
            if 'markets' not in suppress:
                warning = 'Market {} is unavailable at this time.'.format(market_name)
                warnings.warn(warning)
            return

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


def load_exchange_graph_SYNC(exchange, name=True, fees=False, suppress=None, depth=False) -> nx.DiGraph:
    """
    Returns a Networkx DiGraph populated with the current ask and bid prices for each market in graph (represented by
    edges). If depth, also adds an attribute 'depth' to each edge which represents the current volume of orders
    available at the price represented by the 'weight' attribute of each edge.
    """
    if suppress is None:
        suppress = ['markets']
    if name:
        exchange = getattr(ccxt, exchange)()

    exchange.load_markets()

    if fees:
        if 'maker' in exchange.fees['trading']:
            # we always take the maker side because arbitrage depends on filling orders
            fee = exchange.fees['trading']['maker']
        else:
            if 'fees' not in suppress:
                warnings.warn("The fees for {} have not yet been implemented into the library. "
                              "Values will be calculated using a 0.2% maker fee.".format(exchange))
            fee = 0.002
    else:
        fee = 0

    graph = nx.DiGraph()

    try:
        tickers = exchange.fetch_tickers()
    except ccxt.errors.NotSupported:
        tickers = {exchange: None for exchange in ccxt.exchanges}

    for market_name, ticker in tickers.items():
        _add_weighted_edge_to_graph_SYNC(exchange, market_name, graph,
                                         log=True, fee=fee, suppress=suppress, ticker=ticker, depth=depth)



    return graph
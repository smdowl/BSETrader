from pylab import *
from BSE import *
from trader_aa import Marginality
from log_maker import make_logger
import json
from nose.tools import *

logger = make_logger()

class Lob:
    def __init__(self):
        self.best_bid = None
        self.best_ask = None

    def get_lob(self,time):
        # return {'bids':{'best':2},'asks':{'best':2.5}}
        lob={}
        lob['time']=time
        lob['bids']={'best':self.best_bid,
                     'worst':bse_sys_minprice,
                     'n':0,
                     'lob':[]}
        lob['asks']={'best':self.best_ask,
                     'worst':bse_sys_maxprice,
                     'n':0,
                     'lob':[]}
        return lob

def create_trader():
    trader = Trader_AA('AA','B01',0.00)
    trader.equilibrium = 3
    # trader.theta = 4
    trader.job = 'Ask'
    trader.limit = 1
    trader.p_max = 6
    trader.marginality = Marginality.Intra
    trader.transactions = [6,4]

    trader.alphas = [0.02,0.15]

    return trader

def create_test_trader_1():
    """ Create an intramarginal buyer """
    trader = Trader_AA('AA','T01',0.00)

    value = 4
    qty = 1
    time = 0
    order = Order(trader.tid, "Bid", value, qty, time)
    trader.add_order(order)

    return trader

def create_test_trader_2():
    """ Create an intramarginal ask """
    trader = Trader_AA('AA','T01',0.00)

    value = 4
    qty = 1
    time = 0
    order = Order(trader.tid, "Ask", value, qty, time)
    trader.add_order(order)

    return trader

def test_case_1():
    """ 
    Take a buyer and run a test sequence on it. 
        1. get an order with an empty lob
        2. get an order after a trader of 3
        3. respond to a change in the lob
        4. respond to another trader at 5
    """
    TraderUtils.wipe_trader_files()

    total_time = 10
    time = 0
    time_left = total_time - time

    test_lob = Lob()
    lob = test_lob.get_lob()

    trader = create_test_trader_1()

    # test trader with empty lob
    order = trader.getorder(time,time_left,lob)

    time = time+1

    trade = create_trade(time,3)
    trader.respond(time, lob, trade, True)
    print trader
    order = trader.getorder(time,time_left,lob)
    # print order

    lob['bids']['best'] = 2
    trader.respond(time, lob, None, True)
    print trader

    trade = create_trade(time,5)
    trader.respond(time, lob, trade, True)
    print trader

def plot_rs(trader):
    targets = zeros(21)
    rs = zeros(21)
    for i in range(21):
        r = -1 + float(i) / 10
        targets[i] = trader.calculate_target_price(r)
        rs[i] = r
    
    plot(rs,targets)
    plot(rs,trader.equilibrium*ones(len(rs)),'k--')

    logger.debug(lob['bids']['best'] * ones(len(rs)))

    plot(rs, lob['bids']['best'] * ones(len(rs)),'r.-')
    plot(rs, lob['asks']['best'] * ones(len(rs)),'b.-')

def create_trade(time,price):
    return {'time': time,
               'price': price,
               'party1':'T01',
               'party2':'T02',
               'qty': 1}

def add_order_to_lob(lob,time,price,trade_type,trader):
    """ Changes the best bid for the given job type. (Not dependent on whether the bid is actually better) """
    lob[trade_type]['best'] = price
    trader.respond(time, lob, None, True)

def add_trade(lob,time,price,trader):
    """ Run the sequence that would happen when there is a completed trade. The lob is not updated """
    trade = create_trade(time,price)
    trader.respond(time, lob, trade, True)

def test_add_trade():
    time = 0

    # run through the standard way first
    test_lob = Lob()
    lob = test_lob.get_lob(time)
    trader = create_test_trader_1()
    trade = create_trade(time,3)
    trader.respond(time, lob, trade, True)
    trader_str1 = str(trader)

    # run through with add_trade
    test_lob = Lob()
    lob = test_lob.get_lob(time)
    trader = create_test_trader_1()
    add_trade(lob,time,3,trader)
    trader_str2 = str(trader)

    assert_equal(trader_str1,trader_str2)

# TraderUtils.wipe_trader_files()

# total_time = 10
# time = 0
# time_left = total_time - time

# test_lob = Lob()
# lob = test_lob.get_lob()

# trader = create_test_trader_1()

# # test trader with empty lob
# order = trader.getorder(time,time_left,lob)

# time = time+1

# trade = create_trade(time,3)
# trader.respond(time, lob, trade, True)
# print trader

# order = trader.getorder(time,time_left,lob)
# # print order

# lob['bids']['best'] = 2
# trader.respond(time, lob, None, True)
# print trader

# trade = create_trade(time,5)
# trader.respond(time, lob, trade, True)
# print trader

test_add_trade()

# order = trader.getorder(time,time_left,lob)
# print order
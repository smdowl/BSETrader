from pylab import *
from BSE import *
from Trader_AA import Marginality
from log_maker import make_logger
import json

logger = make_logger()

class Lob:
    def __init__(self):
        self.best_bid = None
        self.best_ask = None

    def get_lob(self):
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

# order = trader.getorder(time,time_left,lob)
# print order




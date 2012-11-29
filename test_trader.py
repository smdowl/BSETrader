from pylab import *
from BSE import *
from Trader_AA import Marginality
from log_maker import make_logger
import json

logger = make_logger()

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

def get_lob():
    # return {'bids':{'best':2},'asks':{'best':2.5}}
    lob={}
    lob['time']=time
    lob['bids']={'best':bse_sys_minprice,
                 'worst':None,
                 'n':0,
                 'lob':[]}
    lob['asks']={'best':bse_sys_maxprice,
                 'worst':None,
                 'n':0,
                 'lob':[]}
    return lob


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

total_time = 10
time = 0
time_left = total_time - time

lob = get_lob()
trader = create_trader()

trader = create_test_trader_1()
order = trader.getorder(time,time_left,lob)

print order
# logger.debug(trader.getorder())
# trader.respond()
# logger.debug(trader)
# logger.debug("r_shout = %f" % trader.calculate_r_shout(lob))


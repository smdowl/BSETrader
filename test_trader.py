from pylab import *
from BSE import *
from Trader_AA import Marginality
from log_maker import make_logger

logger = make_logger()

def create_trader():
    trader = Trader_AA('AA','B01',0.00)
    trader.equilibrium = 3
    trader.theta = 4
    trader.job = 'Ask'
    trader.limit = 1
    trader.p_max = 6
    trader.marginality = Marginality.Extra
    trader.transactions = [6]

    trader.alphas = [0.02,0.15]

    return trader

def get_lob():
    return {'bids':{'best':2},'asks':{'best':2.5}}

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

lob = get_lob()
trader = create_trader()

logger.debug("r_shout = %f" % trader.calculate_r_shout(lob))
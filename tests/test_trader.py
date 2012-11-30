from pylab import *
import os,sys
parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0,parentdir)

from trader_aa import Trader_AA
from trader_aa import Marginality

def test_r_intramarginal():
    traders = []

    bid_trader = Trader_AA('AA','B01',0.00)
    bid_trader.equilibrium = 3
    bid_trader.job = 'Bid'
    bid_trader.limit = 4
    bid_trader.p_max = 6
    bid_trader.marginality = Marginality.Intra
    bid_trader.transactions = [6,4]
    bid_trader.alphas = [0.02,0.15]
    traders.append(bid_trader)

    ask_trader = Trader_AA('AA','A01',0.00)
    ask_trader.equilibrium = 3
    ask_trader.job = 'Ask'
    ask_trader.limit = 2
    ask_trader.p_max = 6
    ask_trader.marginality = Marginality.Intra
    ask_trader.transactions = [6,4]
    ask_trader.alphas = [0.02,0.15]
    traders.append(ask_trader)

    N = 40
    thetas = range(-1,4)
    # thetas = range(4,5)
    print thetas

    for theta in thetas:
        targets = zeros((N,2))

        rs = zeros(N)
        for i in range(N):
            r = -1 + 2 * float(i) / N
            for j in range(2):
                traders[j].theta = theta
                targets[i,j] = traders[j].calculate_target_price(r)
            rs[i] = r
       

        plot(rs,targets[:,0], 'r-')
        plot(rs,targets[:,1], 'b--')
    show()

def test_r_extramarginal():
    traders = []

    bid_trader = Trader_AA('AA','B01',0.00)
    bid_trader.equilibrium = 3
    bid_trader.job = 'Bid'
    bid_trader.limit = 2
    bid_trader.p_max = 6
    bid_trader.marginality = Marginality.Extra
    bid_trader.transactions = [6,4]
    bid_trader.alphas = [0.02,0.15]
    traders.append(bid_trader)

    ask_trader = Trader_AA('AA','A01',0.00)
    ask_trader.equilibrium = 3
    ask_trader.job = 'Ask'
    ask_trader.limit = 4
    ask_trader.p_max = 6
    ask_trader.marginality = Marginality.Extra
    ask_trader.transactions = [6,4]
    ask_trader.alphas = [0.02,0.15]
    traders.append(ask_trader)

    N = 40
    thetas = range(-1,4)
    # thetas = range(4,5)
    print thetas

    for theta in thetas:
        targets = zeros((N,2))

        rs = zeros(N)
        for i in range(N):
            r = -1 + 2 * float(i) / N
            for j in range(2):
                traders[j].theta = theta
                targets[i,j] = traders[j].calculate_target_price(r)
            rs[i] = r
       

        plot(rs,targets[:,0], 'r-')
        plot(rs,targets[:,1], 'b--')
    show()

test_r_extramarginal()
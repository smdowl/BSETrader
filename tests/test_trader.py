from pylab import *
import os,sys
parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0,parentdir)

from BSE import Trader_AA

# THETAS = range(0,2)
# THETAS = range(-2,4)
THETAS = range(-8,4)

def test_r_intramarginal():
    traders = []

    bid_trader = Trader_AA('AA','B01',0.00)
    bid_trader.equilibrium = 3
    bid_trader.job = 'Bid'
    bid_trader.limit = 4
    bid_trader.p_max = 6
    bid_trader.marginality = Trader_AA.Marginality.Intra
    bid_trader.transactions = [6,4]
    bid_trader.alphas = [0.02,0.15]
    traders.append(bid_trader)

    ask_trader = Trader_AA('AA','A01',0.00)
    ask_trader.equilibrium = 3
    ask_trader.job = 'Ask'
    ask_trader.limit = 2
    ask_trader.p_max = 6
    ask_trader.marginality = Trader_AA.Marginality.Intra
    ask_trader.transactions = [6,4]
    ask_trader.alphas = [0.02,0.15]
    traders.append(ask_trader)

    N = 40

    for theta in THETAS:
        targets = zeros((N,2))
        support = linspace(-1,1,N)

        rs = zeros(N)
        for i in range(N):
            r = support[i]
            for j in range(2):
                traders[j].theta = theta + 0.0001 
                targets[i,j] = traders[j].calculate_target_price(r)
            rs[i] = r
       

        plot(rs,targets[:,0], 'r-')
        plot(rs,targets[:,1], 'b--')

    title('Intra')
    show()

def test_r_extramarginal():
    traders = []

    bid_trader = Trader_AA('AA','B01',0.00)
    bid_trader.equilibrium = 3
    bid_trader.job = 'Bid'
    bid_trader.limit = 2
    bid_trader.p_max = 6
    bid_trader.marginality = Trader_AA.Marginality.Extra
    bid_trader.transactions = [6,4]
    bid_trader.alphas = [0.02,0.15]
    traders.append(bid_trader)

    ask_trader = Trader_AA('AA','A01',0.00)
    ask_trader.equilibrium = 3
    ask_trader.job = 'Ask'
    ask_trader.limit = 4
    ask_trader.p_max = 6
    ask_trader.marginality = Trader_AA.Marginality.Extra
    ask_trader.transactions = [6,4]
    ask_trader.alphas = [0.02,0.15]
    traders.append(ask_trader)

    N = 40

    for theta in THETAS:
        targets = zeros((N,2))
        support = linspace(-1,1,N)
        rs = zeros(N)
        for i in range(N):
            r = support[i]
            for j in range(2):
                traders[j].theta = theta + 0.00001
                targets[i,j] = traders[j].calculate_target_price(r)
            rs[i] = r
       
        plot(rs,targets[:,0], 'r-')
        plot(rs,targets[:,1], 'b--')
    
    title('Extramarginal')
    show()

def test_instance(trader):
    N = 40
    targets = zeros(N)
    rs = zeros(N)
    for i in range(N):
        r = -1 + 2 * float(i) / N

        targets[i] = trader.calculate_target_price(r)
        rs[i] = r

    if trader.job == "Bid":
        plot(rs,targets, 'r-')    
        plot(rs,ones(N) * trader.limit,'r--')
    else:
        plot(rs,targets, 'b-')
        plot(rs,ones(N) * trader.limit,'b--')

    if trader.equilibrium:
        plot(rs,ones(N) * trader.equilibrium, 'k--')

    show()


if __name__ == "__main__":
    test_r_intramarginal()
    test_r_extramarginal()
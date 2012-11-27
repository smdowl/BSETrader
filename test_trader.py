from pylab import *
from BSE import *
from Trader_AA import Marginality

trader = Trader_AA('AA','B01',0.00)
trader.equilibrium = 3
trader.theta = 4
trader.job = 'Bid'
trader.limit = 2.5
trader.p_max = 6
trader.marginality = Marginality.Extra
trader.transactions = [6]

trader.alphas = [0.02,0.15]

targets = zeros(21)
rs = zeros(21)
for i in range(21):
    r = -1 + float(i) / 10
    targets[i] = trader.calculate_target_price(r)
    rs[i] = r
    
plot(rs,targets)
plot(rs,trader.equilibrium*ones(len(rs)),'k--')

lob = {'bids':{'best':5}}
print trader.calculate_r_shout(lob)
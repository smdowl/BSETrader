from BSE import bse_sys_minprice
from BSE import bse_sys_maxprice
from BSE import Order

from DefaultTraders import Trader
from numpy import exp
from numpy import log
import math

from log_maker import make_logger

import TraderUtils

logger = make_logger("trader_AA")
# logging.basicConfig(filename='trader_AA_log.log',level=logging.DEBUG)

class Marginality:
    Intra = 1
    Extra = 2
    Neutral = 3

def greater_than(a,b):
    return a > b

def less_than(a,b):
    return a < b

class Trader_AA(Trader):
    """ Adaptive Aggressive """

    def __init__(self, ttype, tid, balance, initial_data = None):
        """Call Trader's init method then add extra iVars"""
        Trader.__init__(self,ttype, tid, balance)

        # Keep track of all previous transaction prices
        self.transactions = []
        
        # A value for the degree of aggressiveness
        self.r = 0

        self.price = None

        # A value that influences long term bidding behaviour 
        self.theta = 0
        self.thetamax = 2
        self.thetamin = -8

        # Our approximation to the market equilibrium
        self.equilibrium = None

        # memory of best price & quantity of best bid and ask, on LOB on previous update 
        self.prev_best_bid_price = None
        self.prev_best_ask_price = None

        self.limit = None
        self.job = None 

        # store the max and min aloud on the market so that these values can be changed for testing
        self.p_min = bse_sys_minprice
        self.p_max = bse_sys_maxprice

        # Store the price volatility at every point in time (may be repeats)
        self.alphas = [0]

        # Store what marginality this trader is
        self.marginality = Marginality.Neutral;
        self.beta1 = 0.5
        self.beta2 = 0.5

        self.eta = 3

        # Store target price
        self.tau = None

    # def __str__(self):
    #     return '[limit %s price %s theta %s equilibrium %s theta %s r %s]' % (self.limit, self.price, self.theta, self.equilibrium, self.theta, self.r)

    @classmethod
    def init_from_json(cls, json_string):
        trader = cls(None,None,None)
        data = json.loads(json_string)
        for key in data:
            setattr(trader, key, data[key])
        return trader

    def getorder(self,time,countdown,lob):
        """Use the variables we have learnt to create an order"""

        if len(self.orders) < 1:
            self.active = False
            order = None
        else:
            self.active = True
            self.limit = self.orders[0].price
            self.job = self.orders[0].otype

            if len(self.transactions) == 0:
                best_bid = lob['bids']['best']
                best_ask = lob['asks']['best']

                if not best_bid:
                    best_bid = bse_sys_minprice

                if not best_ask:
                    best_ask = bse_sys_maxprice

                if self.job == 'Bid' and self.limit > best_bid:
                    self.price = best_bid + (min(self.limit,best_ask) - best_bid)/self.eta
                elif self.job == 'Ask' and self.limit < best_ask:
                    self.price = best_ask - (best_ask - max(self.limit,best_bid))/self.eta
                else:
                    self.price = None

            logger.debug("%s: %s" % (self.tid,str(self.price)))
            if self.price != None:
                order = Order(self.tid, self.job, self.price, self.orders[0].qty, time)
            else:
                order = None
        
        TraderUtils.dump_trader(self,time)

        return order
        

    def respond(self, time, lob, trade, verbose):
        """ Learn from what just happened in the market"""
        
        change = self.check_for_changes(trade,lob)

        best_bid = lob['bids']['best']
        best_ask = lob['asks']['best']

        if not best_bid:
            best_bid = bse_sys_minprice

        if not best_ask:
            best_ask = bse_sys_maxprice

        # If there have been some previous transactions then approximate the equilibrium
        if len(self.transactions) > 0:
            # If there has been any change then recalculate the equilibrium and our marginality
            if change:
                # Update our estimate the new market equilibrium
                self.calculate_market_equilibrium()
                # Update the marginality of the trader given the new estimate of the equilibrium price
                self.get_marginality()
            
            # Calculate theta from alpha
            self.theta = self.calculate_theta()

            r_shout = caclulate_r_shout(lob)
            self.r = calculate_r(r_shout)

            self.tau = self.calculate_target_price(self.r)
            if self.job == 'Bid' and self.limit > best_bid:
                self.price = best_bid + (self.tau - best_bid)/self.eta
            elif self.job == 'Ask' and self.limit < best_ask:
                self.price = best_ask - (best_ask - self.tau)/self.eta
            else:
                self.price = None

    def get_marginality(self):
        """Get the marginality based on the trader type and estimate of the market equilibrium"""

        # Set the comparison method depending on trader type
        comparator = None
        if (self.job == 'Bid'):
            comparator = greater_than
        else:
            comparator = less_than

        if (comparator(self.limit, self.equilibrium)):
            self.marginality  = Marginality.Intra
        elif not comparator(self.limit, self.equilibrium) and self.limit != self.equilibrium:
            self.marginality  = Marginality.Extra
        else:
            self.marginality = Marginality.Neutral

    def check_for_changes(self,trade,lob):
        """
        Add any new transactions to the list so that we can use them to approximate the equilibrium
        Returns true if there was a change in the market and false otherwise
        """
        # what, if anything, has happened on the bid LOB?
        bid_improved = False
        bid_hit = False
        lob_best_bid_p = lob['bids']['best']
        if lob_best_bid_p != None:
            # non-empty bid LOB
            if self.prev_best_bid_price < lob_best_bid_p :
                # best bid has improved
                # NB doesn't check if the improvement was by self
                bid_improved = True
            elif trade != None and (self.prev_best_bid_price > lob_best_bid_p):
                # previous best bid was hit                              
                bid_hit = True
                self.transations.append(self.prev_best_bid_price)
        elif self.prev_best_bid_price != None:
            # the bid LOB has been emptied by a hit
            bid_hit = True
            self.transations.append(self.prev_best_bid_price)
                        
        # what, if anything, has happened on the ask LOB?
        ask_improved = False
        ask_lifted = False
        lob_best_ask_p = lob['asks']['best']
        if lob_best_ask_p != None:
            # non-empty ask LOB
            if self.prev_best_ask_price > lob_best_ask_p :
                # best ask has improved -- NB doesn't check if the improvement was by self
                ask_improved = True
            elif trade != None and (self.prev_best_ask_price < lob_best_ask_p):
                    # trade happened and best ask price has got worse, or stayed same but quantity reduced -- assume previous best ask was lifted
                    ask_lifted = True
        elif self.prev_best_ask_price != None:
            # the bid LOB is empty now but was not previously, so must have been hit
            ask_lifted = True
            self.transactions.append(self.prev_best_ask_price)


        return bid_hit or ask_lifted

    def calculate_market_equilibrium(self):
        """ Use a weighted average of all previous transactions to calculate the market equilibrium """
        estimate_sum = 0
        weights = 0
        # Now we want to calculate the estimate of the equilibrium price
        for i in range(len(self.transactions)):
            weight = 0.9 ** (i-1)
            
            estimate_sum += self.transactions[-i] * weight
            weights += weight

        self.equilibrium = estimate_sum / weights

    def calculate_r_shout(self, lob):
        """
        Use current market estimates the work out what aggressiveness would be required to match the current price.
        Both the price and the function to solve depend on the marginality of the trader
        """

        price_to_match = lob[self.job.lower()+'s']['best']

        # Work out which direction r should move in if it results in a target price greater than the price_to_match
        if self.job == 'Ask': 
            iterate_multiplier = -1
            bid_range = self.p_max - self.limit
        else :
            iterate_multiplier = 1
            bid_range = self.limit

        r = 0
        last_target_price = 0
        target_price = self.calculate_target_price(r)

        # how close to the correct price do we want to get
        limit = 0.1
        
        i=1
        while abs(target_price - price_to_match) > limit:
            target_price = self.calculate_target_price(r)

            change = math.copysign(1,(price_to_match - target_price) * iterate_multiplier)

            r = r + change * 0.5 ** i
            
            # if the target price hasn't changed then we can't get any closer to the price_to_match
            if target_price == last_target_price:
                return change

            last_target_price = target_price
            
            i=i+1

        return r

    def calculate_r(self, r_shout):
        if r_shout < self.r:
            delta = 0.95 * r_shout
        else:
            delta = 1.05 * r_shout
        return self.r + self.beta1 * (delta - self.r)

    def calculate_target_price(self,r):
        """ 

        Using the current traders statistics and a set aggressiveness (r), calculate the correct target_price.
        This takes into consideration: equilibrium approximation, limit price, trader job, marginality (a different formula for each) and theta (long term learning)
        r has been left as an argument so that r can be tested to approximate r_shout

        *** WITH ALL OF THESE EQUATIONS WE HAVE NEGATED r SO THAT AGRESSIVENESS IS POSITIVE AND THE DIAGRAMS MATCH THOSE IN THE PAPER ***

        """

        if r > 1 or r < -1:
            assert('r should be in the range (-1,1)')

        if self.marginality == Marginality.Intra:
            if self.job == 'Bid':
                if r <= 0:
                    # orig
                    # return self.equilibrium * (1 - r * exp(self.theta * (r-1)))
                    return self.equilibrium * (1 + r * exp(self.theta * (-r-1)))
                elif r > 0:
                    theta_underscore = ((self.equilibrium * exp(-self.theta)) / (self.limit - self.equilibrium)) - 1
                    # return (self.limit - self.equilibrium) * (1 - (r+1) * exp(r * theta_underscore)) + self.equilibrium
                    return (self.limit - self.equilibrium) * (1 - (-r+1) * exp(-r * theta_underscore)) + self.equilibrium
            elif self.job == 'Ask':
                if r <= 0:
                    return self.equilibrium + (self.p_max - self.equilibrium) * (-r)*exp(-(r+1)*self.theta)
                elif r > 0:
                    theta_underscore = log((self.p_max - self.equilibrium)/(self.equilibrium-self.limit)) - self.theta
                    return self.equilibrium + (self.equilibrium - self.limit) * (-r) * exp((-r+1)*theta_underscore)

        if self.marginality == Marginality.Extra:
            if self.job == 'Bid':
                if r <= 0:
                    return self.limit * (1 + r * exp(-self.theta * (r+1)))
                elif r > 0:
                    return self.limit
            elif self.job == 'Ask':
                if r <= 0:
                    return self.limit + (self.p_max - self.limit) * (-r) * exp(-self.theta * (r+1))
                elif r > 0:
                    return self.limit

    def calculate_theta(self):
        thetastar = self.calculate_thetastar()
        return self.theta + beta2*(thetastar - self.theta)

    def calculate_thetastar(self,a=None):
        if a == None:
            temp = 0
            for i in range(len(self.transactions)):
                temp += (self.transactions[i] - self.equilibrium)**2
            a = (temp/len(self.transactions))**0.5
            a /= self.equilibrium
            self.alphas.append(a)

        if (max(self.alphas) == min(self.alphas)):
            ahat = 1
        else:
            ahat = 1 - (a - min(self.alphas))/(max(self.alphas) - min(self.alphas))
        
        return (self.thetamax - self.thetamin)*ahat*math.exp(1-ahat) + self.thetamin
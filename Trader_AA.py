from DefaultTraders import Trader

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
    def __init__(self, ttype, tid, balance):
        """Call Trader's init method then add extra iVars"""

        Trader.__init__(self,ttype, tid, balance)

        # Keep track of all previous transaction prices
        self.transaction_history = []
        
        # A value for the degree of aggressiveness
        self.r = 0

        # A value that influences long term bidding behaviour 
        self.theta = 0

        # Our approximation to the market equilibrium
        self.equilibrium = None

        self.transactions = []

        # memory of best price & quantity of best bid and ask, on LOB on previous update 
        self.prev_best_bid_price = None
        self.prev_best_ask_price = None

        self.limit = None
        self.job = None 

        # Store the value of the long term learning rate at every point in time (may be repeats)
        self.thetas = []

        # Store the price volatility at every point in time (may be repeats)
        self.alphas = []


    def getorder(self,time,countdown,lob):
        """Use the variables we have learnt to create an order"""
        if len(self.orders) < 1:
            self.active = False
            order = None
        else:
            self.active = True
            self.limit = self.orders[0].price
            self.job = self.orders[0].otype

            raise Exception('Code just copied from ZIP')

            if self.job == 'Bid':
                # currently a buyer (working a bid order)
                self.margin = self.margin_buy
            else:
                # currently a seller (working a sell order)
                self.margin = self.margin_sell

            quoteprice = int(self.limit * (1 + self.margin))
            self.price = quoteprice

            order=Order(self.tid, self.job, quoteprice, self.orders[0].qty, time)
                
        return order
        

    def respond(self, time, lob, trade, verbose):
        """Learn from what just happened in the market"""
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
                    self.transactions.append(self.prev_best_ask_price)
        elif self.prev_best_ask_price != None:
            # the bid LOB is empty now but was not previously, so must have been hit
            ask_hit = True

        # If there have been some previous transactions then approximate the equlibrium
        if len(self.transactions) > 0:
            estimate_sum = 0
            weights = 0
            # Now we want to calculate the estimate of the equilibrium price
            for i in range(len(self.transactions)):
                weight = 0.9 ** (i-1)
                
                estimate_sum += transations[-i] * weight
                weights += weight

            estimate = estimate_sum / weights

            marginality = self.get_marginality(estimate)

    def get_marginality(self,estimate):
        """Get the marginality based on the trade type and estimate to the market equilibrium"""

        # Set the comparison method depending on trader type
        comparator = None
        if (self.job == 'Ask'):
            comparator = greater_than
        else:
            comparator = less_than

        if (comparator(self.limit, estimate)):
            marginality  = Marginality.Intra
        elif  not comparator(self.limit, estimate) and self.limit != estimate:
            marginality  = Marginality.Extra
        else:
            marginality = Marginality.Neutral

        return marginality

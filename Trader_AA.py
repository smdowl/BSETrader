from DefaultTraders import Trader
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

    def getorder(self,time,countdown,lob):
        """Use the variables we have learnt to create an order"""
        return None

    def respond(self, time, lob, trade, verbose):
        """Learn from what just happened in the market"""
        pass
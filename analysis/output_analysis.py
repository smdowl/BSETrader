import os,sys
parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0,parentdir)

from BSE import Trader_AA
from utils import trader_utils
import json
from tests import test_trader

class TraderProfiles:
    """ A class to manage all the historical traders that have been stored during a simulation """ 
    def __init__(self):
        self.trader_histories = {}
        self.__import_data()

    def __import_data(self):
        with open("../" + trader_utils.trader_filepath()) as f:
            for line in f.readlines():
                line_dictionary = json.loads(line)
                
                tid = line_dictionary['tid']
                if tid in self.trader_histories:
                    self.trader_histories[tid].append(line_dictionary)
                else:
                    self.trader_histories[tid] = [line_dictionary]

    def find_trader_instance_for_transaction(self,transaction):
        try:
            trader_instances = self.trader_histories[transaction['tid']]
            previous_trader = None
            for instance in trader_instances:
                # print instance
                if instance['time'] == transaction['time']:
                    return (previous_trader, instance)
                previous_trader = instance
        except KeyError:
            print "No trader " + transaction['tid']
            return None

    def find_orders_for_ttype(self,ttype):
        tids = []
        for tid in self.trader_histories:
            if self.trader_histories[tid][0]['ttype'] == ttype:
                tids.append(tid)
        
        orders = {}
        for tid in tids:

            order_list = []
            
            for instance in self.trader_histories[tid]:
                try:
                    if instance['order']:
                        order_list.append(instance)
                except KeyError:
                    continue

            orders[tid] = order_list

        return orders

    def find_negative_offers(self):       
        instances = []
        for tid in self.trader_histories.keys():            
            for instance in self.trader_histories[tid]:
                if 'order' in instance:
                    print instance['job'], instance['order']['price'], instance['orders'][0]['price']
                    if instance['job'] == "Bid" and instance['order']['price'] > instance['orders'][0]['price']:
                        instances.append(instance)
                    elif instance['job'] == "Ask" and instance['order']['price'] < instance['orders'][0]['price']:
                        instances.append(instance)
        return instances

    def find_not_matching_offers(self):       
        """ Find the offers that don't have the same job as the trader """
        instances = []
        for tid in self.trader_histories.keys():            
            for instance in self.trader_histories[tid]:
                if 'order' in instance:
                    if instance['job'] != instance['order']['otype']:
                        instances.append(instance)
        return instances

class ProfitHistory:
    """ A class to store and extract information from a saved profit history json file """
    def __init__(self):
        self.profits = {}
        self.__import_profits()

    def __import_profits(self):
        with open("../" + trader_utils.profit_filepath()) as f:
            for line in f.readlines():
                line_dictionary = json.loads(line)
                
                tid = line_dictionary['tid']
                if tid in self.profits:
                    self.profits[tid].append(line_dictionary)
                else:
                    self.profits[tid] = [line_dictionary]

    def find_negatives(self):
        negatives = []
        for key in self.profits:
            profit_list = self.profits[key]
            for record in profit_list:
                if record['profit'] < 0:
                    negatives.append(record)
        return negatives

def find_loss():
    history = ProfitHistory()
    negative_profits = history.find_negatives()

    if len(negative_profits):
        traders = TraderProfiles()

        for profit in negative_profits:
            trader_pair = traders.find_trader_instance_for_transaction(profit)
            # trader = traders.find_trader_instance_for_transaction(profit)
            if trader_pair:
                # print profit
                # print trader_pair
                previous_trader = Trader_AA.init_from_json(trader_pair[0])
                trader = Trader_AA.init_from_json(trader_pair[1])
                # trader = Trader_AA.init_from_json(trader)

                # print "\n" + str(trader_pair[0]) + "\n" + str(trader_pair[1]) + "\n"
                print profit
                print str(trader) + "\n"
                test_trader.test_instance(trader)
                # print trader_pair[0]
                # print previous_trader.getorder(None,None,None)
                # print previous_trader
                # print trader

def list_losses():
    profiles = TraderProfiles()

    order_instances = profiles.find_orders_for_ttype("AA")
    for trader_history in order_instances.values():
        for instance in trader_history:
            # print instance['job'],instance['order']['price'], instance['limit']
            if instance['job'] == 'Bid' and instance['order']['price'] > instance['limit']:
                print instance['job'], instance['order']['price'], instance['limit']
            elif instance['job'] == 'Ask' and instance['order']['price'] < instance['limit']:
                print instance['job'], instance['order']['price'], instance['limit']
            elif instance['order']['price'] < 0:
                print instance['job'], instance['order']['price'], instance['limit']
                # trader = Trader_AA.init_from_json(instance)
                # test_trader.test_instance(trader)
                # break

def find_abnormal_trades():
    with open("../" + trader_utils.trades_filepath()) as f:
        for line in f.readlines():
            line_dictionary = json.loads(line)
            
if __name__ == "__main__":
    profiles = TraderProfiles()
    print profiles.find_negative_offers()
    print profiles.find_not_matching_offers()
    # print profiles.

    history = ProfitHistory()
    # for line in history.find_negatives():
    #     print line
    #     print line['job'],line['orders']['otype']
    # list_losses()





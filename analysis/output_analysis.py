import os,sys
parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0,parentdir)

import TraderUtils
from trader_aa import *
import json
from tests import test_trader

class TraderProfiles:
    """ A class to manage all the historical traders that have been stored during a simulation """ 
    def __init__(self):
        self.trader_histories = {}
        self.__import_data()

    def __import_data(self):
        with open("../" + TraderUtils.trader_filepath()) as f:
            for line in f.readlines():
                line_dictionary = json.loads(line)
                
                tid = line_dictionary['tid']
                if tid in self.trader_histories:
                    self.trader_histories[tid].append(line_dictionary)
                else:
                    self.trader_histories[tid] = [line_dictionary]

    def find_trader_instance_for_transaction(self,transaction):
        trader_instances = self.trader_histories[transaction['tid']]
        previous_trader = None
        for instance in trader_instances:
            # print instance
            if instance['time'] == transaction['time']:
                return (previous_trader, instance)
            previous_trader = instance

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

class ProfitHistory:
    """ A class to store and extract information from a saved profit history json file """
    def __init__(self):
        self.profits = {}
        self.__import_profits()

    def __import_profits(self):
        with open("../" + TraderUtils.profit_filepath()) as f:
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
        profit = negative_profits[0]

        trader_pair = traders.find_trader_instance_for_transaction(profit)
        # trader = traders.find_trader_instance_for_transaction(profit)

        print profit
        # print trader_pair
        previous_trader = Trader_AA.init_from_json(trader_pair[0])
        trader = Trader_AA.init_from_json(trader_pair[1])
        # trader = Trader_AA.init_from_json(trader)

        print "\n" + str(trader_pair[0]) + "\n"
        print "\n" + str(trader_pair[1]) + "\n"

        # test_trader.test_instance(trader)
        print trader_pair[0]
        # print previous_trader.getorder(None,None,None)
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

if __name__ == "__main__":
    find_loss()    





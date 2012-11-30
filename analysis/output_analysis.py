import os,sys
parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0,parentdir)

import TraderUtils
from trader_aa import *
import json

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
            if abs(instance['time'] - transaction['time']) < 0.1:
                print instance
                return (previous_trader, instance)
            previous_trader = instance

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

history = ProfitHistory()
negative_profits = history.find_negatives()

traders = TraderProfiles()
profit = negative_profits[0]

trader_pair = traders.find_trader_instance_for_transaction(profit)

# print profit
# print trader_pair
previous_trader = Trader_AA.init_from_json(trader_pair[0])
trader = Trader_AA.init_from_json(trader_pair[1])
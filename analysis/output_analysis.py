import os,sys
parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0,parentdir)
from pylab import *
from BSE import Trader_AA
from utils import trader_utils
import json, csv
from tests import test_trader
import pdb

import scipy.stats

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

    def get_trader_orders(self):
        tid = self.trader_histories.keys()[0]
        limits = array([0])
        for instance in self.trader_histories[tid]:
            limits = vstack((limits,instance['orders'][0]['price']))
        return limits

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

    def losses_per_trader(self):
        losses = {}
        for key in self.profits:
            for profit in self.profits[key]:
                ttype = profit['ttype']

                if profit['profit'] < 0:
                    if not ttype in losses.keys():
                        losses[ttype] = 1
                    else:
                        losses[ttype] += 1
        return losses


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
                # print profit
                # print str(trader) + "\n"
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

def find_nongvwy_transactions():
    count = 0
    with open("../" + trader_utils.trader_orders_filepath()) as f:
        reader = csv.reader(f)
        for row in reader:
            if row[2] != row[3]:
                count += 1
    return count    

def find_orders(job):
    buyers = []
    with open("../" + trader_utils.trader_orders_filepath()) as f:
        reader = csv.reader(f)
        for row in reader:
            if row[0][0] == job and row[0] not in buyers:
                buyers.append(row[0])
    return buyers

def get_transactions():
    transactions = {}
    all_ts = []
    with open('../output/transactions.csv') as f:
        reader = csv.reader(f)
        for row in reader:
            tid1 = row[0].strip()
            tid2 = row[1].strip()

            time = float(row[2])
            price = float(row[3])
            # print tid1,tid2
            if not tid1 in transactions:
                transactions[tid1] = array((time,price))
            else:
                transactions[tid1] = vstack((transactions[tid1], (time,price)))

            if not tid2 in transactions:
                transactions[tid2] = array((time,price))
            else:
                transactions[tid2] = vstack((transactions[tid2], (time,price)))

            if len(all_ts) == 0:
                all_ts = array((time,price))
            else:
                all_ts = vstack((all_ts, (time,price)))


    return (all_ts,transactions)

def plot_order_vs_limit(tids,all,job):
    with open("../" + trader_utils.trader_orders_filepath()) as f:
        reader = csv.reader(f)

        traders = {}
        # Keep track of every value so that we can plot more acurately
        points = []
        augmented = False

        for row in reader:
            tid = row[0]
            time = row[4]

            order_price = row[3]
            points.append(float(order_price))
            # if order_price <= 5 or order_price >= 900:
            #     order_price = None

            limit_price = row[2]
            try: points.append(float(limit_price))
            except Exception: pdb.set_trace()

            if len(row) > 5:
                equilibrium = float(row[5])
                points.append(float(equilibrium))
            else:
                equilibrium = None

            if len(row) > 6:
                r = float(row[6])
            else:
                r = None

            if len(row) > 7:
                try:
                    tau = float(row[7])
                except Exception:
                    pdb.set_trace()
            else:
                tau = None

            if len(row) > 8:
                agg_r = float(row[8])
                augmented = True
            else:
                agg_r = None


            if tid in tids:
                if not tid in traders:
                    trader = {}
                    trader['times'] = array([time])
                    trader['orders'] = array([order_price])
                    trader['limits'] = array([limit_price])
                    trader['equilibriums'] = array([equilibrium])
                    trader['rs'] = array([r])
                    trader['agg_rs'] = array([agg_r])
                    trader['taus'] = array([tau])
                else:
                    trader = traders[tid]
                    trader['times'] = vstack((trader['times'],time))
                    trader['orders'] = vstack((trader['orders'],order_price))
                    trader['limits'] = vstack((trader['limits'],limit_price))
                    trader['equilibriums'] = vstack((trader['equilibriums'],equilibrium))
                    trader['rs'] = vstack((trader['rs'],r))
                    trader['agg_rs'] = vstack((trader['agg_rs'],agg_r))
                    trader['taus'] = vstack((trader['taus'],tau))

                traders[tid] = trader

    (all_ts, transactions) = get_transactions()

    # pdb.set_trace()

    maximum = max(all_ts[:,1]) + 50
    minimum = min(all_ts[:,1]) - 50

    xlimit = (all_ts[0,0],all_ts[-1,0]*1.2)

    if augmented: number_of_plots = 3
    else: number_of_plots = 2

    square = int(ceil(sqrt(len(tids))))
    plot_index = 0
    for tid in traders:
        trader = traders[tid]
        
        if all:
            subplot(square, square, plot_index)
        else:
            subplot(number_of_plots, 1, 0)

        ylim((minimum, maximum))
        if not all: xlim(xlimit)
        plot(trader['times'],trader['limits'],'b.')
        
        plot(trader['times'],trader['orders'],'r.')
        plot(trader['times'],trader['equilibriums'],'k-')
        # try:
        #     if 'taus' in trader:
        #         plot(trader['times'],trader['taus'],'r--')            
        # except Exception:
        #     pdb.set_trace()

        plot(all_ts[:,0],all_ts[:,1],'cx',markersize=4)
        xlabel("time")
        ylabel("Price")
        if tid in transactions:
            if count_nonzero(transactions[tid]) == 2:
                plot(transactions[tid][0],transactions[tid][1], 'y*', markersize=10)
            else:
                plot(transactions[tid][:,0],transactions[tid][:,1], 'y*', markersize=10)

        
        if not all:
            legend(['Limit price', 'Order price', 'Equilibrium', 'Target Price', 'Market ts', 'Trader ts'])

            subplot(number_of_plots, 1, 1)    
            xlim(xlimit)   
            if job == 'S':
                title('Seller Trader AAA aggressiveness vs transactions')
            else:
                title('Buyer Trader AAA aggressiveness vs transactions')
            plot(trader['times'],trader['rs'],'b-')

            ylabel("Aggressiveness, r")
            if augmented:
                subplot(number_of_plots, 1, 2)       
                ylabel("Augmented Agg, r")
                plot(trader['times'],trader['agg_rs'],'b--')
            show()

        plot_index += 1

    if all:
        if job == 'S':
            suptitle('Seller Trader AAA transactions overview')
        else:
            suptitle('Buyer Trader AAA transactions overview')

    # while plot_index < square**2:
    #     print plot_index
    #     axes[plot_index].axis('off')
    #     plot_index += 1

    show()

def find_abnormal_trades():
    with open("../" + trader_utils.trades_filepath()) as f:
        for line in f.readlines():
            line_dictionary = json.loads(line)
            
if __name__ == "__main__":
    job = 'B'
    buyer_tids = find_orders(job)
    plot_order_vs_limit(buyer_tids,True,job)

    # print get_transactions()

    # profiles = TraderProfiles()
    # print profiles.get_trader_orders()
    # # print profiles.find_negative_offers()
    # # print profiles.find_not_matching_offers()
    # # print profiles.

    # history = ProfitHistory()

    # print history.profits
    # print history.losses_per_trader()

    # print find_nongvwy_transactions()

    # losses = history.find_negatives()
    # for loss in  losses:
    #     # print loss['ttype'], loss['profit']
    #     print loss
    #     (previous_trader, instance) = profiles.find_trader_instance_for_transaction(loss)
    #     print instance['job'], instance['orders'][0], instance['order']
    #     break 
    # for line in history.find_negatives():
    #     print line
    #     print line['job'],line['orders']['otype']
    # list_losses()





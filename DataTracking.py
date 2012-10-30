from numpy import *
from pylab import * 

class SupplyAndDemandCurve:
    """A structure to define both a supply and demand curve at a given point in time"""
    
    def __init__(self, time, bids, asks):
        """
        Initialise the curve with the time given and the lists of bids and asks.
        Then create quantity available at each price
        """
        self.time = time
        self.bids = sorted(bids,reverse=True)
        self.asks = sorted(asks)

        # Because each person only has 1 item the number of people offering at each index, i, is equal that index
        supply_values = transpose(array([range(1,size(self.asks)+1),self.asks]))
        demand_values = transpose(array([range(1,size(self.bids)+1),self.bids]))
        self.supply = self.create_curve_from_values(supply_values,100)
        self.demand = self.create_curve_from_values(demand_values,100)

    
    def create_curve_from_values(self,values,points_per_quantity):
        """Create data so that it is presentable via a line plot given an 2-d array of points""" 
        results = zeros((points_per_quantity * size(values)/2,2))
        for i in range(size(values)/2):
            quantity = values[i,0]
            price = values[i,1]
            for j in range(points_per_quantity):
                results[i*points_per_quantity + j,0] = quantity + float(j)/points_per_quantity
                results[i*points_per_quantity + j,1] = price
                
        return results
    
    def plot(self):
        plot(self.supply[:,0],self.supply[:,1],color='b',label = 'Supply')
        plot(self.demand[:,0],self.demand[:,1],color='r',label = 'Demand')
#        legend(['Supply', 'Demand'], loc = 1)
        title('Supply and Demand at T=%i'%self.time)
        xlabel('Quantity')
        ylabel('Price')
        show()
        
    def __repr__(self):
        return 'SupplyAndDemandCurve(%s,%s,%s)' % (self.time,self.bids,self.asks)

import json
def plot_orderpoints(filename):
    """Plot all the price vs time for all the traders"""
    with open(filename) as orderpoints_file:
        orderpoints = orderpoints_file.readlines()
        for line in orderpoints:
            points = json.loads(line)

    bid_traders = points['bids']
    # Sort the traders by the key their key
    sorted_traders = sorted(bid_traders)
    for trader_key in sorted_traders:
        # get the list of orders placed by each bid trader
        trader = array(bid_traders[trader_key])
        plot(trader[:,0],trader[:,1],'-',label=trader_key)

    ask_traders = points['asks']
    sorted_traders = sorted(ask_traders)
    for trader_key in sorted_traders:
        # get the list of orders placed by each ask trader
        trader = array(ask_traders[trader_key])
        plot(trader[:,0],trader[:,1],'--',label=trader_key)

    legend()
    # now add the transactions over the top
    show_transactions()
    show()

import csv
def show_transactions():
    """Show the price of the transactions that went through and what time they occured"""
    MOVING_AVE_LENGTH = 5

    times = []
    values = []
    parties = []
    with open('transactions.csv','rb') as transactionsFile:
        transactionReader = csv.reader(transactionsFile)
        for row in transactionReader:
            time = float(row[0])
            value = int(row[1])
            party1 = row[2]
            party2 = row[3]

            times.append(time)
            values.append(value)
            parties.append((party1,party2))

    times = array(times)
    values = array(values)
    
    plot(times,values,'kx')

    for index in range(len(times)):
        seed()
        sign = 1 + 2 * (-1 * ((floor(100 * rand()) % 2)))
        label_y = sign * (10 + int(floor(10 * rand())))
        annotate('(%s,%s)'%(parties[index]),
             xy=(times[index], values[index]), xycoords='data',
             xytext=(+10, label_y), textcoords='offset points', fontsize=10,
             arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=.2"))
        index+=1


## Trying to store lists of plots
# import json
# def plot_orderpoints(filename):
#     """Plot all the price vs time for all the traders"""
#     with open(filename) as orderpoints_file:
#         orderpoints = orderpoints_file.readlines()
#         for line in orderpoints:
#             points = json.loads(line)
    
#     bid_traders = points['bids']
#     for trader_key in bid_traders.keys():
#         # get the list of orders placed by each bid trader
#         trader_lists = bid_traders[trader_key]
#         for line in trader_lists:
#             line_array = array(line)
#             plot(line_array[:,0],line_array[:,1],'--',label=trader_key)

#     # ask_traders = points['asks']
#     # for trader_key in ask_traders.keys():
#     #     # get the list of orders placed by each ask trader
#     #     trader = array(ask_traders[trader_key])
#     #     plot(trader[:,0],trader[:,1],label=trader_key)

#     # legend()
#     show()
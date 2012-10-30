# -*- coding: utf-8 -*-
#
# BSE: The Bristol Stock Exchange
#
# Copyright (c) 2012, Dave Cliff
#
#
# ------------------------
#
# MIT Open-Source License:
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and
# associated documentation files (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or substantial
# portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT
# LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
# ------------------------
#
#
#
# BSE is a very simple simulation of automated execution traders
# operating on a very simple model of a limit order book (LOB) exchange
#
# major simplifications in this version:
#       (a) only one financial instrument being traded
#       (b) traders can only trade contracts of size 1 (will add variable quantities later)
#       (c) each trader can have max of one order per single orderbook.
#       (d) traders can replace/overwrite earlier orders, but cannot cancel
#       (d) simply processes each order in sequence and republishes LOB to all traders
#           => no issues with exchange processing latency/delays or simultaneously issued orders.
#
# NB this code has been written to be readable, not efficient!



# could import pylab here for graphing etc
import sys
import random
import pickle
import json

ticksize = 1
bse_sys_minprice = 1
bse_sys_maxprice = 1000

# an Order has a trader id, a type (buy/sell) price, quantity, and time it was issued
class Order:
        
        def __init__(self, tid, otype, price, qty, time):
                self.tid = tid
                self.otype = otype
                self.price = price
                self.qty = qty
                self.time = time
                
        def __str__(self):
                return '[%s %s P=%03d Q=%s T=%s]' % (self.tid, self.otype, self.price, self.qty, self.time)



# Orderbook_half is one side of the book: a list of bids or a list of asks, each sorted best-first

class Orderbook_half(object):

        def __init__(self, booktype, worstprice):
                # booktype: bids or asks?
                self.booktype = booktype
                # dictionary of orders received, indexed by Trader ID
                self.orders = {} 
                # limit order book, dictionary indexed by price, with order info
                self.lob = {}
                # anonymized LOB, lists, with only price/qty info
                self.lob_anon = [] 
                # summary stats
                self.best_price = None
                self.best_tid = None
                self.worstprice = worstprice
                self.n_orders = 0 # how many orders? 
                self.lob_depth = 0 # how many different prices on lob?


        def anonymize_lob(self):
                # anonymize a lob, strip out order details, format as a sorted list
                # NB for asks, the sorting should be reversed
                self.lob_anon = []
                for price in sorted(self.lob):
                        qty = self.lob[price][0]
                        self.lob_anon.append([price, qty])
                

        def build_lob(self):
                # take a list of orders and build a limit-order-book (lob) from it
                # NB the exchange needs to know arrival times and trader-id associated with each order
                # returns lob as a dictionary (i.e., unsorted)
                # also builds anonymized version (just price/quantity, sorted, as a list) for publishing to traders
                self.lob = {}
                for tid in self.orders:
                        order = self.orders.get(tid)
                        price = order.price
                        if price in self.lob:
                                # update existing entry
                                qty = self.lob[price][0]
                                orderlist = self.lob[price][1]
                                orderlist.append([order.time, order.qty, order.tid])
                                self.lob[price] = [qty+order.qty, orderlist]
                        else:
                                #create a new dictionary entry
                                self.lob[price] = [order.qty, [[order.time, order.qty, order.tid]]]
                # create anonymized version
                self.anonymize_lob()
                # record best price and associated trader-id
                if len(self.lob) > 0 :
                        if self.booktype == 'Bid':
                                self.best_price = self.lob_anon[-1][0]
                        else :
                                self.best_price = self.lob_anon[0][0]
                        self.best_tid = self.lob[self.best_price][1][0][2]
                else :
                        self.best_price = None
                        self.best_tid = None
                      

        def book_add(self, order):
                # add order to the dictionary holding the list of orders
                # either overwrites old order from this trader
                # or dynamically creates new entry in the dictionary
                # so, max of one order per trader per list
                self.orders[order.tid] = order
                self.n_orders = len(self.orders)
                self.build_lob()


        def book_del(self, order):
                # delete order to the dictionary holding the orders
                # assumes max of one order per trader per list
                # checks that the Trader ID does actually exist in the dict before deletion 
                if self.orders.get(order.tid)!= None :
                        del(self.orders[order.tid])
                        self.n_orders = len(self.orders)
                        self.build_lob()
                

        def delete_best(self):
                # delete order: when the best bid/ask has been hit, delete it from the book
                # the TraderID of the deleted order is return-value, as counterparty to the trade
                best_price_orders = self.lob[self.best_price]
                best_price_qty = best_price_orders[0]
                best_price_counterparty = best_price_orders[1][0][2]
                if best_price_qty == 1:
                        # here the order deletes the best price
                        del(self.lob[self.best_price])
                        del(self.orders[best_price_counterparty])
                        self.n_orders = self.n_orders-1
                        if self.n_orders > 0:
                                self.best_price = min(self.lob.keys())
                                self.lob_depth = len(self.lob.keys())
                        else:
                                self.best_price = self.worstprice
                                self.lob_depth = 0
                else:
                        # best_bid_qty>1 so the order decrements the quantity of the best bid     
                        # update the lob with the decremented order data
                        self.lob[self.best_price] = [best_price_qty-1, best_price_orders[1][1:]]
                      
                        # update the bid list: counterparty's bid has been deleted
                        del(self.orders[best_price_counterparty])
                        self.n_orders = self.n_orders-1
                self.build_lob()
                return best_price_counterparty

        def get_values(self):
            """Returns the price of every order in a list"""
            values = []
            for order in self.orders.values():
                values.append(order.price)
            return values


# Orderbook for a single instrument: list of bids and list of asks

class Orderbook(Orderbook_half):

        def __init__(self):
                self.bids = Orderbook_half('Bid',bse_sys_minprice)
                self.asks = Orderbook_half('Ask',bse_sys_maxprice)
                self.tape = []



# Exchange's internal orderbook

class Exchange(Orderbook):

        def __init__(self):
            super(Exchange,self).__init__()
                             
        def add_order(self, order):
                # add an order to the exchange and update all internal records
                tid = order.tid
                if order.otype == 'Bid':
                        self.bids.book_add(order)
                        best_price = self.bids.lob_anon[-1][0]
                        self.bids.best_price = best_price
                        self.bids.best_tid = self.bids.lob[best_price][1][0][2]
                else:
                        self.asks.book_add(order)
                        best_price = self.asks.lob_anon[0][0]
                        self.asks.best_price = best_price
                        self.asks.best_tid = self.asks.lob[best_price][1][0][2]


        def del_order(self, order):
                # delete an order from the exchange, update all internal records
                tid = order.tid
                if order.otype == 'Bid':
                        self.bids.book_del(order)
                        best_price = self.bids.lob_anon[-1][0]
                        self.bids.best_price = best_price
                        self.bids.best_tid = self.bids.lob[best_price][1][0][2]
                else:
                        self.asks.book_del(order)
                        best_price = self.asks.lob_anon[0][0]
                        self.asks.best_price = best_price
                        self.asks.best_tid = self.asks.lob[best_price][1][0][2]
                        
                                                      
        def process_order2(self, time, order, verbose):
                # receive an order and either add it to the relevant LOB (ie treat as limit order)
                # or if it crosses the best counterparty offer, execute (treat as a market order)             
                oprice = order.price
                counterparty = None
                self.add_order(order) # add it to the order lists -- overwriting any previous order       
                best_ask = self.asks.best_price
                best_ask_tid = self.asks.best_tid
                best_bid = self.bids.best_price
                best_bid_tid = self.bids.best_tid
                if order.otype == 'Bid':
                        if self.asks.n_orders > 0 and best_bid >= best_ask:
                                # bid hits the best ask
                                if verbose: print("Bid hits best ask")
                                counterparty = best_ask_tid
                                price = best_ask # bid crossed ask, so use ask price
                                if verbose: print('counterparty, price',counterparty, price)
                                # delete the ask just crossed
                                self.asks.delete_best()
                                # delete the bid that was the latest order
                                self.bids.delete_best()
                elif order.otype == 'Ask':
                        if self.bids.n_orders > 0 and best_ask <= best_bid:
                                # ask hits the best bid
                                if verbose: print("Ask hits best bid")
                                # remove the best bid
                                counterparty = best_bid_tid
                                price = best_bid # ask crossed bid, so use bid price
                                if verbose: print('counterparty, price',counterparty, price)
                                # delete the bid just crossed, from the exchange's records
                                self.bids.delete_best()
                                # delete the ask that was the latest order, from the exchange's records
                                self.asks.delete_best()
                else:
                        # we should never get here
                        sys.exit('process_order() given neither Bid nor Ask')
                # NB at this point we have deleted the order from the exchange's records
                # but the two traders concerned still have to be notified
                if counterparty != None:
                        # process the trade
                        if verbose: print('>>>>>>>>>>>>>>>>>TRADE t=%d $%d %s %s' % (int(time), price, counterparty, order.tid))
                        transaction_record = {'time': time,
                                               'price': price,
                                               'party1':counterparty,
                                               'party2':order.tid,
                                               'qty': order.qty}
                        self.tape.append(transaction_record)
                        return transaction_record
                else:
                        return None                 

                                                      

        def tape_dump(self,fname,fmode,tmode):
                dumpfile = open(fname,fmode)
                for tapeitem in self.tape:
                        dumpfile.write('%s, %s, %s, %s\n' % (tapeitem['time'], tapeitem['price'],tapeitem['party1'], tapeitem['party2']))
                dumpfile.close()
                if tmode == 'wipe':
                        self.tape = []     

        # this returns the LOB data "published" by the exchange,
        # i.e., what is accessible to the traders
        def publish_lob(self, time, verbose):
                public_data={}
                public_data['time']=time
                public_data['bids']={'best':self.bids.best_price,
                                     'worst':self.bids.worstprice,
                                     'n': self.bids.n_orders,
                                     'lob':self.bids.lob_anon}
                public_data['asks']={'best':self.asks.best_price,
                                     'worst':self.asks.worstprice,
                                     'n': self.asks.n_orders,
                                     'lob':self.asks.lob_anon}
                if verbose:
                        print('publish_lob: t=%d' % time)
                        print('BID_lob=%s' % public_data['bids']['lob']) 
                        print('ASK_lob=%s' % public_data['asks']['lob']) 
                return public_data

# After all the BSE objects have been set up, now import the traders
from DefaultTraders import *

# one session in the market
def market_session(sess_id, starttime, endtime, trader_spec, order_schedule, dumpfile, dump_each_trade):

        def store_charts_as_json(fname,charts):
            """Convert the dictionary describing each supply and demand chart to json and write it to the given file"""
            chart_file = open(fname,'w')
            for chart in charts:
                chart_file.write('%s\n' % json.dumps(chart))

        def add_new_orderpoint_to_dictionary(orderpoints,bot_id,time,price):
            """Actually create and add the new orderpoint to the dictionary of lists of orderpoints using the id provided as the key"""
            if bot_id not in orderpoints:
                trader_orders = [(time,price)]
                orderpoints[bot_id] = trader_orders
            else:
                trader_orders = orderpoints[bot_id]

                # If there was already an order at a given time then replace it with the new value (seemed to have an effect when new orders came in)
                if trader_orders[-1][0] == time:
                    # print 'replacing order %s' % str(trader_orders[-1])
                    trader_orders[-1] = (time,price)
                else:
                    trader_orders.append((time,price))

        def add_all_current_orders_for_type(exchange,all_orderpoints,traders,order_type,time):
            # First, get the correct list of orders from the exchange
            orders = None
            if order_type == 'bids':
                orders = exchange.bids.orders
            elif order_type == 'asks':
                orders = exchange.asks.orders

            if orders == None:
                raise Exception('Incorrect order type', 'define an order type as either buy or sell')

            # Make sure that that order_type in in the all_orderpoints dictionary
            if order_type not in all_orderpoints:
                orderpoints = {}
                all_orderpoints[order_type] = orderpoints
            else:
                orderpoints = all_orderpoints[order_type]

            # Go through each of the current orders and find the list of orders corresponding to that bot
            for order in orders.values():
                bot_id = '%s (%s)' % (order.tid,traders[order.tid].ttype)
                add_new_orderpoint_to_dictionary(orderpoints,bot_id,time,order.price)
            

        def add_orderpoints(exchange,all_orderpoints,traders,time,new_order):
            """
            Adds all the orderpoint at a given moment in time.
            all_orderpoints is broken into bids/asks buckets then into buckets for each trader
            Each trader's orders are then broken up based on whether they had an order in the previous time step
            This results in each TID being the key for a list of lists of points in the form (time,price)
            """

            add_all_current_orders_for_type(exchange,all_orderpoints,traders,'bids',time)
            add_all_current_orders_for_type(exchange,all_orderpoints,traders,'asks',time)
            
            orders = exchange.bids.orders.values() + exchange.asks.orders.values()

            # Check for each trader to see if there is a current order for them. If not, just drop the price down to zero.
            for trader in traders.values():
                bot_id = '%s (%s)' % (trader.tid,trader.ttype)
                if not bot_id in orders:
                    add_new_orderpoint_to_dictionary(orderpoints,bot_id,time,0)

            # Process the new order that came in if there was one. This will override whatever was put there in the last loop
            new_order_id = ''
            if new_order != None:
                new_order_id = '%s (%s)' % (new_order.tid,traders[new_order.tid].ttype)
                # print 'Adding new order %s' % new_order
                add_new_orderpoint_to_dictionary(orderpoints,new_order_id,time,new_order.price)



        def store_orderpoints_as_json(fname,orderpoints):
            """Convert the dictionary mapping traders to (time,ordervalues) points"""
            orderpoint_file = open(fname,'w')
            orderpoint_file.write('%s\n' % json.dumps(orderpoints))

        # initialise the exchange
        exchange = Exchange()

        # create a bunch of traders
        traders = {}
        trader_stats = populate_market(trader_spec, traders, True, True)

        # timestep set so that can process all traders in one second
        timestep = 1.0/float(trader_stats['n_buyers']+trader_stats['n_sellers']) 
        duration = float(endtime - starttime)

        last_update = -1.0

        time = starttime
        orders_verbose = True
        lob_verbose = False
        respond_verbose = False

        # Set the time to wait before making a new supply/demand chart
        number_of_charts = 10
        chart_timestep = order_schedule['interval'] / number_of_charts
        chart_counter = 0
        charts = []

        # Set the time to wait before taking another set of order values data points
        number_of_orderpoints = 100
        orderpoint_timestep = order_schedule['interval'] / number_of_orderpoints
        orderpoint_counter = 0

        # We are going to store the order points in a dictionary mapping TID to a list of tuples of points (time,price)
        # Firstly the dictionary is broken up into buy/sell then further by TID
        orderpoints = {}

        while time < endtime:

                # how much time left, as a percentage?
                time_left = (endtime - time) / duration

##                print('%s; t=%08.2f (%4.1f) ' % (sess_id, time, time_left*100))

                trade = None

                lu = customer_orders(time, last_update, traders, trader_stats, order_schedule, orders_verbose)
                if lu != None:
                        last_update = lu

                #get an order (or None) from a randomly chosen trader
                tid = list(traders.keys())[random.randint(0,len(traders)-1)]        
                order = traders[tid].getorder(time,time_left,exchange.publish_lob(time, lob_verbose))

                if order != None:
                        # send order to exchange
                        trade = exchange.process_order2(time, order, True)
                        if trade != None:
                                # trade occurred,
                                # so the counterparties update order lists and blotters
                                traders[trade['party1']].bookkeep(trade, order)
                                traders[trade['party2']].bookkeep(trade, order)
                                if dump_each_trade: trade_stats(sess_id, traders, tdump, time, exchange.publish_lob(time, lob_verbose))

                        # traders respond to whatever happened
                        lob = exchange.publish_lob(time, lob_verbose)
                        for t in traders:
                                traders[t].respond(time, lob, trade, respond_verbose)

                        # Also store the current supply and demand info
                        bid_values = exchange.bids.get_values()
                        ask_values = exchange.asks.get_values()

                # If its time to store another set of values to create a supply/demand chart then do it
                if chart_counter > chart_timestep:
                    charts.append({'time':time,'bids':bid_values,'asks':ask_values})
                    chart_counter = 0

                # If it is time to store another set of ask/buy datapoints then do it
                # if orderpoint_counter > orderpoint_timestep:
                # MAKE SURE THERE ARE SOME BIDS AND ASKS. THIS IS A BIT OF A HACK
                if len(exchange.bids.orders) > 0 and len(exchange.asks.orders) > 0:
                    # bid_orders = exchange.bids.orders
                    # for order in bid_orders.values():
                    #     bot_id = '%s (%s)' % (order.tid,traders[order.tid].ttype)
                    #     if bot_id not in bid_orderpoints:
                    #         trader_bids = []
                    #     else:
                    #         trader_bids = bid_orderpoints[bot_id]
                    #     trader_bids.append((order.time,order.price))
                    #     bid_orderpoints[bot_id] = trader_bids
                    
                    # ask_orders = exchange.asks.orders
                    # for order in ask_orders.values():
                    #     bot_id = '%s (%s)' % (order.tid,traders[order.tid].ttype)
                    #     if bot_id not in ask_orderpoints:
                    #         trader_asks = []
                    #     else:
                    #         trader_asks = ask_orderpoints[bot_id]
                    #     trader_asks.append((order.time,order.price))
                    #     ask_orderpoints[bot_id] = trader_asks

                    add_orderpoints(exchange,orderpoints,traders,time,order)

                    orderpoint_counter = 0
                        
                time = time + timestep
                chart_counter += timestep
                orderpoint_counter += timestep
        
        # end of an experiment -- dump the tape
        exchange.tape_dump('transactions.csv','w','keep')

        # write trade_stats for this experiment NB end-of-session summary only
        trade_stats(sess_id, traders, dumpfile, time, exchange.publish_lob(time, lob_verbose))    

        store_charts_as_json('charts.json', charts)
        store_orderpoints_as_json('orderpoints.json',orderpoints)
        

# create a bunch of traders from traders_spec
# returns dictionary of (n_buyers, n_sellers)
# optionally shuffles the pack of buyers and the pack of sellers
def populate_market(traders_spec, traders, shuffle, verbose):

        def trader_type(robottype, name):
                if robottype == 'GVWY':
                        return Trader_Giveaway('GVWY', name, 0.00)
                elif robottype == 'ZIC':
                        return Trader_ZIC('ZIC', name, 0.00)
                elif robottype == 'SHVR':
                        return Trader_Shaver('SHVR', name, 0.00)
                elif robottype == 'SNPR':
                        return Trader_Sniper('SNPR', name, 0.00)
                elif robottype == 'ZIP':
                        return Trader_ZIP('ZIP', name, 0.00)
                else:
                        sys.exit('FATAL: don\'t know robot type %s\n' % robottype)


        def shuffle_traders(ttype_char, n, traders):
                for swap in (10* range(n)):
                        t1 = random.randint(0,n-1)
                        t2 = t1
                        while t2 == t1:
                                t2 = random.randint(0,n-1)
                        t1name = '%c%02d' % (ttype_char, t1)
                        t2name = '%c%02d' % (ttype_char, t2)
                        traders[t1name].tid = t2name
                        traders[t2name].tid = t1name
                        temp = traders[t1name]
                        traders[t1name] = traders[t2name]
                        traders[t2name] = temp
                       
                
        n_buyers = 0
        for bs in traders_spec['buyers']:
                ttype = bs[0]
                for b in range(bs[1]):
                        tname = 'B%02d' % n_buyers # buyer i.d. string
                        traders[tname] = trader_type(ttype, tname)
                        n_buyers = n_buyers + 1

        if n_buyers < 1:
                sys.exit('FATAL: no buyers specified\n')

        if shuffle: shuffle_traders('B', n_buyers, traders)

                
        n_sellers = 0
        for ss in traders_spec['sellers']:
                ttype = ss[0]
                for s in range(ss[1]):
                        tname = 'S%02d' % n_sellers # buyer i.d. string
                        traders[tname] = trader_type(ttype, tname)
                        n_sellers = n_sellers + 1
        
        if n_sellers < 1:
                sys.exit('FATAL: no sellers specified\n')

        if shuffle: shuffle_traders('S', n_sellers, traders)

        if verbose :
                for t in range(n_buyers):
                        bname = 'B%02d' % t
                        print(traders[bname])
                for t in range(n_sellers):
                        bname = 'S%02d' % t
                        print(traders[bname])


        return {'n_buyers':n_buyers, 'n_sellers':n_sellers}

# trade_stats()
# dump CSV statistics on exchange data and trader population to file for later analysis
# this makes no assumptions about the number of types of traders, or
# the number of traders of any one type -- allows either/both to change
# between successive calls, but that does make it inefficient as it has to
# re-analyse the entire set of traders on each call
def trade_stats(expid, traders, dumpfile, time, lob):
        trader_types = {}
        n_traders = len(traders)
        for t in traders:
                ttype = traders[t].ttype
                if ttype in trader_types.keys():
                        t_balance = trader_types[ttype]['balance_sum'] + traders[t].balance
                        n = trader_types[ttype]['n'] + 1
                else:
                        t_balance = traders[t].balance
                        n = 1
                trader_types[ttype]={'n':n, 'balance_sum':t_balance}


        dumpfile.write('%s, %06d, '% (expid, time))
        for ttype in sorted(list(trader_types.keys())):
                n = trader_types[ttype]['n']
                s = trader_types[ttype]['balance_sum']
                dumpfile.write('%s, %d, %d, %f, ' % (ttype, s, n, s/float(n)))
                               
        if lob['bids']['best'] != None :
                dumpfile.write('%d, ' % (lob['bids']['best']))
        else:

                dumpfile.write('N, ')
        if lob['asks']['best'] != None :
                dumpfile.write('%d, '% (lob['asks']['best']))
        else:
                dumpfile.write('N, ')
        dumpfile.write('\n');
        

                        


# customer_orders: allocate orders to traders
# needs extending for continuous drip-feed replenishment
# NB will be extended to allow multiple ranges for mode='random'

def customer_orders(time, last_update, traders, trader_stats, os, verbose):


        def sysmin_check(price):
                if price < bse_sys_minprice:
                        print('WARNING: price < bse_sys_min -- clipped')
                        price = bse_sys_minprice
                return price

        def sysmax_check(price):
                if price > bse_sys_maxprice:
                        print('WARNING: price > bse_sys_max -- clipped')
                        price = bse_sys_maxprice
                return price

        def getorderprice(i, sched, n, mode):
                pmin = sysmin_check(min(sched[0][0], sched[0][1]))
                pmax = sysmax_check(max(sched[0][0], sched[0][1]))
                prange = pmax-pmin
                stepsize = prange/(n-1)
                halfstep = round(stepsize/2.0)
                if mode == 'fixed':
                        orderprice = pmin + int(i*stepsize)
                elif mode == 'jittered':
                        orderprice = pmin + int(i*stepsize) + random.randint(-halfstep,halfstep)
                elif mode == 'random':
                        orderprice = random.randint(pmin,pmax)
                else:
                        sys.exit('FAIL: Unknown mode in schedule')
                orderprice = sysmin_check(sysmax_check(orderprice))                
                return orderprice

        
        n_buyers = trader_stats['n_buyers']
        n_sellers = trader_stats['n_sellers']
        n_traders = n_buyers + n_sellers

        itime = int(time)

        # here we do a full instantaneous replenishment once every replenish_interval
        if ((itime % os['interval']) == 0) and (itime > last_update):           
                if verbose: print('>>>>>>>>>>>>>>>>>>REPLENISHING')
                for t in range(n_buyers):
                        tname = 'B%02d' % t  # demand side (a buyer)
                        ordertype = 'Bid'
                        sched = os['dem']['ranges']
                        mode = os['dem']['mode']
                        orderprice = getorderprice(t, sched, n_buyers, mode)
                        order = Order(tname, ordertype, orderprice, 1, time)
                        if verbose: print order
                        traders[tname].add_order(order)

                for t in range(n_sellers):
                        tname = 'S%02d' % t  # supply side (a seller)
                        ordertype = 'Ask'
                        sched = os['sup']['ranges']
                        mode = os['sup']['mode']
                        orderprice = getorderprice(t, sched, n_sellers, mode)
                        order = Order(tname, ordertype, orderprice, 1, time)
                        if verbose: print order
                        traders[tname].add_order(order)

                return itime # returns time of last replenishment, if there was one
        else:
                return None 
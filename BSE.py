# -*- coding: utf-8 -*-
#
# BSE: The Bristol Stock Exchange
#
# Version 1.2; November 17th, 2012. 
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
import os,sys
parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0,parentdir)

import math
import random

import pdb

from numpy import exp
from numpy import log
from numpy import zeros
from numpy import ones
from matplotlib.pyplot import *

from utils import trader_utils

bse_sys_minprice = 1  # minimum price in the system, in cents/pennies
bse_sys_maxprice = 1000  # maximum price in the system, in cents/pennies
ticksize = 1  # minimum change in price, in cents/pennies

# an Order has a trader id, a type (buy/sell) price, quantity, and time it was issued
class Order:

        def __init__(self, tid, otype, price, qty, time):
                self.tid = tid
                self.otype = otype
                self.price = price
                self.qty = qty
                self.time = time

        def __str__(self):
                return '[%s %s P=%03d Q=%s T=%5.2f]' % (self.tid, self.otype, self.price, self.qty, self.time)



# Orderbook_half is one side of the book: a list of bids or a list of asks, each sorted best-first

class Orderbook_half:

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
                self.n_orders = 0  # how many orders?
                self.lob_depth = 0  # how many different prices on lob?


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
                                self.lob[price] = [qty + order.qty, orderlist]
                        else:
                                # create a new dictionary entry
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
                if self.orders.get(order.tid) != None :
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
                        self.n_orders = self.n_orders - 1
                        if self.n_orders > 0:
                                self.best_price = min(self.lob.keys())
                                self.lob_depth = len(self.lob.keys())
                        else:
                                self.best_price = self.worstprice
                                self.lob_depth = 0
                else:
                        # best_bid_qty>1 so the order decrements the quantity of the best bid
                        # update the lob with the decremented order data
                        self.lob[self.best_price] = [best_price_qty - 1, best_price_orders[1][1:]]

                        # update the bid list: counterparty's bid has been deleted
                        del(self.orders[best_price_counterparty])
                        self.n_orders = self.n_orders - 1
                self.build_lob()
                return best_price_counterparty



# Orderbook for a single instrument: list of bids and list of asks

class Orderbook(Orderbook_half):

        def __init__(self):
                self.bids = Orderbook_half('Bid', bse_sys_minprice)
                self.asks = Orderbook_half('Ask', bse_sys_maxprice)
                self.tape = []



# Exchange's internal orderbook

class Exchange(Orderbook):

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
                self.add_order(order)  # add it to the order lists -- overwriting any previous order
                best_ask = self.asks.best_price
                best_ask_tid = self.asks.best_tid
                best_bid = self.bids.best_price
                best_bid_tid = self.bids.best_tid
                if order.otype == 'Bid':
                        if self.asks.n_orders > 0 and best_bid >= best_ask:
                                # bid hits the best ask
                                if verbose: print("Bid hits best ask")
                                counterparty = best_ask_tid
                                price = best_ask  # bid crossed ask, so use ask price
                                if verbose: print('counterparty, price', counterparty, price)
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
                                price = best_bid  # ask crossed bid, so use bid price
                                if verbose: print('counterparty, price', counterparty, price)
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
                        if verbose: print('>>>>>>>>>>>>>>>>>TRADE t=%5.2f $%d %s %s' % (time, price, counterparty, order.tid))
                        transaction_record = {'time': time,
                                               'price': price,
                                               'party1':counterparty,
                                               'party2':order.tid,
                                               'qty': order.qty}
                        self.tape.append(transaction_record)
                        return transaction_record
                else:
                        return None



        def tape_dump(self, fname, fmode, tmode):
                dumpfile = open(fname, fmode)
                for tapeitem in self.tape:
                        dumpfile.write('%s, %s, %s, %s\n' % (tapeitem['party1'],tapeitem['party2'],tapeitem['time'], tapeitem['price']))
                dumpfile.close()
                if tmode == 'wipe':
                        self.tape = []


        # this returns the LOB data "published" by the exchange,
        # i.e., what is accessible to the traders
        def publish_lob(self, time, verbose):
                public_data = {}
                public_data['time'] = time
                public_data['bids'] = {'best':self.bids.best_price,
                                     'worst':self.bids.worstprice,
                                     'n': self.bids.n_orders,
                                     'lob':self.bids.lob_anon}
                public_data['asks'] = {'best':self.asks.best_price,
                                     'worst':self.asks.worstprice,
                                     'n': self.asks.n_orders,
                                     'lob':self.asks.lob_anon}
                if verbose:
                        print('publish_lob: t=%d' % time)
                        print('BID_lob=%s' % public_data['bids']['lob'])
                        print('ASK_lob=%s' % public_data['asks']['lob'])
                return public_data






##################--Traders below here--#############


# Trader superclass
# all Traders have a trader id, bank balance, blotter, and list of orders to execute
class Trader:

        def __init__(self, ttype, tid, balance):
                self.ttype = ttype
                self.tid = tid
                self.balance = balance
                self.blotter = []
                self.orders = []
                self.willing = 1
                self.able = 1
                self.lastquote = None


        def __str__(self):
                return '[TID %s type %s balance %s blotter %s orders %s]' % (self.tid, self.ttype, self.balance, self.blotter, self.orders)


        def add_order(self, order):
                # in this version, trader has at most one order,
                # if allow more than one, this needs to be self.orders.append(order)
                self.orders = [order]


        def del_order(self, order):
                # this is lazy: assumes each trader has only one order with quantity=1, so deleting sole order
                # CHANGE TO DELETE THE HEAD OF THE LIST AND KEEP THE TAIL
                self.orders = []


        def bookkeep(self, trade, order, verbose,store_profits):

                outstr = '%s (%s) bookkeeping: orders=' % (self.tid, self.ttype)
                for order in self.orders: outstr = outstr + str(order)

                self.blotter.append(trade)  # add trade record to trader's blotter
                # NB What follows is **LAZY** -- assumes all orders are quantity=1
                transactionprice = trade['price']
                if self.orders[0].otype == 'Bid':
                        profit = self.orders[0].price - transactionprice
                else:
                        profit = transactionprice - self.orders[0].price
                self.balance += profit
                if verbose: print('%s profit=%d balance=%d ' % (outstr, profit, self.balance))
                
                # if self.ttype == "AA" and profit < 0:
                #     pdb.set_trace()

                if store_profits:
                    profit_breakdown = {'time':trade['time'], 'limit':self.orders[0].price, 'transactionprice':transactionprice, 'profit':profit, 'balance':self.balance, 'orderowner':order.tid}
                    trader_utils.store_profits(self,profit_breakdown)
                
                self.del_order(order)  # delete the order


        # specify how trader responds to events in the market
        # this is a null action, expect it to be overloaded with clever things by specific algos
        def respond(self, time, lob, trade, verbose):
                return None




# Trader subclass Giveaway
# even dumber than a ZI-U: just give the deal away
# (but never makes a loss)
class Trader_Giveaway(Trader):

        def getorder(self, time, countdown, lob):
                if len(self.orders) < 1:
                        order = None
                else:
                        quoteprice = self.orders[0].price
                        self.lastquote = quoteprice
                        order = Order(self.tid,
                                    self.orders[0].otype,
                                    quoteprice,
                                    self.orders[0].qty,
                                    time)
                return order



# Trader subclass ZI-C
# After Gode & Sunder 1993
class Trader_ZIC(Trader):

        def getorder(self, time, countdown, lob):
                if len(self.orders) < 1:
                        # no orders: return NULL
                        order = None
                else:
                        minprice = lob['bids']['worst']
                        maxprice = lob['asks']['worst']
                        limit = self.orders[0].price
                        otype = self.orders[0].otype
                        if otype == 'Bid':
                                quoteprice = random.randint(minprice, limit)
                        else:
                                quoteprice = random.randint(limit, maxprice)
                                # NB should check it == 'Ask' and barf if not
                        order = Order(self.tid, otype, quoteprice, self.orders[0].qty, time)

                return order


# Trader subclass Shaver
# shaves a penny off the best price
# if there is no best price, creates "stub quote" at system max/min
class Trader_Shaver(Trader):

        def getorder(self, time, countdown, lob):
                if len(self.orders) < 1:
                        order = None
                else:
                        limitprice = self.orders[0].price
                        otype = self.orders[0].otype
                        if otype == 'Bid':
                                if lob['bids']['n'] > 0:
                                        quoteprice = lob['bids']['best'] + 1
                                        if quoteprice > limitprice :
                                                quoteprice = limitprice
                                else:
                                        quoteprice = lob['bids']['worst']
                        else:
                                if lob['asks']['n'] > 0:
                                        quoteprice = lob['asks']['best'] - 1
                                        if quoteprice < limitprice:
                                                quoteprice = limitprice
                                else:
                                        quoteprice = lob['asks']['worst']
                        self.lastquote = quoteprice
                        order = Order(self.tid, otype, quoteprice, self.orders[0].qty, time)

                return order

class Trader_Shaver_Plus(Trader):

        def getorder(self, time, countdown, lob):
                if len(self.orders) < 1:
                        order = None
                else:
                        limitprice = self.orders[0].price
                        otype = self.orders[0].otype
                        if otype == 'Bid':
                                if lob['bids']['n'] > 0:
                                        quoteprice = lob['bids']['best'] + ((100/countdown)+1)
                                        if quoteprice > limitprice :
                                                quoteprice = limitprice
                                else:
                                        quoteprice = lob['bids']['worst']
                        else:
                                if lob['asks']['n'] > 0:
                                        quoteprice = lob['asks']['best'] - ((100/countdown)+1)
                                        if quoteprice < limitprice:
                                                quoteprice = limitprice
                                else:
                                        quoteprice = lob['asks']['worst']
                        self.lastquote = quoteprice
                        order = Order(self.tid, otype, quoteprice, self.orders[0].qty, time)

                return order

# Trader subclass Sniper
# Based on Shaver,
# "lurks" until time remaining < threshold% of the trading session
# then gets increasing aggressive, increasing "shave thickness" as time runs out
class Trader_Sniper(Trader):

        def getorder(self, time, countdown, lob):
                lurk_threshold = 0.2
                shavegrowthrate = 3
                shave = int(1.0 / (0.01 + countdown / (shavegrowthrate * lurk_threshold)))
                if (len(self.orders) < 1) or (countdown > lurk_threshold):
                        order = None
                else:
                        limitprice = self.orders[0].price
                        otype = self.orders[0].otype

                        if otype == 'Bid':
                                if lob['bids']['n'] > 0:
                                        quoteprice = lob['bids']['best'] + shave
                                        if quoteprice > limitprice :
                                                quoteprice = limitprice
                                else:
                                        quoteprice = lob['bids']['worst']
                        else:
                                if lob['asks']['n'] > 0:
                                        quoteprice = lob['asks']['best'] - shave
                                        if quoteprice < limitprice:
                                                quoteprice = limitprice
                                else:
                                        quoteprice = lob['asks']['worst']
                        self.lastquote = quoteprice
                        order = Order(self.tid, otype, quoteprice, self.orders[0].qty, time)

                return order




# Trader subclass ZIP
# After Cliff 1997
class Trader_ZIP(Trader):

        # ZIP init key param-values are those used in Cliff's 1997 original HP Labs tech report
        # NB this implementation keeps separate margin values for buying & sellling,
        #    so a single trader can both buy AND sell
        #    -- in the original, traders were either buyers OR sellers

        def __init__(self, ttype, tid, balance):
                self.ttype = ttype
                self.tid = tid
                self.balance = balance
                self.blotter = []
                self.orders = []
                self.job = None  # this gets switched to 'Bid' or 'Ask' depending on order-type
                self.active = False  # gets switched to True while actively working an order
                self.prev_change = 0  # this was called last_d in Cliff'97
                self.beta = 0.1 + 0.4 * random.random()
                self.momntm = 0.1 * random.random()
                self.ca = 0.05  # self.ca & .cr were hard-coded in '97 but parameterised later
                self.cr = 0.05
                self.margin = None  # this was called profit in Cliff'97
                self.margin_buy = -1.0 * (0.05 + 0.3 * random.random())
                self.margin_sell = 0.05 + 0.3 * random.random()
                self.price = None
                self.limit = None
                # memory of best price & quantity of best bid and ask, on LOB on previous update
                self.prev_best_bid_p = None
                self.prev_best_bid_q = None
                self.prev_best_ask_p = None
                self.prev_best_ask_q = None


        def getorder(self, time, countdown, lob):
                if len(self.orders) < 1:
                        self.active = False
                        order = None
                else:
                        self.active = True
                        self.limit = self.orders[0].price
                        self.job = self.orders[0].otype
                        if self.job == 'Bid':
                                # currently a buyer (working a bid order)
                                self.margin = self.margin_buy
                        else:
                                # currently a seller (working a sell order)
                                self.margin = self.margin_sell
                        quoteprice = int(self.limit * (1 + self.margin))
                        self.price = quoteprice

                        order = Order(self.tid, self.job, quoteprice, self.orders[0].qty, time)

                return order


        # update margin on basis of what happened in market
        def respond(self, time, lob, trade, verbose):
                # ZIP trader responds to market events, altering its margin
                # does this whether it currently has an order to work or not

                def target_up(price):
                        # generate a higher target price by randomly perturbing given price
                        ptrb_abs = self.ca * random.random()  # absolute shift
                        ptrb_rel = price * (1.0 + (self.cr * random.random()))  # relative shift
                        target = int(round(ptrb_rel + ptrb_abs, 0))
# #                        print('TargetUp: %d %d\n' % (price,target))
                        return(target)


                def target_down(price):
                        # generate a lower target price by randomly perturbing given price
                        ptrb_abs = self.ca * random.random()  # absolute shift
                        ptrb_rel = price * (1.0 - (self.cr * random.random()))  # relative shift
                        target = int(round(ptrb_rel - ptrb_abs, 0))
# #                        print('TargetDn: %d %d\n' % (price,target))
                        return(target)


                def willing_to_trade(price):
                        # am I willing to trade at this price?
                        willing = False
                        if self.job == 'Bid' and self.active and self.price >= price:
                                willing = True
                        if self.job == 'Ask' and self.active and self.price <= price:
                                willing = True
                        return willing


                def profit_alter(price):
                        oldprice = self.price
                        diff = price - oldprice
                        change = ((1.0 - self.momntm) * (self.beta * diff)) + (self.momntm * self.prev_change)
                        self.prev_change = change
                        newmargin = ((self.price + change) / self.limit) - 1.0

                        if self.job == 'Bid':
                                if newmargin < 0.0 :
                                        self.margin_buy = newmargin
                                        self.margin = newmargin
                        else :
                                if newmargin > 0.0 :
                                        self.margin_sell = newmargin
                                        self.margin = newmargin

                        # set the price from limit and profit-margin
                        self.price = int(round(self.limit * (1.0 + self.margin), 0))
# #                        print('old=%d diff=%d change=%d price = %d\n' % (oldprice, diff, change, self.price))


                # what, if anything, has happened on the bid LOB?
                bid_improved = False
                bid_hit = False
                lob_best_bid_p = lob['bids']['best']
                lob_best_bid_q = None
                if lob_best_bid_p != None:
                        # non-empty bid LOB
                        lob_best_bid_q = lob['bids']['lob'][-1][1]
                        if self.prev_best_bid_p < lob_best_bid_p :
                                # best bid has improved
                                # NB doesn't check if the improvement was by self
                                bid_improved = True
                        elif trade != None and ((self.prev_best_bid_p > lob_best_bid_p) or ((self.prev_best_bid_p == lob_best_bid_p) and (self.prev_best_bid_q > lob_best_bid_q))):
                                # previous best bid was hit
                                bid_hit = True
                elif self.prev_best_bid_p != None:
                        # the bid LOB has been emptied by a hit
                                bid_hit = True

                # what, if anything, has happened on the ask LOB?
                ask_improved = False
                ask_lifted = False
                lob_best_ask_p = lob['asks']['best']
                lob_best_ask_q = None
                if lob_best_ask_p != None:
                        # non-empty ask LOB
                        lob_best_ask_q = lob['asks']['lob'][0][1]
                        if self.prev_best_ask_p > lob_best_ask_p :
                                # best ask has improved -- NB doesn't check if the improvement was by self
                                ask_improved = True
                        elif trade != None and ((self.prev_best_ask_p < lob_best_ask_p) or ((self.prev_best_ask_p == lob_best_ask_p) and (self.prev_best_ask_q > lob_best_ask_q))):
                                # trade happened and best ask price has got worse, or stayed same but quantity reduced -- assume previous best ask was lifted
                                ask_lifted = True
                elif self.prev_best_ask_p != None:
                        # the bid LOB is empty now but was not previously, so must have been hit
                                ask_lifted = True


                if verbose and (bid_improved or bid_hit or ask_improved or ask_lifted):
                        print ('B_improved', bid_improved, 'B_hit', bid_hit, 'A_improved', ask_improved, 'A_lifted', ask_lifted)


                deal = bid_hit or ask_lifted

                if self.job == 'Ask':
                        # seller
                        if deal :
                                tradeprice = trade['price']
                                if self.price <= tradeprice:
                                        # could sell for more? raise margin
                                        target_price = target_up(tradeprice)
                                        profit_alter(target_price)
                                elif ask_lifted and self.active and not willing_to_trade(tradeprice):
                                        # wouldnt have got this deal, still working order, so reduce margin
                                        target_price = target_down(tradeprice)
                                        profit_alter(target_price)
                        else:
                                # no deal: aim for a target price higher than best bid
                                if ask_improved and self.price > lob_best_ask_p:
                                        if lob_best_bid_p != None:
                                                target_price = target_up(lob_best_bid_p)
                                        else:
                                                target_price = lob['asks']['worst']  # stub quote
                                        profit_alter(target_price)

                if self.job == 'Bid':
                        # buyer
                        if deal :
                                tradeprice = trade['price']
                                if self.price >= tradeprice:
                                        # could buy for less? raise margin (i.e. cut the price)
                                        target_price = target_down(tradeprice)
                                        profit_alter(target_price)
                                elif bid_hit and self.active and not willing_to_trade(tradeprice):
                                        # wouldnt have got this deal, still working order, so reduce margin
                                        target_price = target_up(tradeprice)
                                        profit_alter(target_price)
                        else:
                                # no deal: aim for target price lower than best ask
                                if bid_improved and self.price < lob_best_bid_p:
                                        if lob_best_ask_p != None:
                                                target_price = target_down(lob_best_ask_p)
                                        else:
                                                target_price = lob['bids']['worst']  # stub quote
                                        profit_alter(target_price)


                # remember the best LOB data ready for next response
                self.prev_best_bid_p = lob_best_bid_p
                self.prev_best_bid_q = lob_best_bid_q
                self.prev_best_ask_p = lob_best_ask_p
                self.prev_best_ask_q = lob_best_ask_q


class Trader_AA(Trader):
    """ Adaptive Aggressive """

    class Marginality:
        Intra = 1
        Extra = 2
        Neutral = 3

    def greater_than(a,b):
        return a > b

    def less_than(a,b):
        return a < b

    def __init__(self, ttype, tid, balance):
        """Call Trader's init method then add extra iVars"""
        Trader.__init__(self,ttype, tid, balance)

        # Keep track of all previous transaction prices
        self.transactions = []
        
        # A value for the degree of aggressiveness
        self.r = 0
        self.agg_r = 0
        self.r_shout = 0

        self.price = None

        self.lambda_a = 0.01
        self.lambda_r = 0.02

        # A value that influences long term bidding behaviour 
        self.theta = random.random() * 0.1

        self.thetamax = 2.0
        self.thetamin = -8.0

        # How should the average be weighted
        self.ave_weight = 0.7

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
        self.alphas = []

        # Store what marginality this trader is
        self.marginality = self.Marginality.Neutral;
        self.beta1 = 0.5
        self.beta2 = 0.5

        self.offer_reject_count = 0

        # self.p_max = 1
        # self.p_min = 

        self.eta = 2.0

        # Store target price
        self.tau = None

    def __str__(self):
        if self.marginality == self.Marginality.Intra:
            marginality = "Intra"
        elif self.marginality == self.Marginality.Extra:
            marginality = "Extra"
        else:
            marginality = "None"

        return '[tid: %s job:%s limit:%s price:%s equilibrium:%s tau:%s theta:%s r:%s transactions:%s marginality:%s]' % (self.tid,self.job,self.limit, self.price, self.equilibrium, self.tau, self.theta, self.r, self.transactions, marginality)

    @classmethod
    def init_from_json(cls, data):
        trader = cls(None,None,None)
        # data = json.loads(json_string)
        for key in data:
            setattr(trader, key, data[key])
        
        return trader

    def bookkeep(self, trade, order, verbose,store_profits):
        Trader.bookkeep(self,trade, order, verbose,store_profits)
        self.offer_reject_count = 0


    def add_order(self,order):
        """ Had issues with no limit price when responding so set it here """
        Trader.add_order(self,order)

        self.limit = self.orders[0].price
        self.job = self.orders[0].otype

    def getorder(self,time,countdown,lob):
        """Use the variables we have learnt to create an order"""

        if len(self.orders) < 1:
            self.active = False
            order = None
            self.limit = None
        else:
            self.active = True

            best_bid = lob['bids']['best']
            best_ask = lob['asks']['best']
            self.limit = self.orders[0].price
            self.job = self.orders[0].otype
            
            if not best_bid:
                best_bid = bse_sys_minprice

            if not best_ask:
                best_ask = bse_sys_maxprice
            
            if len(self.transactions) < 3:
                if self.job == 'Bid':
                    ask_plus = (1 + self.lambda_r) * best_ask + self.lambda_a
                    self.price = min(self.limit,best_bid + (min(self.limit,ask_plus) - best_bid)/self.eta)
                else:# self.job == 'Ask':
                    bid_minus = (1 - self.lambda_r) * best_bid - self.lambda_a
                    self.price = max(self.limit,best_ask - (best_ask - max(self.limit,bid_minus))/self.eta)
            else:
                self.get_marginality()
                self.tau = self.calculate_target_price(self.agg_r)

                # self.get_marginality()
                # self.tau = self.calculate_target_price(self.r)
                if self.job == 'Bid':
                    if self.limit > best_bid:
                        price = math.floor(best_bid + float(self.tau - best_bid)/self.eta)
                        # Added this in due to rounding errors that were costing us £s!
                        self.price = min(self.limit,price)
                        # self.offer_reject_count += 1
                    else:
                        self.price = self.p_min
                        # self.offer_reject_count = 0
                elif self.job == 'Ask':
                    if self.limit < best_ask:
                        price = math.ceil(best_ask - float(best_ask - self.tau)/self.eta)
                        # Added this in due to rounding errors that were costing us £s!
                        self.price = max(self.limit,price)
                    else:
                        self.price = self.p_max
                        # self.offer_reject_count = 0

                self.offer_reject_count += 1

            if ((self.job == "Bid" and self.price > self.limit) or 
                (self.job == "Ask" and self.price < self.limit) ):
                pdb.set_trace()
            
            order = Order(self.tid, self.orders[0].otype, math.floor(self.price), self.orders[0].qty, time)
            # order = Order(self.tid, self.orders[0].otype, math.floor(self.limit), self.orders[0].qty, time)
        
        return order
        

    def respond(self, time, lob, trade, verbose):
        """ Learn from what just happened in the market"""
    
        # If there has been any change then recalculate the equilibrium and our marginality
        if trade and self.limit:
            self.transactions.append(trade['price'])
            # Update our estimate the new market equilibrium
            self.calculate_market_equilibrium()
            # Calculate theta from alpha
            self.theta = self.calculate_theta()

            if self.job == "Bid":
                price_to_match = lob['bids']['best']
                if not price_to_match:
                    price_to_match = self.p_min
            else:
                price_to_match = lob['asks']['best']   
                if not price_to_match:
                    price_to_match = self.p_max

            r_shout = self.calculate_r_shout(price_to_match)
            self.r = self.calculate_r(r_shout)

            # Limit the new aggressiveness to 1
            self.agg_r = min(self.r + self.offer_reject_count * 0.1, 1)

            self.get_marginality()
            self.tau = self.calculate_target_price(self.agg_r)

    def get_marginality(self):
        """Get the marginality based on the trader type and estimate of the market equilibrium"""

        if (self.job == 'Bid'):
            if self.limit > self.equilibrium:
                self.marginality  = self.Marginality.Intra
            else:
                self.marginality  = self.Marginality.Extra
        else:
            if self.limit < self.equilibrium:
                self.marginality  = self.Marginality.Intra
            else:
                self.marginality  = self.Marginality.Extra

    def calculate_market_equilibrium(self):
        """ Use a weighted average of all previous transactions to calculate the market equilibrium """
        estimate_sum = 0
        weights = 0
        # Now we want to calculate the estimate of the equilibrium price
        for i in range(len(self.transactions)):
            weight = self.ave_weight ** i
            estimate_sum += self.transactions[-(i+1)] * weight
            weights += weight

        self.equilibrium = estimate_sum / weights

    def calculate_r_shout(self, price_to_match):
        """
        Use current market estimates the work out what aggressiveness would be required to match the current price.
        Both the price and the function to solve depend on the marginality of the trader
        """           

        # Work out which direction r should move in if it results in a target price greater than the price_to_match
        if self.job == 'Ask': 
            iterate_multiplier = -1
            bid_range = self.p_max - self.limit
        else:
            iterate_multiplier = 1
            bid_range = self.limit

        r = 0
        last_target_price = 0
        target_price = self.calculate_target_price(r)

        # how close to the correct price do we want to get
        limit = 0.1
        
        i=1
        try:
            abs(target_price - price_to_match)
        except TypeError:
            self.test_instance()
            print self.limit
            print target_price
            print price_to_match
            return self.r

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
            delta = (1-self.lambda_r) * r_shout
        else:
            delta = (1+self.lambda_r) * r_shout

        new_r = self.r + self.beta1 * (delta - self.r)
        if new_r > 1: new_r = 1
        if new_r < -1: new_r = -1

        return new_r


    def newton(self):
        # runs Newton-Raphson to find theta_est (the value of theta that makes the 1st 
        # derivative of eqn(3) continuous)
        theta_est = self.theta
        rightHside = ((self.theta * (self.limit - self.equilibrium)) / float(math.exp(self.theta) - 1));
        i = 0
        maxNewtonItter = 10
        maxNewtonError = 0.0001

        try:
            while i <= maxNewtonItter:
                eX = math.exp(theta_est)
                eXminOne = eX - 1
                fofX = (((theta_est * self.equilibrium) / float(eXminOne)) - rightHside)
                if abs(fofX) <= maxNewtonError:
                    break
                dfofX = ((self.equilibrium / eXminOne) - ((eX * self.equilibrium * theta_est) / float(eXminOne * eXminOne)))
                theta_est = (theta_est - (fofX / float(dfofX)));
                i += 1
            if theta_est == 0.0: theta_est += 0.000001
        except Exception:
            # pdb.set_trace()
            theta_est = 0.000001
        return theta_est

    def newtonsell(self):
        # runs Newton-Raphson to find theta_est (the value of theta that makes the 1st 
        # derivative of eqn(3) continuous)
        theta_est = self.theta
        rightHside = ((self.theta * (self.equilibrium - self.limit)) / float(math.exp(self.theta) - 1))
        i = 0
        maxNewtonItter = 10
        maxNewtonError = 0.0001

        try:
            while i <= maxNewtonItter:
                eX = math.exp(theta_est)
                eXminOne = eX - 1
                fofX = (((theta_est * self.equilibrium) / float(eXminOne)) - rightHside)
                if abs(fofX) <= maxNewtonError:
                    break
                dfofX = (((self.p_max - self.equilibrium) / eXminOne) - ((eX * (self.p_max - self.equilibrium) * theta_est) / float(eXminOne * eXminOne)))
                theta_est = (theta_est - (fofX / float(dfofX)));
                i += 1
            if theta_est == 0.0: theta_est += 0.000001
        except Exception:
            # pdb.set_trace()
            theta_est = 0.000001
        return theta_est
    
    def calculate_target_price(self,r):
        """ 

        Using the current traders statistics and a set aggressiveness (r), calculate the correct target_price.
        This takes into consideration: equilibrium approximation, limit price, trader job, marginality (a different formula for each) and theta (long term learning)
        r has been left as an argument so that r can be tested to approximate r_shout

        *** WITH ALL OF THESE EQUATIONS WE HAVE NEGATED r SO THAT AGRESSIVENESS IS POSITIVE AND THE DIAGRAMS MATCH THOSE IN THE PAPER ***

        """

        if r > 1 or r < -1:
            assert('r should be in the range (-1,1)')

        if self.marginality == self.Marginality.Intra:
            if self.job == 'Bid':
                if r <= 0:
                    # orig
                    # return self.equilibrium * (1 - r * exp(self.theta * (r-1)))
                    # return self.equilibrium * (1 + r * exp(self.theta * (-r-1)))
                    theta_underscore = ((self.equilibrium * exp(-self.theta)) / (self.limit - self.equilibrium + 0.00001)) - 1
                    # From Trader_AA.py off github
                    theta_underscore = self.newton()

                    if theta_underscore > self.thetamax:
                        theta_underscore = self.thetamax
                    if theta_underscore < self.thetamin:
                        theta_underscore = self.thetamin

                    # print theta_underscore
                    try:
                        return self.equilibrium * (1 - (math.exp(-r * theta_underscore) - 1) / float(math.exp(theta_underscore) - 1))
                    except:
                        pdb.set_trace()
                        return self.tau
                elif r > 0:
                    theta_underscore = ((self.equilibrium * exp(-self.theta)) / (self.limit - self.equilibrium)) - 1
                    # return (self.limit - self.equilibrium) * (1 - (-r+1) * exp(-r * theta_underscore)) + self.equilibrium

                    # From Trader_AA.py off github
                    return (self.equilibrium + (self.limit - self.equilibrium) * ((math.exp(r * self.theta) - 1) / float(math.exp(self.theta) - 1)))
            else: # self.job == 'Ask':
                if r <= 0:
                    # return self.equilibrium + (self.p_max - self.equilibrium) * (-r)*exp(-(r+1)*self.theta)

                    # From Trader_AA.py off github
                    # theta_underscore = log((self.p_max - self.equilibrium)/(self.equilibrium-self.limit)) - self.theta
                    theta_underscore = self.newtonsell()
                    
                    if theta_underscore > self.thetamax:
                        theta_underscore = self.thetamax
                    if theta_underscore < self.thetamin:
                        theta_underscore = self.thetamin

                    return self.equilibrium + (self.p_max - self.equilibrium) * ((math.exp(-r * theta_underscore) - 1) / (math.exp(theta_underscore) - 1))
                elif r > 0:
                    # theta_underscore = log((self.p_max - self.equilibrium)/(self.equilibrium-self.limit)) - self.theta
                    # return self.equilibrium + (self.equilibrium - self.limit) * (-r) * exp((-r+1)*theta_underscore)

                    # From Trader_AA.py off github
                    return self.limit + (self.equilibrium - self.limit) * (1 - (math.exp(r * self.theta) - 1) / float(math.exp(self.theta) - 1))

        else: # self.marginality == Marginality.Extra
            if self.job == 'Bid':
                if r < 0:
                    # return self.limit * (1 + r * exp(-self.theta * (r+1)))

                    # From Trader_AA.py off github                    
                    return self.limit * (1 - (math.exp(-r * self.theta) - 1) / float(math.exp(self.theta) - 1))
                elif r >= 0:
                    return self.limit
            else: # self.job == 'Ask':
                if r < 0:
                    # return self.limit + (self.p_max - self.limit) * (-r) * exp(-self.theta * (r+1))

                    # From Trader_AA.py off github                    
                    return self.limit + (self.p_max - self.limit) * ((math.exp(-r * self.theta) - 1) / float(math.exp(self.theta) - 1))
                elif r >= 0:
                    return self.limit

    def calculate_theta(self):
        thetastar = self.calculate_thetastar()
        return self.theta + self.beta2*(thetastar - self.theta)

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

    def test_instance(trader):
        N = 40
        targets = zeros(N)
        rs = zeros(N)
        for i in range(N):
            r = -1 + 2 * float(i) / N

            targets[i] = trader.calculate_target_price(r)
            rs[i] = r

        if trader.job == "Bid":
            plot(rs,targets, 'r-')    
            plot(rs,ones(N) * trader.limit,'r--')
        else:
            plot(rs,targets, 'b-')
            plot(rs,ones(N) * trader.limit,'b--')

        if trader.equilibrium:
            plot(rs,ones(N) * trader.equilibrium, 'k--')

        show()


##########################---trader-types have all been defined now--################




##########################---Below lies the experiment/test-rig---##################



# trade_stats()
# dump CSV statistics on exchange data and trader population to file for later analysis
# this makes no assumptions about the number of types of traders, or
# the number of traders of any one type -- allows either/both to change
# between successive calls, but that does make it inefficient as it has to
# re-analyse the entire set of traders on each call
def trade_stats(expid, traders, dumpfile, time, lob):
        #do_trade_stats(expid, traders, dumpfile, time, lob, 'A','All');
        do_trade_stats_new(expid, traders, dumpfile, time, lob,'All');
        # do_trade_stats(expid, traders, dumpfile, time, lob, 'B','Buyers');
        # do_trade_stats(expid, traders, dumpfile, time, lob, 'S','Sellers');


        #if lob['bids']['best'] != None :
        #        dumpfile.write('%d, ' % (lob['bids']['best']))
        #else:
        #        dumpfile.write('N, ')
        #if lob['asks']['best'] != None :
        #        dumpfile.write('%d, '% (lob['asks']['best']))
        #else:
        #        dumpfile.write('N, ')

        dumpfile.write('\n');

def do_trade_stats(expid, traders, dumpfile, time, lob,label):
    trader_types = {}
    for t in traders:
        job = label[0]
        if job == 'A' or traders[t].tid[0] == job:
            ttype = traders[t].ttype
            if ttype in trader_types.keys():
                t_balance = trader_types[ttype]['balance_sum'] + traders[t].balance
                n = trader_types[ttype]['n'] + 1
            else:
                t_balance = traders[t].balance
                n = 1
            trader_types[ttype]={'n':n, 'balance_sum':t_balance}
    
    dumpfile.write('\n%s, %06d, %s, '% (expid, time, label))
    for ttype in sorted(list(trader_types.keys())):
        n = trader_types[ttype]['n']
        s = trader_types[ttype]['balance_sum']
        dumpfile.write('%s, %d, %d, %f, ' % (ttype, s, n, s/float(n)))

def do_trade_stats_new(expid, traders, dumpfile, time, lob, label):
    trader_types = {}
    for t in traders:
        job = label[0];
        if job == 'A' or traders[t].tid[0] == job: 
            ttype = traders[t].ttype
            if ttype in trader_types.keys():
                t_balance = trader_types[ttype]['balance_sum'] + traders[t].balance
                n = trader_types[ttype]['n'] + 1
            else:
                t_balance = traders[t].balance
                n = 1
            trader_types[ttype]={'n':n, 'balance_sum':t_balance}

    if expid[-2:] == '01':
        for ttype in sorted(list(trader_types.keys())):
            dumpfile.write('%s, ' % ttype)
        dumpfile.write('\n')

    # dumpfile.write('%s, %s, '% (job, expid[-1]))

    for ttype in sorted(list(trader_types.keys())):
        n = trader_types[ttype]['n']
        s = trader_types[ttype]['balance_sum']
        dumpfile.write('%f, ' % (s/float(n)))

def do_trade_stats_profits(expid, traders, dumpfile, time, lob,label):
    dumpfile.write('%s\n' % label)
    for t in traders:
        if label[0] == 'A' or traders[t].tid[0] == label[0]:
            ttype = traders[t].ttype
            dumpfile.write('%s,%s\n'% (ttype, traders[t].balance))


# create a bunch of traders from traders_spec
# returns tuple (n_buyers, n_sellers)
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
                elif robottype == 'AA':
                        return Trader_AA('AA', name, 0.00)
                elif robottype == 'SHVP':
                        return Trader_Shaver_Plus('SHVP', name, 0.00)
                else:
                        sys.exit('FATAL: don\'t know robot type %s\n' % robottype)


        def shuffle_traders(ttype_char, n, traders):
                for swap in range(n):
                        t1 = (n - 1) - swap
                        t2 = random.randint(0, t1)
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
                        tname = 'B%02d' % n_buyers  # buyer i.d. string
                        traders[tname] = trader_type(ttype, tname)
                        n_buyers = n_buyers + 1

        if n_buyers < 1:
                sys.exit('FATAL: no buyers specified\n')

        if shuffle: shuffle_traders('B', n_buyers, traders)


        n_sellers = 0
        for ss in traders_spec['sellers']:
                ttype = ss[0]
                for s in range(ss[1]):
                        tname = 'S%02d' % n_sellers  # buyer i.d. string
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



# customer_orders(): allocate orders to traders
# parameter "os" is order schedule
# os['timemode'] is either 'periodic', 'drip-fixed', 'drip-jitter', or 'drip-poisson'
# os['interval'] is number of seconds for a full cycle of replenishment
# drip-poisson sequences will be normalised to ensure time of last replenisment <= interval
# parameter "pending" is the list of future orders (if this is empty, generates a new one from os)
# revised "pending" is the returned value
#
# if a supply or demand schedule mode is "random" and more than one range is supplied in ranges[],
# then each time a price is generated one of the ranges is chosen equiprobably and
# the price is then generated uniform-randomly from that range
#
# if len(range)==2, interpreted as min and max values on the schedule, specifying linear supply/demand curve
# if len(range)==3, first two vals are min & max, third value should be a function that generates a dynamic price offset
#                   -- the offset value applies equally to the min & max, so gradient of linear sup/dem curve doesn't vary
# if len(range)==4, the third value is function that gives dynamic offset for schedule min,
#                   and fourth is a function giving dynamic offset for schedule max, so gradient of sup/dem linear curve can vary
#
# the interface on this is a bit of a mess... could do with refactoring


def customer_orders(time, last_update, traders, trader_stats, os, pending, verbose):


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

        

        def getorderprice(i, sched, n, mode, issuetime):
                # does the first schedule range include optional dynamic offset function(s)?
                if len(sched[0]) > 2:
                        offsetfn = sched[0][2]
                        if callable(offsetfn):
                                # same offset for min and max
                                offset_min = offsetfn(issuetime)
                                offset_max = offset_min
                        else:
                                sys.exit('FAIL: 3rd argument of sched in getorderprice() not callable')
                        if len(sched[0]) > 3:
                                # if second offset function is specfied, that applies only to the max value
                                offsetfn = sched[0][3]
                                if callable(offsetfn):
                                        # this function applies to max
                                        offset_max = offsetfn(issuetime)
                                else:
                                        sys.exit('FAIL: 4th argument of sched in getorderprice() not callable')
                else:
                        offset_min = 0.0
                        offset_max = 0.0

                pmin = sysmin_check(offset_min + min(sched[0][0], sched[0][1]))
                pmax = sysmax_check(offset_max + max(sched[0][0], sched[0][1]))
                prange = pmax - pmin
                stepsize = prange / (n - 1)
                halfstep = round(stepsize / 2.0)

                if mode == 'fixed':
                        orderprice = pmin + int(i * stepsize) 
                elif mode == 'jittered':
                        orderprice = pmin + int(i * stepsize) + random.randint(-halfstep, halfstep)
                elif mode == 'random':
                        if len(sched) > 1:
                                # more than one schedule: choose one equiprobably
                                s = random.randint(0, len(sched) - 1)
                                pmin = sysmin_check(min(sched[s][0], sched[s][1]))
                                pmax = sysmax_check(max(sched[s][0], sched[s][1]))
                        orderprice = random.randint(pmin, pmax)
                else:
                        sys.exit('FAIL: Unknown mode in schedule')
                orderprice = sysmin_check(sysmax_check(orderprice))
                return orderprice



        def getissuetimes(n_traders, mode, interval, shuffle, fittointerval):
                interval = float(interval)
                if n_traders < 1:
                        sys.exit('FAIL: n_traders < 1 in getissuetime()')
                elif n_traders == 1:
                        tstep = interval
                else:
                        tstep = interval / (n_traders - 1)
                arrtime = 0
                issuetimes = []
                for t in range(n_traders):
                        if mode == 'periodic':
                                arrtime = interval
                        elif mode == 'drip-fixed':
                                arrtime = t * tstep
                        elif mode == 'drip-jitter':
                                arrtime = t * tstep + tstep * random.random()
                        elif mode == 'drip-poisson':
                                # poisson requires a bit of extra work
                                interarrivaltime = random.expovariate(n_traders / interval)
                                arrtime += interarrivaltime
                        else:
                                sys.exit('FAIL: unknown time-mode in getissuetimes()')
                        issuetimes.append(arrtime) 
                        
                # at this point, arrtime is the last arrival time
                if fittointerval and ((arrtime > interval) or (arrtime < interval)):
                        # generated sum of interarrival times longer than the interval
                        # squish them back so that last arrival falls at t=interval
                        for t in range(n_traders):
                                issuetimes[t] = interval * (issuetimes[t] / arrtime)
                # optionally randomly shuffle the times
                if shuffle:
                        for t in range(n_traders):
                                i = (n_traders - 1) - t
                                j = random.randint(0, i)
                                tmp = issuetimes[i]
                                issuetimes[i] = issuetimes[j]
                                issuetimes[j] = tmp
                return issuetimes
        

        def getschedmode(time, os):
                got_one = False
                for sched in os:
                        if (sched['from'] <= time) and (time < sched['to']) :
                                # within the timezone for this schedule
                                schedrange = sched['ranges']
                                mode = sched['stepmode']
                                got_one = True
                                exit  # jump out the loop -- so the first matching timezone has priority over any others
                if not got_one:
                        sys.exit('Fail: time=%5.2f not within any timezone in os=%s' % (time, os))
                return (schedrange, mode)
        

        n_buyers = trader_stats['n_buyers']
        n_sellers = trader_stats['n_sellers']
        n_traders = n_buyers + n_sellers

        shuffle_times = True


        if len(pending) < 1:
                # list of pending (to-be-issued) customer orders is empty, so generate a new one
                new_pending = []

                # demand side (buyers)
                issuetimes = getissuetimes(n_buyers, os['timemode'], os['interval'], shuffle_times, True)
                
                ordertype = 'Bid'
                (sched, mode) = getschedmode(time, os['dem'])             
                for t in range(n_buyers):
                        issuetime = time + issuetimes[t]
                        tname = 'B%02d' % t
                        orderprice = getorderprice(t, sched, n_buyers, mode, issuetime)
                        order = Order(tname, ordertype, orderprice, 1, issuetime)
                        new_pending.append(order)
                        
                # supply side (sellers)
                issuetimes = getissuetimes(n_sellers, os['timemode'], os['interval'], shuffle_times, True)
                ordertype = 'Ask'
                (sched, mode) = getschedmode(time, os['sup'])
                for t in range(n_sellers):
                        issuetime = time + issuetimes[t]
                        tname = 'S%02d' % t
                        orderprice = getorderprice(t, sched, n_sellers, mode, issuetime)
                        order = Order(tname, ordertype, orderprice, 1, issuetime)
                        new_pending.append(order)
        else:
                # there are pending future orders: issue any whose timestamp is in the past
                new_pending = []
                for order in pending:
                        if order.time < time:
                                # this order should have been issued by now
                                # issue it to the trader
                                tname = order.tid
                                traders[tname].add_order(order)
                                if verbose: print('New order: %s' % order)
                                # and then don't add it to new_pending (i.e., delete it)
                        else:
                                # this order stays on the pending list
                                new_pending.append(order)

        return new_pending



# one session in the market
def market_session(sess_id, starttime, endtime, trader_spec, order_schedule, dumpfile, dump_each_trade,store_traders,store_profits,store_lob_orders=False,store_trader_orders=False):
        # initialise the exchange
        exchange = Exchange()

        orders_verbose = False
        lob_verbose = False
        process_verbose = False
        respond_verbose = False
        bookkeep_verbose = False
        populate_verbose = False

        # create a bunch of traders
        traders = {}
        trader_stats = populate_market(trader_spec, traders, True, False)

        # timestep set so that can process all traders in one second
        # NB minimum interarrival time of customer orders may be much less than this!! 
        timestep = 1.0 / float(trader_stats['n_buyers'] + trader_stats['n_sellers'])
        
        duration = float(endtime - starttime)

        last_update = -1.0

        time = starttime

        pending_orders = []       

        while time < endtime:

                # how much time left, as a percentage?
                time_left = (endtime - time) / duration

                # print('%s; t=%08.2f (%4.1f) ' % (sess_id, time, time_left*100))
                trade = None

                pending_orders = customer_orders(time, last_update, traders, trader_stats,
                                                 order_schedule, pending_orders, orders_verbose)

                # get an order (or None) from a randomly chosen trader
                tid = list(traders.keys())[random.randint(0, len(traders) - 1)]
                order = traders[tid].getorder(time, time_left, exchange.publish_lob(time, lob_verbose))
                
                if traders[tid].ttype == "AA" and order and store_trader_orders:
                    trader_utils.dump_trader_order(traders[tid],time,order)
                    
                if order != None:
                        # send order to exchange
                        trade = exchange.process_order2(time, order, process_verbose)
                        if store_lob_orders:
                            trader_utils.store_lob_orders(exchange)

                        if trade != None:

                                # trade occurred,
                                # so the counterparties update order lists and blotters
                                # trader_utils.store_trade(order,trade,traders[trade['party1']],traders[trade['party2']],time)
                                
                                # if traders[trade['party1']].ttype == "AA":
                                #     trader_utils.dump_trader(traders[trade['party1']],time,order)

                                # if traders[trade['party2']].ttype == "AA":
                                #     trader_utils.dump_trader(traders[trade['party2']],time,order)

                                traders[trade['party1']].bookkeep(trade, order, bookkeep_verbose,store_profits)
                                traders[trade['party2']].bookkeep(trade, order, bookkeep_verbose,store_profits)
                                if dump_each_trade: trade_stats(sess_id, traders, tdump, time, exchange.publish_lob(time, lob_verbose))

                        # traders respond to whatever happened
                        lob = exchange.publish_lob(time, lob_verbose)
                        for t in traders:
                                # NB respond just updates trader's internal variables
                                # doesn't alter the LOB, so processing each trader in
                                # seqeunce (rather than random/shuffle) isn't a problem
                                traders[t].respond(time, lob, trade, respond_verbose)

                                # if traders[t].ttype == "AA" and store_traders:
                                #     trader_utils.dump_trader(traders[t],time,None)

                time = time + timestep


        # end of an experiment -- dump the tape
        exchange.tape_dump('output/transactions.csv', 'w', 'keep')

        # write trade_stats for this experiment NB end-of-session summary only
        trade_stats(sess_id, traders, dumpfile, time, exchange.publish_lob(time, lob_verbose))

        return traders
#############################
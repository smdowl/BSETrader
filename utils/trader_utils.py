import json

def trader_filepath():
    return 'output/trader.json'

def profit_filepath():
    return 'output/trader_profits.json'

def trades_filepath():
    return 'output/trades.json'

def wipe_trader_files(evolution):
    f = open(trader_filepath(),'w')
    f.close()
    f = open(profit_filepath(),'w')
    f.close()

    if evolution:
        f = open(trades_filepath(),'w')
        f.close()

def dump_trader(trader,time,order):
    """ Output the current state of the trader """
    with open(trader_filepath(),'a') as f:
        obj_dict = trader.__dict__.copy()
        obj_dict["time"] = time
        if order:
            obj_dict["order"] = order.__dict__.copy()

        if obj_dict['orders']:
            order_dicts = []
            for order in obj_dict['orders']:
                new_order = order.__dict__.copy()
                order_dicts.append(new_order)

            obj_dict['orders'] = order_dicts
        json_string = json.dumps(obj_dict)
        f.write(json_string + "\n")

def store_profits(trader,profit_breakdown):
    """ Output the profit of the trader at every point in time """
    profit_breakdown['tid'] = trader.tid
    profit_breakdown['ttype'] = trader.ttype
    
    with open(profit_filepath(),'a') as f:
        json_string = json.dumps(profit_breakdown)
        f.write(json_string + "\n")

def store_trade(order,trade,trader1,trader2,time):
    output = {}
    order_dict = order.__dict__.copy()
    output['order'] = order_dict
    output['trader1'] = {'tid':trader1.tid,'ttype':trader1.ttype,'limit':trader1.orders[0].price}
    output['trader2'] = {'tid':trader2.tid,'ttype':trader2.ttype,'limit':trader2.orders[0].price}
    output['trade'] = trade
    output['time'] = time
    with open(trades_filepath(),'a') as f:
        json_string = json.dumps(output)
        f.write(json_string + "\n")
        




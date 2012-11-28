import json

def __create_filepath(trader):
    return 'output/trader%s.json' % trader.tid

def wipe_trader_file(trader):
    f = open(__create_filepath(trader),'w')
    f.close

def dump_trader(trader,time):
    """ Output the current state of the trader """
    with open(__create_filepath(trader),'a') as f:
        obj_dict = trader.__dict__.copy()
        obj_dict["time"] = time

        if obj_dict['orders']:
            order_dicts = []
            for order in obj_dict['orders']:
                new_order = order.__dict__
                order_dicts.append(new_order)

            obj_dict['orders'] = order_dicts
        json_string = json.dumps(obj_dict)
        f.write(json_string + "\n")
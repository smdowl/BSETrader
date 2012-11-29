import json
import TraderUtils

def import_profits():
    profits = {}
    with open(TraderUtils.profit_filepath()) as f:
        for line in f.readlines():
            line_dictionary = json.loads(line)
            
            tid = line_dictionary['tid']
            if tid in profits:
                profits[tid].append(line_dictionary)
            else:
                profits[tid] = [line_dictionary]
                
    return profits

def plot_profits():
    profits = import_profits()
    print profits

plot_profits()
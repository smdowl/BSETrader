from BSE import market_session
from BSE import Trader
import math,sys,pdb


from utils.trader_utils import wipe_trader_files
from utils import simulation_utils

store_traders = False
dump_all = False
vary_parameters = False
evolution = False
knock_out = True
store_profits = False
store_trader_orders = True
store_lob_orders = False
start_time = 0

# schedule_offsetfn returns time-dependent offset on schedule prices
def schedule_offsetfn(t):
        pi2 = math.pi * 2
        c = math.pi * 3000
        wavelength = t / c
        gradient = 100 * t / (c / pi2)
        amplitude = 100 * t / (c / pi2)
        offset = gradient + amplitude * math.sin(wavelength * t)
        return int(round(offset, 0))

def run_standard_simulation(n_trials,end_time, traders_spec, order_sched,m):
        wipe_trader_files(evolution)
        tdump=open('output/avg_balance'+str(m)+'.csv','w')
        #tdump.write(end_time, order_sched['sup'][0]['stepmode'], order_sched['timemode'])

        trial = 1
        while (trial<(n_trials+1)):
               trial_id = 'trial%04d' % trial
               market_session(trial_id, start_time, end_time, traders_spec, order_sched, tdump, dump_all,store_traders,store_profits,store_lob_orders,store_trader_orders)
               tdump.flush()
               trial = trial + 1
               print trial_id + " done!" 
        tdump.close()

        #sys.exit('Done Now')

def run_evolution_simulation(n_trials,end_time, traders_spec, order_sched, knock_out,rnd):
    wipe_trader_files(evolution)
    tdump=open('output/avg_balance.csv','w')
        
    trader_types = []
    counts = []
    for (trader,count) in buyers_spec:
        trader_types.append(trader)
        counts.append(count)
    evolution_output = [counts]

    trial = 1
    while (trial<(n_trials+1)):
        trial_id = 'trial%04d' % trial
        traders = market_session(trial_id, start_time, end_time, traders_spec, order_sched, tdump, dump_all,store_traders,store_profits,store_lob_orders,store_trader_orders)

        best_balance = -float('inf')
        worst_balance = float('inf')

        for trader in traders.values():
            if trader.balance > best_balance:
                best_trader = trader.tid
                best_balance = trader.balance
            elif trader.balance < worst_balance:
                worst_trader = trader.tid
                worst_balance = trader.balance
        
        i = 0
        counts = []
        number_still_in = 0
        for (trader,count) in buyers_spec:
            if not knock_out and trader == traders[best_trader].ttype:
                count += 1

            if trader == traders[worst_trader].ttype:
                count -= 1
            
            if count > 0:
                number_still_in += 1

            buyers_spec[i] = (trader,count)
            counts.append(count)
            i += 1
        evolution_output.append(counts)
            
        if number_still_in == 1:
            break

        sellers_spec = buyers_spec
        traders_spec = {'sellers':sellers_spec, 'buyers':buyers_spec}

            # tdump.flush()
        print str(trial) + " done!" 
        trial = trial + 1
    simulation_utils.store_simulation_data(trader_types,evolution_output,rnd)
    tdump.close()
        

if __name__ == "__main__":
        # #        range1 = (10, 190, schedule_offsetfn)
        # #        range2 = (200,300, schedule_offsetfn)

        # #        supply_schedule = [ {'from':start_time, 'to':duration/3, 'ranges':[range1], 'stepmode':'fixed'},
        # #                            {'from':duration/3, 'to':2*duration/3, 'ranges':[range2], 'stepmode':'fixed'},
        # #                            {'from':2*duration/3, 'to':end_time, 'ranges':[range1], 'stepmode':'fixed'}
        # #                          ]
        
        durationmodes = {'short':150,'medium':450,'long':700}
        
        dmodes = ['short','medium','long']
        stepmodes = ['fixed', 'random', 'jittered']
        timemodes = ['periodic', 'drip-fixed', 'drip-jitter','drip-poisson']

        default = ['medium','jittered','drip-fixed']

        trader_count = 9
        traders = ['GVWY','SHVR','ZIC','ZIP','AA','AAA']

        n_trials = 1
        n_rnds = 2
        m = 1

        if vary_parameters:
        # set up parameters for the session
            for i in range(len(durationmodes)):
                for j in range(len(stepmodes)):
                    for k in range(len(timemodes)):
                        end_time = durationmodes[dmodes[i]]
                        stepmode = stepmodes[j]
                        timemode = timemodes[k]

                        print m, end_time, stepmode, timemode

                        duration = end_time - start_time

                        range1 = (95,95)
                        #range1 = (95, 95, schedule_offsetfn)
                        supply_schedule = [ {'from':start_time, 'to':end_time, 'ranges':[range1], 'stepmode':stepmode}]

                        range2 = (105,105)
                        #range2 = (105, 105, schedule_offsetfn)
                        demand_schedule = [ {'from':start_time, 'to':end_time, 'ranges':[range2], 'stepmode':stepmode}]

                        order_sched = {'sup':supply_schedule, 'dem':demand_schedule, 'interval':30, 'timemode':timemode}

                        buyers_spec = [(trader,trader_count) for trader in traders]
                        # buyers_spec = [('GVWY',trader_count),('SHVR',trader_count),('ZIC',trader_count),('ZIP',trader_count),('AA',trader_count)]
                        sellers_spec = buyers_spec

                        traders_spec = {'sellers':sellers_spec, 'buyers':buyers_spec}

                        run_standard_simulation(end_time, traders_spec, order_sched, m)
                        m += 1

        end_time = durationmodes[default[0]]
        stepmode = default[1]
        timemode = default[2]
        duration = end_time - start_time

        range1 = (95, 95, schedule_offsetfn)
        supply_schedule = [ {'from':start_time, 'to':end_time, 'ranges':[range1], 'stepmode':stepmode}]

        range2 = (105, 105, schedule_offsetfn)
        demand_schedule = [ {'from':start_time, 'to':end_time, 'ranges':[range2], 'stepmode':stepmode}]

        order_sched = {'sup':supply_schedule, 'dem':demand_schedule, 'interval':30, 'timemode':timemode}

        buyers_spec = [(trader,trader_count) for trader in traders]
        sellers_spec = buyers_spec

        traders_spec = {'sellers':sellers_spec, 'buyers':buyers_spec}

        if evolution:
            rnd = 1
            while (rnd<(n_rnds+1)):
                buyers_spec = [(trader,trader_count) for trader in traders]
                sellers_spec = buyers_spec

                traders_spec = {'sellers':sellers_spec, 'buyers':buyers_spec}
                run_evolution_simulation(n_trials,end_time, traders_spec, order_sched, knock_out, rnd)
                rnd += 1
        else:    
            run_standard_simulation(n_trials, end_time, traders_spec, order_sched,0)


        sys.exit('Done Now')











        

        # run a sequence of trials that exhaustively varies the ratio of four trader types
        # NB this has weakness of symmetric proportions on buyers/sellers -- combinatorics of varying that are quite nasty
        

        # n_trader_types = 4
        # equal_ratio_n = 4
        # n_trials_per_ratio = 50

        # n_traders = n_trader_types * equal_ratio_n

        # fname = 'balances_%03d.csv' % equal_ratio_n

        # tdump = open(fname, 'w')

        # min_n = 1

        # trialnumber = 1
        # trdr_1_n = min_n
        # while trdr_1_n <= n_traders:
        #         trdr_2_n = min_n 
        #         while trdr_2_n <= n_traders - trdr_1_n:
        #                 trdr_3_n = min_n
        #                 while trdr_3_n <= n_traders - (trdr_1_n + trdr_2_n):
        #                         trdr_4_n = n_traders - (trdr_1_n + trdr_2_n + trdr_3_n)
        #                         if trdr_4_n >= min_n:
        #                                 buyers_spec = [('GVWY', trdr_1_n), ('SHVR', trdr_2_n),
        #                                                ('ZIC', trdr_3_n), ('ZIP', trdr_4_n)]
        #                                 segllers_spec = buyers_spec
        #                                 traders_spec = {'sellers':sellers_spec, 'buyers':buyers_spec}
        #                                 print buyers_spec
        #                                 trial = 1
        #                                 while trial <= n_trials_per_ratio:
        #                                         trial_id = 'trial%07d' % trialnumber
        #                                         market_session(trial_id, start_time, end_time, traders_spec,
        #                                                        order_sched, tdump, False)
        #                                         tdump.flush()
        #                                         trial = trial + 1
        #                                         trialnumber = trialnumber + 1
        #                         trdr_3_n += 1
        #                 trdr_2_n += 1
        #         trdr_1_n += 1
        # tdump.close()
        
        # print trialnumber
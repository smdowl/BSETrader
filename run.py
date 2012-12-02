from BSE import market_session
import math 

if __name__ == "__main__":

        # set up parameters for the session

        start_time = 0.0
        end_time = 600.0
        duration = end_time - start_time


        # schedule_offsetfn returns time-dependent offset on schedule prices
        def schedule_offsetfn(t):
                pi2 = math.pi * 2
                c = math.pi * 3000
                wavelength = t / c
                gradient = 100 * t / (c / pi2)
                amplitude = 100 * t / (c / pi2)
                offset = gradient + amplitude * math.sin(wavelength * t)
                return int(round(offset, 0))
                
                

        # #        range1 = (10, 190, schedule_offsetfn)
        # #        range2 = (200,300, schedule_offsetfn)

        # #        supply_schedule = [ {'from':start_time, 'to':duration/3, 'ranges':[range1], 'stepmode':'fixed'},
        # #                            {'from':duration/3, 'to':2*duration/3, 'ranges':[range2], 'stepmode':'fixed'},
        # #                            {'from':2*duration/3, 'to':end_time, 'ranges':[range1], 'stepmode':'fixed'}
        # #                          ]



        range1 = (95, 95, schedule_offsetfn)
        supply_schedule = [ {'from':start_time, 'to':end_time, 'ranges':[range1], 'stepmode':'fixed'}]

        range1 = (105, 105, schedule_offsetfn)
        demand_schedule = [ {'from':start_time, 'to':end_time, 'ranges':[range1], 'stepmode':'fixed'}]

        order_sched = {'sup':supply_schedule, 'dem':demand_schedule,'interval':30, 'timemode':'drip-poisson'}

        buyers_spec = [('GVWY',10),('SHVR',10),('ZIC',10),('ZIP',10),('AA',10)]
        sellers_spec = buyers_spec
        traders_spec = {'sellers':sellers_spec, 'buyers':buyers_spec}

        # run a sequence of trials, one session per trial

        n_trials = 10
        tdump=open('avg_balance.csv','w')
        trial = 1

        if n_trials > 1:
               dump_all = False
        else:
               dump_all = True
        dump_all = False

        while (trial<(n_trials+1)):
               trial_id = 'trial%04d' % trial
               market_session(trial_id, start_time, end_time, traders_spec, order_sched, tdump, dump_all)
               tdump.flush()
               trial = trial + 1
        tdump.close()

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
        #                                 sellers_spec = buyers_spec
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
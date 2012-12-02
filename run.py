import BSE

import TraderUtils

# def check_aa_profit():
#     with open("avg_balance.csv",'r'):

if __name__ == "__main__":
    start_time = 0.0
    end_time = 180.0
    duration = end_time - start_time

    supply_schedule = [ {'from':start_time, 'to':duration/3, 'ranges':[(10,190)], 'stepmode':'fixed'},
                        {'from':duration/3, 'to':2*duration/3, 'ranges':[(200,300)], 'stepmode':'fixed'},
                        {'from':2*duration/3, 'to':end_time, 'ranges':[(10,190)], 'stepmode':'fixed'}
                      ]

    demand_schedule = supply_schedule

    order_sched = {'sup':supply_schedule, 'dem':demand_schedule,
                   'interval':30, 'timemode':'drip-poisson'}

    # ,('ZIC',5)
    # ('SHVR',5),('SNPR',5),
    # buyers_spec = [('ZIP',5)],('AA',1)
    buyers_spec = [('SHVR',1),('GVWY',1),('SNPR',1),('ZIP',1),('AA',1)] 
    # buyers_spec = [('AA',2)]
    sellers_spec = buyers_spec

    traders_spec = {'sellers':sellers_spec, 'buyers':buyers_spec}

    # this is it

    n_trials = 10
    tdump=open('avg_balance.csv','w')

    TraderUtils.wipe_trader_files()

    trial = 1
    while trial <= n_trials:
            trial_id = 'trial%04d' % trial
            BSE.market_session(trial_id, 0.0, 180, traders_spec, order_sched, tdump, False)
            # BSE.market_session(trial_id, 0.0, 60, traders_spec, order_schedule, tdump, False)
            tdump.flush()
            trial = trial + 1

    tdump.close()

    # set up parameters for the session


import BSE

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
buyers_spec = [('SHVR',2),('GVWY',2),('SNPR',2),('ZIP',2)]
sellers_spec = buyers_spec

traders_spec = {'sellers':sellers_spec, 'buyers':buyers_spec}

# this is it

n_trials = 1
tdump=open('avg_balance.csv','w')
print tdump

trial = 1
while (trial<(n_trials+1)):
        trial_id = 'trial%04d' % trial
        BSE.market_session(trial_id, 0.0, 180, traders_spec, order_sched, tdump, False)
        # BSE.market_session(trial_id, 0.0, 60, traders_spec, order_schedule, tdump, False)
        tdump.flush()
        trial = trial + 1
tdump.close()

# set up parameters for the session


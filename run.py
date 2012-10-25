import BSE

supply_schedule = {'ranges':[(10,190)], 'mode':'fixed'}
demand_schedule = {'ranges':[(10,190)], 'mode':'jittered'}
order_schedule = {'sup':supply_schedule, 'dem':demand_schedule, 'interval':30}

buyers_spec = [('SHVR',31)]

sellers_spec = buyers_spec
traders_spec = {'sellers':sellers_spec, 'buyers':buyers_spec}

# this is it

n_trials = 1
tdump=open('avg_balance.csv','w')
print tdump

trial = 1
while (trial<(n_trials+1)):
        trial_id = 'trial%04d' % trial
        BSE.market_session(trial_id, 0.0, 180, traders_spec, order_schedule, tdump, False)
        tdump.flush()
        trial = trial + 1
tdump.close()
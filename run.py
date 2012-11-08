import BSE

supply_schedule = {'ranges':[(10,190)], 'mode':'fixed'}
demand_schedule = {'ranges':[(10,190)], 'mode':'jittered'}
order_schedule = {'sup':supply_schedule, 'dem':demand_schedule, 'interval':30}
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
        BSE.market_session(trial_id, 0.0, 180, traders_spec, order_schedule, tdump, False)
        # BSE.market_session(trial_id, 0.0, 60, traders_spec, order_schedule, tdump, False)
        tdump.flush()
        trial = trial + 1
tdump.close()
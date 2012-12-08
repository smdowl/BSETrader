import csv
from random import randint
def create_test_csv():
    header_list = ['ZIP','ZIC','GVWY']
    N = 100
    values = []
    for i in range(N):
        values.append([randint(0,10) for i in xrange(len(header_list))])

    with open ('output/simulation.csv','w') as output_file:
        sim_writer = csv.writer(output_file,delimiter=',')
        sim_writer.writerow(header_list)
        for row in values:
            sim_writer.writerow(row)

def store_simulation_data(trader_list,values,rnd):
    with open ('output/simulation'+str(rnd)+'.csv','w') as output_file:
        sim_writer = csv.writer(output_file,delimiter=',')
        sim_writer.writerow(trader_list)
        for row in values:
            sim_writer.writerow(row)

if __name__ == "__main__":
    create_test_csv()
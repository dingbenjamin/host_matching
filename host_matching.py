import heapq

from math import tanh
from pyevolve import G1DBinaryString
from pyevolve import GSimpleGA
from pyevolve import Mutators
from pyevolve import Selectors
from pymongo import MongoClient
from defs import *
from greedy_match import *
from util import *


### ----------------------------------------- Genetic Evaluation Functions ----------------------------------------- ###


def fairness_eval_func(host_flips, debug=0):
    assignments = greedy_match(hackers, hosts, host_flips)
    score = 0.0

    max_cap = num_hackers
    if num_hackers > total_host_capacity:
        max_cap = total_host_capacity

    assigned_hosts = {}
    num_team_rooms = {}
    for hack, host in assignments:
        if host not in assigned_hosts:
            assigned_hosts[host] = 0
        assigned_hosts[host] += 1

        if hack.team not in num_team_rooms:
            num_team_rooms[hack.team] = []
        if host.id not in num_team_rooms[hack.team]:
            num_team_rooms[hack.team].append(host.id)

    # want assignments to be same length as max_cap, so utilizing total capacity
    # needed if more hackers than hosts
    cap_waste = max_cap - len(assignments)  # put this in some tan function
    cap_waste_score = -20 * (tanh(0.05 * cap_waste) - 1)
    if debug > 0:
        print("Capacity: " + str(cap_waste_score))
    score += cap_waste_score

    # would rather waste smaller rooms than larger rooms, also put in some tan function
    room_waste = 0
    num_room_waste = 0
    for h in hosts:
        if h not in assigned_hosts:
            room_waste += h.capacity
            num_room_waste += 1
    room_waste_score = -20 * (tanh(0.05 * room_waste) - 1)
    if debug > 0:
        print("    Room: " + str(room_waste_score) + " Num room wasted: " + str(num_room_waste))
    score += room_waste_score

    # minimum number of rooms to break a team into is the number of teams
    min_num_team_rooms = len(num_team_rooms)
    iter_num_team_rooms = 0

    for team in num_team_rooms:
        iter_num_team_rooms += len(num_team_rooms[team])
        if debug > 1:
            print(team)

    num_team_splits = iter_num_team_rooms - min_num_team_rooms
    team_score = -20 * (tanh(0.05 * num_team_splits) - 1)

    if debug > 0:
        print("    Team: " + str(team_score) + " Num above optim: " + str(num_team_splits))

    score += team_score
    if debug > 0:
        if debug > 1:
            print(str(num_team_splits) + " Ideal: " + str(min_num_team_rooms))
        return (assignments, score)

    return score



## ---------- Constants ---------- ##

GENS_STAGE_1 = 1000
POPULATION_STAGE_1 = 100

GENS_STAGE 2 = 1000
POPULATION_STAGE_1


### ----------------------------------------------------- Main ----------------------------------------------------- ###


## ---------- Data Import ---------- ##


client = MongoClient('ds119150.mlab.com',
                     port=19150,
                     username='user',
                     password='idontreallycare',
                     authSource='localhost-optim',
                     authMechanism='SCRAM-SHA-1')
db = client['localhost-optim']

hackers = [Hacker(d) for d in db['parties'].find()]
hosts = [Host(d) for d in db['rooms'].find()]

## ---------- Create Subsets ---------- ##


m_gp_hosts = list(filter(host_type("M", True), hosts))
f_gp_hosts = list(filter(host_type("F", True), hosts))

m_np_hosts = list(filter(host_type("M", False), hosts))
f_np_hosts = list(filter(host_type("F", False), hosts))

for l in [m_gp_hosts, f_gp_hosts, m_np_hosts, f_np_hosts]:
    heapq.heapify(l)

len(m_gp_hosts), len(f_gp_hosts), len(m_np_hosts), len(f_np_hosts)

m_gp_hackers = list(filter(hacker_type("M", True), hackers))
f_gp_hackers = list(filter(hacker_type("F", True), hackers))

m_np_hackers = list(filter(hacker_type("M", False), hackers))
f_np_hackers = list(filter(hacker_type("F", False), hackers))

## ---------- Initialise Metrics ---------- ##


total_host_capacity = 0
for host in hosts:
    total_host_capacity += host.capacity

num_hackers = len(hackers)
num_hosts = len(hosts)
num_gp_hosts = sum(host.gender_pref == True for host in hosts)
num_np_hosts = num_hosts - num_gp_hosts


## ---------- (Deterministic) Greedy Algorithm ---------- ##

# TODO(Ben): Implement


## ---------- Genetic Algorithm ---------- ##

# TODO(Ben): Implement

# Genome is a bit string of the index of np
mutated_hosts = G1DBinaryString.G1DBinaryString(num_np_hosts)

# The evaluator function (objective function)
mutated_hosts.evaluator.set(fairness_eval_func)
mutated_hosts.mutator.set(Mutators.G1DBinaryStringMutatorFlip)

# Genetic Algorithm Instance
ga = GSimpleGA.GSimpleGA(mutated_hosts)
ga.selector.set(Selectors.GTournamentSelector)
ga.setGenerations(GENS_STAGE_1)
ga.setPopulationSize(POPULATION_STAGE_1)

# Do the evolution, with stats dump
ga.evolve(freq_stats=GENS_STAGE_1/10)

best = ga.bestIndividual()

print(best)

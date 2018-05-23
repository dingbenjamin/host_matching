import heapq
import sys
import pyevolve
import numpy as np
import numpy.ma as ma
import pymongo
import bson
import sys
import heapq
import networkx as nx

from bson.codec_options import CodecOptions
from bson import Binary, Code
from bson.json_util import dumps
from pymongo import MongoClient
from bson.json_util import loads
from functools import reduce
from operator import add
from random import shuffle, random, randrange, randint
from itertools import groupby
from operator import attrgetter
from sys import maxint
from pyevolve import G1DBinaryString, G1DList, GSimpleGA, Selectors, Mutators
from math import tanh
from defs import *
from util import *
from greedy_match import *


### ----------------------------------------- Genetic Evaluation Function ----------------------------------------- ###


def eval_func(host_flips, debug=0):
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

NUM_GENS = 1000
POPULATION_SIZE = 100

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

hackers = sorted(hackers, key=lambda pair: pair[0].id)
hosts = sorted(hosts, key=lambda pair: pair[0].id)

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


# TODO(Ben): Replace with seeding function and iterate over seeds
assignments = greedy_match(hackers, hosts)


## ---------- Genetic Algorithm ---------- ##

# Sort the assignments by their hacker id, same order as the hackers list

assignments = sorted(assignments, key=lambda pair: pair[0].id)

# Hacker assignment is the mapping between hacker index and host index
hacker_assignments = G1DList.G1DList(num_hackers)

# Initialise hacker_assignments to the outcome of the greedy algorithm
assignments_index = 0
for i in range(num_hackers):
    hacker = hackers[i]
    if hacker == assignments[assignments_index][0]:
        # The hacker was assigned
        host = assignments[assignments_index][1]
        host_index = hosts.index(host)
        assignments_index += 1
    else:
        # The hacker was not assigned
        host_index = -1
    hacker_assignments.append(host_index)
# Now hacker_assignments is in the same order as hackers

# The evaluator function (objective function)
hacker_assignments.evaluator.set(eval_func)

# Genetic Algorithm Instance
ga = GSimpleGA.GSimpleGA(hacker_assignments)
ga.selector.set(Selectors.GTournamentSelector) # TODO(Ben): Verify if this is the right selector
ga.setGenerations(NUM_GENS)
ga.setPopulationSize(POPULATION_SIZE)

# Do the evolution, with stats dump
ga.evolve(freq_stats=NUM_GENS/10)

best = ga.bestIndividual()

print(best)

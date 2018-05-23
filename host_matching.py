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


def eval_func(assignments, debug=0):
    # TODO(Alex): Implement evaluation function
    placeholder_score = 1
    return placeholder_score


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

hackers = sorted(hackers, key=lambda hacker: hacker.id)
hosts = sorted(hosts, key=lambda host: host.id)

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

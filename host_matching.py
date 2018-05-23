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
from random import shuffle, random, randrange
from pyevolve import G1DBinaryString
from pyevolve import GSimpleGA
from pyevolve import Selectors
from pyevolve import Mutators
from math import tanh


### Class Definitions

class Hacker:
    def __init__(self, doc, team=None):
        self.id = doc['_id']
        self.gender = ("M" if doc['gender'] == "Male" else "F")
        self.gender_pref = doc['hasGenderPreference']

        # TODO: Team data
        self.team = team

    def __str__(self):
        return "Hacker ID: {}\tGender: {}\tPref: {}".format(
            self.id, self.gender, self.gender_pref)

    def __lt__(self, other):
        return self.host.id < other.host.id


class Host:
    def __init__(self, doc):
        self.id = doc['_id']
        self.gender = ("M" if doc['gender'] == "Male" else "F")
        self.gender_pref = doc['hasGenderPreference']
        self.capacity = doc['capacity']
        self.fill = 0

    def __str__(self):
        return "Host ID: {}\tCapacity: {}\tGender: {}\tPref: {}".format(
            self.id, self.capacity, self.gender, self.gender_pref)

    def __lt__(self, other):
        return self.key() < other.key()

    def key(self):
        if self.fill == 0:
            return self.capacity  # larger rooms first
        else:
            return -(self.fill / self.capacity)

### Data Import ###

client = MongoClient('ds119150.mlab.com',
                      port = 19150,
                      username='user',
                      password='idontreallycare',
                      authSource='localhost-optim',
                      authMechanism='SCRAM-SHA-1')
db = client['localhost-optim']

hackers = [Hacker(d) for d in db['parties'].find()]
hosts = [Host(d) for d in db['rooms'].find()]

### Subsets ###

def hacker_type(gender, gender_pref):
  return lambda h: h.gender == gender and h.gender_pref == gender_pref


def host_type(gender, gender_pref):
    return lambda h: h.gender == gender and h.gender_pref == gender_pref


def gender(gender):
  return lambda h: h.gender == gender


### Utility Functions ###


def match(hacker, host, assignments):
  assignments.append((hacker, host))
  host.fill += 1


def print_status(assignments):
    print("Assignments: {}".format(len(assignments)))

    total_ha_cap = reduce(add, [
        len(m_gp_hackers), len(f_gp_hackers),
        len(m_np_hackers), len(f_np_hackers)])

    print("Awaiting Assignment: {} ({} + {} + {} + {})".format(total_ha_cap,
                                                               len(m_gp_hackers), len(f_gp_hackers),
                                                               len(m_np_hackers), len(f_np_hackers)))

    m_gp_ho_cap = reduce(lambda sum, x: sum + x.capacity, m_gp_hosts, 0)
    f_gp_ho_cap = reduce(lambda sum, x: sum + x.capacity, f_gp_hosts, 0)
    m_np_ho_cap = reduce(lambda sum, x: sum + x.capacity, m_np_hosts, 0)
    f_np_ho_cap = reduce(lambda sum, x: sum + x.capacity, f_np_hosts, 0)
    total_ho_cap = reduce(add, [
        m_gp_ho_cap, f_gp_ho_cap, m_np_ho_cap, f_np_ho_cap])

    print("Capacity: {} ({} + {} + {} + {})".format(total_ho_cap,
                                                    m_gp_ho_cap, f_gp_ho_cap,
                                                    m_np_ho_cap, f_np_ho_cap))


### Loss Function
def eval_func(host_flips, dev=False):
    # TODO(Alex):
    assignments = hybrid_match(hackers, hosts, host_flips)
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

    # want assignments to be same length as max_cap, so utilizing total capacity, cap_waste = 0 would result in max fitness
    cap_waste = max_cap - len(assignments)  # put this in some tan function
    score += -20 * (tanh(0.05 * cap_waste) - 1)

    # would rather waste smaller rooms than larger rooms, also put in some tan function
    room_waste = 0
    for h in hosts:
        if h not in assigned_hosts:
            room_waste += h.capacity
    score += -20 * (tanh(0.05 * room_waste) - 1)

    # minimum number of rooms to break a team into is the number of teams
    min_num_team_rooms = len(num_team_rooms)
    iter_num_team_rooms = 0

    for team in num_team_rooms:
        iter_num_team_rooms += len(num_team_rooms[team])

    num_team_splits = iter_num_team_rooms - min_num_team_rooms
    score += -20 * (tanh(0.05 * num_team_splits) - 1)

    return score


### Constants ###


NUM_GENS = 1000


### Main ###

# Create subsets

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

# Test Code

# original_assignments = hybrid_match(hackers, hosts)
# print("Original assignments: " + str(len(original_assignments)))
#
# no_flip = G1DBinaryString.G1DBinaryString(38)
# for i in range(71):
#   no_flip.append(0)
# no_flip_assignments = hybrid_match(hackers, hosts, no_flip)
# print("With no flip: " + str(len(no_flip_assignments)))

# Genetic Algorithm

total_host_capacity = 0
for host in hosts:
  total_host_capacity += host.capacity

num_hackers = len(hackers)
num_hosts = len(hosts)
num_gp_hosts = sum(host.gender_pref == True for host in hosts)
num_np_hosts = num_hosts - num_gp_hosts
mutated_hosts = G1DBinaryString.G1DBinaryString(num_np_hosts)

# The evaluator function (objective function)
mutated_hosts.evaluator.set(eval_func)
mutated_hosts.mutator.set(Mutators.G1DBinaryStringMutatorFlip)

# Genetic Algorithm Instance
ga = GSimpleGA.GSimpleGA(mutated_hosts)
ga.selector.set(Selectors.GTournamentSelector)
ga.setGenerations(NUM_GENS)
ga.setPopulationSize(100)

# Do the evolution, with stats dump
ga.evolve(freq_stats=NUM_GENS/10)

best = ga.bestIndividual()

print(best)
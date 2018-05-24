from pyevolve import G1DList, GSimpleGA, Selectors, Mutators, Initializators
from pymongo import MongoClient
from math import tanh

from eval_func import *
from greedy_match import *


### ----------------------------------------- Genetic Evaluation Function ----------------------------------------- ###


def test_eval_func(hacker_assignments):
    # TODO(Alex): Implement evaluation function
    placeholder_sum = sum(hacker_assignments)
    placeholder_score = 1
    return placeholder_score


def eval_func(matching, dev=0):
    score = 0.0
    host_to_hack = {}
    team_to_hosts = {}
    for e in range(len(matching)):
        # dictionary of hosts to lists of hackers who they are hosting
        if hosts[matching[e]] not in host_to_hack:
            host_to_hack[hosts[matching[e]]] = []

        # TODO(Ben): Add fakeness
        if hackers[e].is_fake == False:
            host_to_hack[hosts[matching[e]]].append(hackers[e])

        # dictionary of teams to who is hosting its members
    if hackers[e].team not in team_to_hosts:
        team_to_hosts[hackers[e].team] = []
    team_to_hosts[hackers[e].team].append(hosts[matching[e]])

    total_cap_var = calc_fullness_var(host_to_hack)
    score_cap_var = -20 * (tanh(0.1 * total_cap_var) - 1)

    total_team_split = calc_team_division(team_to_hosts)
    score_team_split = -20 * (tanh(0.1 * total_team_split) - 1)

    total_gender_mismatches = calc_gender_mismatch(host_to_hack)
    score_gender_mismatches = -20 * (tanh(total_gender_mismatches))

    total_sleeptime_diff = calc_sleeptime_diff(host_to_hack)
    score_sleeptime = -20 * (tanh(0.1 * total_sleeptime_diff) - 1)

    score = score_cap_var + score_team_split + \
        score_gender_mismatches + score_sleeptime

    # Diagnostic tools
    if dev > 0:
        print("Capacity variance: " + str(total_cap_var))
        print("      Team splits: " + str(total_team_split))
        print("Gender mismatches: " + str(total_gender_mismatches))
        print("   Sleeptime diff: " + str(total_sleeptime_diff))
        print("  SCORE BREAKDOWN  ")
        print("Capacity var: " + str(score_cap_var))
        print(" Team splits: " + str(score_team_split))
        print("Gender prefs: " + str(score_gender_mismatches))
        print("   Sleep var: " + str(score_sleeptime))
        print("-----------------------------")
        print("Total Score " + str(score) + "/80")  # 80 is max possible score

    return score


def init_genome(genome, **args):
    # Initialise hacker_assignments to the outcome of the greedy algorithm
    genome.genomeList = []

    for i in range(len(global_assignments)):
        # hackers and assignments should be 1-1 mapped via index
        host_index = global_hosts.index(global_assignments[i][1])
        genome.genomeList.append(host_index)


## ---------- Constants ---------- ##

NUM_GENS = 1000
POPULATION_SIZE = 100
MUTATION_RATE = 0.05

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

# TODO(Ben): Update this number after fake hackers are inputted
num_hackers = len(hackers)
num_hosts = len(hosts)
num_gp_hosts = sum(host.gender_pref == True for host in hosts)
num_np_hosts = num_hosts - num_gp_hosts


## ---------- (Deterministic) Greedy Algorithm ---------- ##


# TODO(Ben): Replace with seeding function and iterate over seeds
assignments = greedy_match(hackers, hosts)
# NOTE: greedy_match mutates the fill attribute of hosts, which we use below


## ---------- Genetic Algorithm ---------- ##

# Add Fake Hackers to represent unused spaces.
for host in hosts:
    fakes_needed = host.capacity - host.fill
    for i in range(fakes_needed):
        fake_hacker = FHacker()
        assignments.append((fake_hacker, host))
        hackers.append(fake_hacker)

# Sort the assignments by their hacker id, same order as the hackers list
assignments = sorted(assignments, key=lambda pair: pair[0].id)
hackers = sorted(hackers, key=lambda hacker: hacker.id)

# Hacker assignment is the mapping between hacker index and host index
hacker_assignments = G1DList.G1DList(num_hackers)
hacker_assignments.evaluator.set(eval_func)
hacker_assignments.mutator.set(Mutators.G1DListMutatorSwap)

# Set some things to global for the init function to access
global_hosts = hosts
global_assignments = assignments
hacker_assignments.initializator.set(init_genome)

# Genetic Algorithm Instance
ga = GSimpleGA.GSimpleGA(hacker_assignments)
# TODO(Ben): Verify if this is the right selector
ga.selector.set(Selectors.GTournamentSelector)
ga.setGenerations(NUM_GENS)
ga.setCrossoverRate(0)
ga.setPopulationSize(POPULATION_SIZE)
ga.setMutationRate(MUTATION_RATE)

# Do the evolution, with stats dump
ga.evolve(freq_stats=NUM_GENS/10)

best = ga.bestIndividual()

print(best)

"""Stage 1: Host matching by changing insertion order (Notebook 4.3)."""
from math import tanh
from operator import add, attrgetter, itemgetter

from pyevolve import (Crossovers, G1DList, GSimpleGA, Initializators, Mutators,
                      Selectors)
from pyevolve.DBAdapters import DBFileCSV

from defs import *
from eval_func import *
from greedy_match import *


def greedy_match_for_genome(genome, hackers, hosts):
    hackers_ordered = [hacker for _, hacker in sorted(zip(genome, hackers))]
    return greedy_match(hackers_ordered, hosts)


def evolve(hackers, hosts, num_gens, stat_freq, population_size, mutation_rate,
           crossover_rate, elitism, selector):

    def init_genome(genome, **args):
        # Initialise hacker_assignments to the outcome of the greedy algorithm
        genome.genomeList = range(0, len(hackers))

    def eval_func(genome, dev=0):
        # 1. Generate the matching.
        matching = greedy_match_for_genome(genome, hackers, hosts)[0]

        # 2. Preprocess for scoring.
        host_to_hack = {}
        team_to_hosts = {}
        for hacker, host in matching:
            # dictionary of hosts to lists of hackers who they are hosting
            if host not in host_to_hack:
                host_to_hack[host] = []
            host_to_hack[host].append(hacker)

            # dictionary of teams to who is hosting its members
            if hacker.team not in team_to_hosts:
                team_to_hosts[hacker.team] = []
            team_to_hosts[hacker.team].append(host)

        # 3. Do the scoring.
        total_cap_var = calc_fullness_var(host_to_hack)
        score_cap_var = -25 * (tanh(0.05 * total_cap_var) - 1)

        total_team_split = calc_team_division(team_to_hosts, dev=dev)
        score_team_split = -25 * (tanh(0.05 * total_team_split-2) - 1)

        total_gender_mismatches = calc_gender_mismatch(host_to_hack)
        score_gender_mismatches = -13 * \
            (tanh(0.1 * (total_gender_mismatches - 15)) - 1)

        total_sleeptime_diff = calc_sleeptime_diff(host_to_hack)
        score_sleeptime = -25 * (tanh(0.0025 * total_sleeptime_diff) - 1)

        score = score_cap_var + score_team_split + \
            score_gender_mismatches + score_sleeptime

        # Diagnostic tools
        if dev > 0:
            print("Capacity variance: " + str(total_cap_var))
            print("      Team splits: " + str(total_team_split))
            print("Gender mismatches: " + str(total_gender_mismatches))
            print("   Sleeptime diff: " + str(total_sleeptime_diff))
            print("")
            print("  SCORE BREAKDOWN  ")
            print("Capacity var: " + str(score_cap_var))
            print(" Team splits: " + str(score_team_split))
            print("Gender prefs: " + str(score_gender_mismatches))
            print("   Sleep var: " + str(score_sleeptime))
            print("-----------------------------")
            # 80 is max possible score
            print("Total Score " + str(score) + "/80")

        return score

    # Hacker assignment is the mapping between hacker index and host index
    hacker_order = G1DList.G1DList(len(hackers))
    hacker_order.evaluator.set(eval_func)
    hacker_order.crossover.set(Crossovers.G1DListCrossoverCutCrossfill)
    hacker_order.mutator.set(Mutators.G1DListMutatorSwap)
    hacker_order.initializator.set(init_genome)

    # Genetic Algorithm Instance
    ga = GSimpleGA.GSimpleGA(hacker_order)
    ga.setDBAdapter(DBFileCSV(identify="stage_1", frequency=10, reset=True))
    ga.selector.set(selector)
    ga.setGenerations(num_gens)
    ga.setCrossoverRate(crossover_rate)
    ga.setPopulationSize(population_size)
    ga.setMutationRate(mutation_rate)
    ga.setElitismReplacement(elitism)

    # Do the evolution, with stats dump
    ga.evolve(freq_stats=stat_freq)

    # Print outcome.
    best = ga.bestIndividual()
    eval_func(best, dev=1)
    ga.printStats()

    return best

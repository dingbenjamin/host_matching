from math import tanh
from random import choice

import numpy as np
import networkx as nx
import matplotlib.pyplot as plt

from numpy.linalg import norm
from numpy.random import choice
from pyevolve import G1DList, GSimpleGA, Selectors, Crossovers
from pyevolve import Util
from pymongo import MongoClient

from eval_func import *
from greedy_match import *


def evolve(hackers, hosts, initial_matching, num_gens, stat_freq,
           population_size, mutation_rate, crossover_rate, elitism,
           selector):
    num_hackers = len(hackers)
    (assignments,
     m_gp_assigned_hackers,
     f_gp_assigned_hackers,
     np_assigned_hackers) = initial_matching

    # 1. Add Fake Hackers to represent unused spaces.
    for host in hosts:
        fakes_needed = host.capacity - host.fill
        for i in range(fakes_needed):
            fake_hacker = FHacker()
            assignments.append((fake_hacker, host))
            hackers.append(fake_hacker)

    # 2. Sort the assignments by their hacker id, same order as the hackers list
    assignments = sorted(assignments, key=lambda pair: pair[0].id)
    hackers = sorted(hackers, key=lambda hacker: hacker.id)
    hosts = sorted(hosts, key=lambda host: host.id)

    def eval_func(matching, dev=0):
        score = 0.0
        host_to_hack = {}
        team_to_hosts = {}
        for e in range(len(matching)):
            # dictionary of hosts to lists of hackers who they are hosting
            if hosts[matching[e]] not in host_to_hack:
                host_to_hack[hosts[matching[e]]] = []

            # TODO(Ben): Add fakeness
            if not hackers[e].is_fake:
                host_to_hack[hosts[matching[e]]].append(hackers[e])

                # dictionary of teams to who is hosting its members
            if hackers[e].team not in team_to_hosts:
                team_to_hosts[hackers[e].team] = []
            team_to_hosts[hackers[e].team].append(hosts[matching[e]])

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

    def init_genome(genome, **args):
        # Initialise hacker_assignments to the outcome of the greedy algorithm
        genome.genomeList = [hosts.index(host) for _, host in assignments]

    def mutate_genome(genome, **args):
        """
        Mutations that respect gender preference, by mutating only within
        gender/gender preference groups.
        """
        global m_gp_assigned_hackers
        global f_gp_assigned_hackers
        global np_assigned_hackers

        def indices_of_subset(subset):
            return [i for i, x in enumerate(genome) if hackers[x] in subset]

        def mutate_subset(subset):
            mutations = 0
            for idx in xrange(len(subset)):
                if Util.randomFlipCoin(args["pmut"]):
                    Util.listSwapElement(
                        genome,
                        subset[idx],
                        subset[rand_randint(0, len(subset) - 1)]
                    )
                    mutations += 1

            return mutations

        if args["pmut"] <= 0.0:
            return 0
        listSize = len(genome)
        mutations = args["pmut"] * listSize

        # 1. Find subsets to do mutations in.
        m_gp = indices_of_subset(m_gp_assigned_hackers)
        f_gp = indices_of_subset(f_gp_assigned_hackers)
        np_ = indices_of_subset(np_assigned_hackers)

        # 2. Run random mutations on each subset.
        if mutations < 1.0:
            mutations = mutate_subset(
                m_gp) + mutate_subset(f_gp) + mutate_subset(np_)
        else:
            for _ in xrange(int(round(mutations))):
                a = [m_gp, f_gp, np_]
                len_a = np.array(map(len, a))
                subset = choice(a, p=(len_a / norm(len_a, ord=1)))
                Util.listSwapElement(genome, randint(0, len(subset) - 1),
                                     randint(0, len(subset) - 1))

        return int(mutations)

    # Hacker assignment is the mapping between hacker index and host index
    hacker_assignments = G1DList.G1DList(num_hackers)
    hacker_assignments.evaluator.set(eval_func)
    hacker_assignments.mutator.set(mutate_genome)
    hacker_assignments.crossover.set(Crossovers.G1DListCrossoverCutCrossfill)
    hacker_assignments.initializator.set(init_genome)

    # Genetic Algorithm Instance
    ga = GSimpleGA.GSimpleGA(hacker_assignments)
    ga.setDBAdapter(DBFileCSV(identify="stage_2", frequency=10, reset=True))
    ga.selector.set(selector)
    ga.setGenerations(num_gens)
    ga.setCrossoverRate(crossover_rate)
    ga.setPopulationSize(population_size)
    ga.setMutationRate(mutation_rate)
    ga.setElitismReplacement(elitism)

    # Do the evolution, with stats dump
    ga.evolve(freq_stats=stat_freq)

    best = ga.bestIndividual()
    best_assignments = [(hackers[i], hosts[best[i]]) for i in range(len(best))]

    eval_func(best, dev=1)
    ga.printStats()

    return best, best_assignments


# ---------- Visualisation ---------- #


def visualize():
    # Add Nodes
    g = nx.Graph()
    g.add_nodes_from(hosts)
    # Don't visualise the fake hackers
    real_hackers = [hacker for hacker in hackers if not hacker.is_fake]
    g.add_nodes_from(real_hackers)
    num_hackers = len(real_hackers)

    # Add Edges
    for hacker, host in best_assignments:
        g.add_edge(hacker, host)

    # Labels
    labels = {}
    for host in hosts:
        labels[host] = str(host.fill) + "/" + str(host.capacity)

    # Color the nodes
    colors = []
    for node in g.nodes():
        if "Hacker" in str(type(node)):
            colors.append('b')
        elif not node.fill == 0:
            colors.append('r')
        elif node.fill > node.capacity:
            colors.append('r')
        else:
            colors.append('g')

    # Draw
    plt.figure(figsize=(25, 25))
    plt.subplot(111)
    nx.draw_spring(g, with_labels=True, font_weight='bold',
                   node_color=colors, labels=labels, k=5, iterations=500,
                   scale=5)
    plt.show()

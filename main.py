from pyevolve import Selectors
from pymongo import MongoClient
from defs import Hacker, Host
from operator import attrgetter

import stage_1

# ---------- Data Import ---------- #
print("Importing data...")
client = MongoClient('ds119150.mlab.com',
                     port=19150,
                     username='user',
                     password='idontreallycare',
                     authSource='localhost-optim',
                     authMechanism='SCRAM-SHA-1')
db = client['localhost-optim']

hackers = [Hacker(d) for d in db['parties'].find()]
hosts = [Host(d) for d in db['rooms'].find()]

hackers = sorted(hackers, key=attrgetter("team"))
hosts = sorted(hosts, key=lambda host: host.id)


# ---------- Stage 1 ------------ #
print("Stage 1: Evolving an optimal hacker insertion order for the algorithm.")
best_order = stage_1.evolve(hackers,
                            hosts,
                            num_gens=6,
                            stat_freq=3,
                            population_size=150,
                            mutation_rate=0.03,
                            crossover_rate=0.8,
                            elitism=5,
                            selector=Selectors.GTournamentSelector)

assignments = stage1.greedy_match_for_genome(best_order, hackers, hosts)

print("Stage 2: Evolving from stage 1 to find minute improvements.")
best_assignments = stage2.evolve(hackers,
                                 hosts,
                                 num_gens=20,
                                 stat_freq=10,
                                 population_size=150,
                                 mutation_rate=0.03,
                                 crossover_rate=0.8,
                                 elitism=5,
                                 selector=Selectors.GTournamentSelector)

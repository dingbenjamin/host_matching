### Greedy Algorithm ###


import heapq
import random

from defs import *
from util import *
from random import shuffle

# match Inflexible Hackers
def match_gp_to_gp(hackers, gp_hosts, np_hosts, assignments):
    while len(hackers) > 0:
        hacker = hackers.pop()

        # A. Find a Host
        host = None
        if len(gp_hosts) > 0:
            host = heapq.heappop(gp_hosts)
        else:  # no more hosts available
            break

        # B. Assign the Host
        match(hacker, host, assignments)
        if (host.fill < host.capacity):
            heapq.heappush(gp_hosts, host)


# match Flexible Hackers
def match_np_hackers_pref_own_gender(hackers, gp_hosts, np_hosts, o_np_hosts, assignments):
    # o_np_hosts refers to the other gender's hosts

    while len(hackers) > 0:
        hacker = hackers.pop()

        # A. Find the best group to use
        hosts_group = None
        if len(gp_hosts) > 0:
            hosts_group = gp_hosts
        elif len(np_hosts) > 0:
            hosts_group = np_hosts
        elif len(o_np_hosts) > 0:
            hosts_group = o_np_hosts
        else:
            break

        # B. Find and match the host
        host = heapq.heappop(hosts_group)
        match(hacker, host, assignments)
        if (host.fill < host.capacity):
            heapq.heappush(hosts_group, host)


# match Flexible Hackers, without regard for NP host gender
def match_np_hackers(hackers, gp_hosts, np_hosts, assignments):
    while len(hackers) > 0:
        hacker = hackers.pop()

        # A. Find the best group to use
        hosts_group = None
        if len(gp_hosts) > 0:
            hosts_group = gp_hosts
        elif len(np_hosts) > 0:
            hosts_group = np_hosts
        else:
            break

        # B. Find and match the host
        host = heapq.heappop(hosts_group)
        match(hacker, host, assignments)
        if (host.fill < host.capacity):
            heapq.heappush(hosts_group, host)


# Kicking
def replace_gp_hackers(gender, gp_hackers, np_hackers, assignments):
    if len(np_hackers) == 0:
        return

    is_gp_hacker = lambda x: x[0].gender_pref and x[0].gender == gender
    not_gp_hacker = lambda x: not is_gp_hacker(x)
    to_hacker = lambda x: x[0]

    # A. Remove GP guests from assignments
    np_assignments = list(filter(not_gp_hacker, assignments))
    gp_assignments = list(filter(is_gp_hacker, assignments))

    # B. Randomize and set up probabilities.
    num_gp = len(gp_assignments)
    num_np = len(np_assignments)

    replace_prob = num_np / (float)(num_gp + num_np)  # <--- this is giving some issues
    shuffle(np_hackers)

    # C. Randomly replace GP with NP hackers.
    for i in range(len(gp_assignments)):
        [hacker, host] = gp_assignments[i]
        if len(np_hackers) > 0 and random() < replace_prob:
            gp_assignments[i] = ((np_hackers.pop(), host))
            gp_hackers.append(hacker)

    return gp_assignments + np_assignments


# Hybrid Matching
# host_flips is a G1D Binary String
def greedy_match(hackers, hosts):
    assignments = []
    for host in hosts:
        # NOTE: Not thread-safe
        host.fill = 0

    m_gp_hackers = list(filter(hacker_type("M", True), hackers))
    f_gp_hackers = list(filter(hacker_type("F", True), hackers))

    m_np_hackers = list(filter(hacker_type("M", False), hackers))
    f_np_hackers = list(filter(hacker_type("F", False), hackers))

    m_gp_hosts = list(filter(host_type("M", True), hosts))
    f_gp_hosts = list(filter(host_type("F", True), hosts))

    m_np_hosts = list(filter(host_type("M", False), hosts))
    f_np_hosts = list(filter(host_type("F", False), hosts))

    # Step 1: Match Inflexible Hackers
    match_gp_to_gp(m_gp_hackers, m_gp_hosts, m_np_hosts, assignments)
    match_gp_to_gp(f_gp_hackers, f_gp_hosts, f_np_hosts, assignments)

    # Step 2: Match Flexible Hackers
    np_hosts = list(heapq.merge(m_np_hosts, f_np_hosts))
    match_np_hackers(m_np_hackers, m_gp_hosts, np_hosts, assignments)
    match_np_hackers(f_np_hackers, f_gp_hosts, np_hosts, assignments)

    # Step 3: Kicking
    replace_gp_hackers("M", m_gp_hackers, m_np_hackers, assignments)
    replace_gp_hackers("F", f_gp_hackers, f_np_hackers, assignments)

    # Step 4: Shuffling
    # TODO(Ben): Temporarily disabled
    # shuffle_np(assignments)

    return assignments
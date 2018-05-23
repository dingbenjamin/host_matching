### Utility Functions ###


from functools import reduce
from operator import add


## Utility ##


def match(hacker, host, assignments):
  assignments.append((hacker, host))
  host.fill += 1


def print_status(assignments, m_gp_hackers, m_np_hackers, f_gp_hackers, f_np_hackers,
                 m_gp_hosts, f_gp_hosts, m_np_hosts, f_np_hosts):
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
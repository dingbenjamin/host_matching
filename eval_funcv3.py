##
##      Notes 
## add "Fake hacker" field to hackers 
from collections import Counter

SINGLE_FAKE_FULL = 0.5
DOUBLE_FAKE_FULL = 0.3

def eval_func(matching, dev=0):
  score = 0.0
  host_to_hack = {}
  team_to_hosts = {}
  for e in range(len(matching)):
    ## dictionary of hosts to lists of hackers who they are hosting
    if host[matching[e]] not in host_to_hack:
      host_to_hack[host[matching[e]]] = []

    if hack[e].isFake == False:
      host_to_hack[host[matching[e]]].append(hack[e])

    ## dictionary of teams to who is hosting its members
      if hack[e].team not in team_to_hosts:
        team_to_hosts[hack[e].team] = []
      team_to_hosts[hack[e].team].append(host[matching[e]])

  total_cap_var = calc_fullness_var(host_to_hack)
  score_cap_var = -20 * (tanh(0.1 * total_cap_var) - 1)

  total_team_split = calc_team_division(team_to_hosts)
  score_team_split = -20 * (tanh(0.1 * total_team_split) - 1)

  total_gender_mismatches = calc_gender_mismatch(host_to_hack)
  score_gender_mismatches = -20 * (tanh(total_gender_mismatches))

  total_sleeptime_diff = calc_sleeptime_diff(host_to_hack)
  score_sleeptime = -20 * (tanh(0.1 * total_sleeptime_diff) - 1)

  score = score_cap_var + score_team_split + score_gender_mismatches + score_sleeptime

  ## Diagnostic tools
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
    print("Total Score " + str(score))

  return score


  

  #### params 
  # total_cap_var
  # total_team_split
  # total_gender_mismatches
  # total_sleeptime_diff

#calculate average "fullness" of room
def calc_fullness_var(host_to_hack):
  total_fullness = 0.0
  for host in host_to_hack:
    if host.capacity > 2 or len(host_to_hack[host]) >= 1:
      total_fullness += len(host_to_hack[host]) / float(host.capacity)
    elif host.capacity == 2:
      total_fullness += DOUBLE_FAKE_FULL
    else:
      total_fullness += SINGLE_FAKE_FULL

  avg_fullness = total_fullness / len(host_to_hack)

  total_cap_var = 0.0
  for host in host_to_hack:
    if host.capacity > 2:
      room_fullness = len(host_to_hack[host]) / float(host.capacity)
      total_cap_var += (room_fullness - avg_fullness)**2
    elif host.capacity > 1:
      total_cap_var += (single_empty_fullness - avg_fullness)**2
    else:
      total_cap_var += (double_empty_fullness - avg_fullness)**2 
  return total_cap_var

##calculate team distribution loss
def calc_team_division(team_to_hosts):
  total_team_split = 0.0
  for team in team_to_hosts:
    teammates_per_room = Counter(team_to_hosts[team])
    for x in teammates_per_room:
      total_team_split += 1.0/teammates_per_room[x]
    total_team_split -= 1.0/len(team_to_hosts[team])
  return total_team_split

#calculate number of gender mismatches
def calc_gender_mismatch(host_to_hack):
  total_gender_mismatches = 0
  for host in host_to_hack:
    males = 0
    females = 0
    num_females_gp = 0
    num_males_gp   = 0
    if host.gender == "M":
      males += 1
      if host.gender_pref:
        num_males_gp += 1
    else:
      females += 1
      if host.gender_pref:
        num_females_gp += 1

    for hack in host_to_hack[host]:
      if hack.gender == "M":
        males += 1
        if hack.gender_pref:
          num_males_gp += 1
      else:
        females += 1
        if hack.gender_pref:
          num_females_gp += 1
    total_gender_mismatches += (num_females_gp * males) + (num_males_gp * females)
  return total_gender_mismatches

def calc_sleeptime_diff(host_to_hack):
  total_sleeptime_diff = 0.0
  for room in host_to_hack:
    for hack in host_to_hack[room]
      if room.bedtime < hack.bedtime:
        total_sleeptime_diff += (hack.bedtime - room.bedtime) ** 2
  return total_sleeptime_diff

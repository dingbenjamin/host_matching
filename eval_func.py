### Evaluation Subfunctions ###


from collections import Counter

SINGLE_FAKE_FULL = 0.5
DOUBLE_FAKE_FULL = 0.3

#### params
# total_cap_var
# total_team_split
# total_gender_mismatches
# total_sleeptime_diff

# calculate average "fullness" of room
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
      total_cap_var += (SINGLE_FAKE_FULL - avg_fullness)**2
    else:
      total_cap_var += (DOUBLE_FAKE_FULL - avg_fullness)**2
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
    for hack in host_to_hack[room]:
      if room.bedtime < hack.bedtime:
        total_sleeptime_diff += (hack.bedtime - room.bedtime) ** 2
  return total_sleeptime_diff

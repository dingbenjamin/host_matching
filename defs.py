### Class Definitions ###

import sys

from random import randint

## Classes ##


class Hacker:
    def __init__(self, doc, team=None):
        self.id = doc['_id']
        self.gender = ("M" if doc['gender'] == "Male" else "F")
        self.gender_pref = doc['hasGenderPreference']
        self.team = int(doc.get('teamCode', randint(100,sys.maxsize)))

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
        self.flipped = False

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


## Subsets ##


def hacker_type(gender, gender_pref):
  return lambda h: h.gender == gender and h.gender_pref == gender_pref


def host_type(gender, gender_pref):
    return lambda h: h.gender == gender and h.gender_pref == gender_pref


def gender(gender):
  return lambda h: h.gender == gender
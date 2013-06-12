import os
import re

"""
A simple way to verify whether team, match, event key name strings are valid ndb
keys.
"""

team_key_name_regex = re.compile(r'^frc[1-9]\d+$')
event_key_name_regex = re.compile(r'^[1-9]\d{3}[a-z]+$')
match_key_name_regex = re.compile(r'^[1-9]\d{3}[a-z]+\_(?:qm|ef|qf\dm|sf\dm|f\dm)\d+$')

def validate_team_key_name(team_key):
    match = re.match(team_key_name_regex, team_key)
    return True if match else False

def validate_event_key_name(event_key):
    match = re.match(event_key_name_regex, event_key)
    return True if match else False

def validate_match_key_name(match_key):
    match = re.match(match_key_name_regex, match_key)
    return True if match else False

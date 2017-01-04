event_properties = {
    'simple': [
        'key',
        'name',
        'year',
        'event_code',
        'event_type',
        'district_type',
        'start_date',
        'end_date',
        'city',
        'state_prov',
        'country'],
    'keys': ['key']
}

team_properties = {
    'simple': [
        'key',
        'team_number',
        'nickname',
        'name',
        'city',
        'state_prov',
        'country'],
    'keys': ['key']
}

match_properties = {
    'simple': [
        'key',
        'event_key',
        'comp_level',
        'set_number',
        'match_number',
        'alliances',
        'winning_alliance',
        'time',
        'actual_time'],
    'keys': ['key']
}


def filter_event_properties(events, model_type):
    return [{key: event[key] for key in event_properties[model_type]} for event in events]


def filter_team_properties(teams, model_type):
    return [{key: team[key] for key in team_properties[model_type]} for team in teams]


def filter_match_properties(matches, model_type):
    return [{key: match[key] for key in match_properties[model_type]} for match in matches]

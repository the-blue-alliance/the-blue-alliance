# Allows us to sort matches by key name.
# Note: Matches within a comp_level (qual, qf, sf, f, etc.) will be in order,
# but the comp levels themselves may not be in order. Doesn't matter because
# XXX_match_table.html checks for comp_level when rendering the page
def natural_sort_matches(matches):
    import re
    convert = lambda text: int(text) if text.isdigit() else text.lower() 
    alphanum_key = lambda match: [ convert(c) for c in re.split('([0-9]+)', str(match.get_key_name())) ] 
    return sorted(matches, key = alphanum_key)
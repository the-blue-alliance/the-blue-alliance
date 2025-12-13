from backend.common.models.keys import EventKey

# event_key (code, short_name)
EVENT_CODE_EXCEPTIONS = {
    "archimedes": ("arc", "Archimedes"),
    "arpky": ("arc", "Archimedes"),
    "carson": ("cars", "Carson"),
    "carver": ("carv", "Carver"),
    "curie": ("cur", "Curie"),
    "cpra": ("cur", "Curie"),
    "daly": ("dal", "Daly"),
    "dcmp": ("dal", "Daly"),
    "darwin": ("dar", "Darwin"),
    "galileo": ("gal", "Galileo"),
    "gcmp": ("gal", "Galileo"),
    "hopper": ("hop", "Hopper"),
    "hcmp": ("hop", "Hopper"),
    "jcmp": ("joh", "Johnson"),
    "mpcia": ("mil", "Milstein"),
    "newton": ("new", "Newton"),
    "npfcmp": ("new", "Newton"),
    "roebling": ("roe", "Roebling"),
    "tesla": ("tes", "Tesla"),
    "turing": ("tur", "Turing"),
    "johnson": ("joh", "Johnson"),
    "milstein": ("mil", "Milstein"),
    # For Einstein, format with the name "Einstein" or "FIRST Championship" or whatever
    "cmp": ("cmp", "{}"),
    "cmpmi": ("cmpmi", "{} (Detroit)"),
    "cmpmo": ("cmpmo", "{} (St. Louis)"),
    "cmptx": ("cmptx", "{} (Houston)"),
}


class EventCodeExceptions:

    @staticmethod
    def resolve(event_key: EventKey) -> EventKey:
        year, event_code = (event_key[:4], event_key[4:])
        if event_code in EVENT_CODE_EXCEPTIONS:
            return f"{year}{EVENT_CODE_EXCEPTIONS[event_code][0]}"

        return event_key

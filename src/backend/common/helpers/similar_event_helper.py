import re
import unicodedata
from difflib import SequenceMatcher
from typing import FrozenSet, List, Optional, Set

from backend.common.models.event import Event

# Words that show up in so many FRC event names that sharing one tells us
# nothing about two events being the same event in different years.
GENERIC_NAME_WORDS: FrozenSet[str] = frozenset(
    {
        "a",
        "an",
        "and",
        "annual",
        "at",
        "by",
        "challenge",
        "champs",
        "championship",
        "championships",
        "classic",
        "competition",
        "competitions",
        "day",
        "event",
        "first",
        "for",
        "frc",
        "ftc",
        "in",
        "invitational",
        "of",
        "off",
        "offseason",
        "on",
        "presented",
        "presents",
        "robot",
        "robotics",
        "robots",
        "season",
        "state",
        "the",
        "tournament",
        "vex",
        "week",
    }
)

# Similarity a candidate must reach to be shown to a reviewer at all
SIMILARITY_THRESHOLD = 0.65

# Most similar events to show for a single suggestion. Multi-day and
# multi-stop offseason series (e.g. the Arizona Robotics League) can
# legitimately have this many prior-year siblings.
MAX_SIMILAR_EVENTS = 8

# Full event names are mostly generic filler ("FRC Off-Season Robotics
# Competition"), so raw name similarity is discounted relative to the signals
# that compare only the distinguishing words.
RAW_NAME_WEIGHT = 0.85

# Words an acronym may or may not pick up a letter from -- "South Carolina
# Robotics & Practical Off-Season" is abbreviated SCRAP, but "Georgia Robotics
# Invitational Tournament & Showcase" is GRITS
CONNECTOR_WORDS: FrozenSet[str] = frozenset(
    {"a", "an", "and", "at", "by", "for", "in", "of", "on", "the"}
)

# How much of an acronym has to be written out before a name that starts with
# it counts as that acronym, since acronyms routinely drop the tail of a name
# ("South Carolina Robotics And Practical" Off-Season -> SCRAP)
MIN_ACRONYM_PREFIX = 4

# Abbreviations that get written in caps but name a whole category of events
# rather than one particular event
AMBIGUOUS_ABBREVIATIONS: FrozenSet[str] = frozenset(
    {"frc", "ftc", "first", "stem", "tba", "usa", "vex"}
)

# Score given when one name is an acronym of the other ("GRITS" <->
# "Georgia Robotics Invitational Tournament & Showcase"), or when both names
# carry the same abbreviation ("THOR - Thundering Herd of Robots" <->
# "THOR @ UNC Pembroke")
ACRONYM_SCORE = 0.95
SHARED_ABBREVIATION_SCORE = 0.9

# How alike two words must look to count as the same word, which lets typos and
# pluralization ("Invitations" vs "Invitational") still line up
WORD_MATCH_THRESHOLD = 0.85

# Every word of one name appearing in the other is slightly weaker evidence
# when the other name has extra words in it, so a name that matches outright
# still outranks a name that merely contains it.
CONTAINMENT_WEIGHT = 0.9

# Location agreement is a bonus on top of name similarity, never a match on
# its own -- two unrelated events are often held in the same town.
COUNTRY_BONUS = 0.05
STATE_BONUS = 0.15
CITY_BONUS = 0.15
VENUE_BONUS = 0.2

_NON_ALPHANUMERIC = re.compile(r"[^a-z0-9]+")
_WORD = re.compile(r"[A-Za-z]+")
_YEAR_TOKEN = re.compile(r"(19|20)\d\d")
# Roman numerals up to XXXIX, which is as high as an offseason event's edition
# number is going to get. Matching any run of i/v/x/l would swallow words.
_ROMAN_NUMERAL_TOKEN = re.compile(r"(?=[ivx])x{0,3}(ix|iv|v?i{0,3})")


def _normalize(name: Optional[str]) -> str:
    """
    Lowercases, strips accents, and collapses punctuation to single spaces.
    """
    decomposed = unicodedata.normalize("NFKD", name or "")
    ascii_only = decomposed.encode("ascii", "ignore").decode()
    spelled_out = ascii_only.lower().replace("&", " and ")
    return " ".join(_NON_ALPHANUMERIC.sub(" ", spelled_out).split())


def _tokens(name: Optional[str]) -> List[str]:
    """
    Words of a name with edition markers (years, roman numerals) removed.
    """
    return [
        token
        for token in _normalize(name).split()
        if not _YEAR_TOKEN.fullmatch(token)
        and not _ROMAN_NUMERAL_TOKEN.fullmatch(token)
    ]


def _significant_tokens(name: Optional[str]) -> List[str]:
    """
    Words of a name that actually distinguish it from other event names.
    """
    return [token for token in _tokens(name) if token not in GENERIC_NAME_WORDS]


def _acronyms(name: Optional[str]) -> Set[str]:
    """
    Acronyms a name could plausibly be abbreviated to. Which words get a letter
    varies -- every word ("Thundering Herd Of Robots" -> "thor"), every word
    but the connectors ("Georgia Robotics Invitational Tournament & Showcase"
    -> "grits"), or only the distinguishing ones -- so all three are included.
    """
    all_words = _tokens(name)
    without_connectors = [word for word in all_words if word not in CONNECTOR_WORDS]
    acronyms = {
        "".join(word[0] for word in words)
        for words in (all_words, without_connectors, _significant_tokens(name))
        if len(words) > 1
    }
    return {acronym for acronym in acronyms if len(acronym) >= 3}


def _is_acronym_of(word: str, acronyms: Set[str]) -> bool:
    """
    Whether a word abbreviates a name, either as the whole acronym or as enough
    of the front of one to be unmistakable.
    """
    return any(
        acronym == word
        or (len(word) >= MIN_ACRONYM_PREFIX and acronym.startswith(word))
        for acronym in acronyms
    )


def _acronym_like_words(name: Optional[str]) -> Set[str]:
    """
    Words in a name that could themselves be an acronym of another name.
    """
    return {
        token
        for token in _significant_tokens(name)
        if len(token) >= 3 and token.isalpha()
    }


def _abbreviations(name: Optional[str]) -> Set[str]:
    """
    Words written in all caps, which offseason events use to carry their
    identity across renames and rebrandings.
    """
    return {
        word.lower()
        for word in _WORD.findall(name or "")
        if len(word) >= 3
        and word.isupper()
        and word.lower() not in GENERIC_NAME_WORDS
        and word.lower() not in AMBIGUOUS_ABBREVIATIONS
    }


def _word_containment(a: List[str], b: List[str]) -> float:
    """
    Fraction of the shorter name's distinguishing words that also appear in the
    longer one, in [0, 1]. Comparing word by word (rather than comparing the
    names as a whole) means one long shared word doesn't make two events look
    alike, while a subtitle or a reordering doesn't make them look different.
    """
    shorter, longer = (
        (set(a), set(b)) if len(set(a)) <= len(set(b)) else (set(b), set(a))
    )
    matched = sum(
        1
        for word in shorter
        if any(
            SequenceMatcher(a=word, b=other).ratio() >= WORD_MATCH_THRESHOLD
            for other in longer
        )
    )
    length_agreement = len(shorter) / len(longer)
    return (matched / len(shorter)) * (
        CONTAINMENT_WEIGHT + (1 - CONTAINMENT_WEIGHT) * length_agreement
    )


def name_similarity(a: Optional[str], b: Optional[str]) -> float:
    """
    How likely two event names are to name the same event, in [0, 1].

    Offseason events get renamed constantly between years, so this looks at a
    few different kinds of agreement and takes the strongest one:
      * the full names look alike (discounted, since the filler words match too)
      * one name's distinguishing words are all present in the other, which
        covers added subtitles ("GRITS" -> "GRITS - Deep Space") and
        reorderings ("Tennessee Valley Fair Robo-Rodeo" -> "Robo-Rodeo at the
        TN Valley Fair")
      * one name is an acronym of the other
      * both names carry the same abbreviation
    """
    normalized_a, normalized_b = _normalize(a), _normalize(b)
    if not normalized_a or not normalized_b:
        return 0.0

    raw_similarity = SequenceMatcher(a=normalized_a, b=normalized_b).ratio()
    # Names that match outright aren't discounted; partial matches are, since
    # much of what they have in common is filler.
    score = (
        raw_similarity if raw_similarity == 1.0 else RAW_NAME_WEIGHT * raw_similarity
    )

    significant_a, significant_b = _significant_tokens(a), _significant_tokens(b)
    if significant_a and significant_b:
        score = max(score, _word_containment(significant_a, significant_b))
    else:
        # One of the names is entirely filler words; the raw comparison is all
        # we have, so don't discount it.
        score = max(score, raw_similarity)

    acronyms_a, acronyms_b = _acronyms(a), _acronyms(b)
    if any(_is_acronym_of(word, acronyms_b) for word in _acronym_like_words(a)) or any(
        _is_acronym_of(word, acronyms_a) for word in _acronym_like_words(b)
    ):
        score = max(score, ACRONYM_SCORE)

    if _abbreviations(a) & _abbreviations(b):
        score = max(score, SHARED_ABBREVIATION_SCORE)

    return score


def location_similarity(a: Event, b: Event) -> float:
    """
    Bonus for two events being held in the same place, in [0, 0.55].
    """
    score = 0.0
    if a.country and a.country == b.country:
        score += COUNTRY_BONUS
    if a.state_prov and a.state_prov == b.state_prov:
        score += STATE_BONUS
    if _normalize(a.city) and _normalize(a.city) == _normalize(b.city):
        score += CITY_BONUS
    if _normalize(a.venue) and _normalize(a.venue) == _normalize(b.venue):
        score += VENUE_BONUS
    return score


def event_similarity(a: Event, b: Event) -> float:
    """
    How likely two events are to be the same event, name plus location.
    """
    return name_similarity(a.name, b.name) + location_similarity(a, b)


class SimilarEventHelper:
    @classmethod
    def similar_events(
        cls,
        candidate_event: Event,
        events: List[Event],
        threshold: float = SIMILARITY_THRESHOLD,
        limit: int = MAX_SIMILAR_EVENTS,
    ) -> List[Event]:
        """
        Finds the events most likely to be the same event as the candidate,
        best match first.
        """
        scored = [(event_similarity(candidate_event, event), event) for event in events]
        matches = sorted(
            (scored_event for scored_event in scored if scored_event[0] >= threshold),
            key=lambda scored_event: (-scored_event[0], scored_event[1].key_name),
        )
        return [event for _, event in matches[:limit]]

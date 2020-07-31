from typing import Iterable, Sequence, Tuple


CITY_STATE_COUNTRY_PARAMETERS: Tuple[str, Iterable[Sequence[object]]] = (
    "city, state, country, output",
    [
        (None, None, None, ""),
        ("New York", None, None, "New York"),
        ("New York", "NY", None, "New York, NY"),
        ("New York", "NY", "USA", "New York, NY, USA"),
        ("New York", "NY", "US", "New York, NY, USA"),
        (None, "NY", None, "NY"),
        (None, "NY", "USA", "NY, USA"),
        (None, None, "USA", "USA"),
        ("New York", None, "USA", "New York, USA"),
    ],
)

LOCATION_PARAMETERS: Tuple[str, Iterable[Sequence[object]]] = (
    "city, state, country, postalcode, output",
    [
        (None, None, None, None, ""),
        ("New York", None, None, None, "New York"),
        ("New York", "NY", None, None, "New York, NY"),
        ("New York", "NY", "USA", None, "New York, NY, USA"),
        ("New York", "NY", "USA", "10023", "New York, NY 10023, USA"),
        (None, "NY", None, None, "NY"),
        (None, "NY", "USA", None, "NY, USA"),
        (None, None, "USA", None, "USA"),
        ("New York", None, "USA", None, "New York, USA"),
    ],
)

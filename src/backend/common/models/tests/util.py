CITY_STATE_COUNTRY_PARAMETERS = (
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

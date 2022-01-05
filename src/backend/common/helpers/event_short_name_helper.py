import re
from typing import Optional, Set

from backend.common.decorators import memoize
from backend.common.models.district import District


class EventShortNameHelper:
    """
    A helper class to compute event short names
    """

    @staticmethod
    @memoize(timeout=86400)  # 1 day
    def _get_all_district_codes() -> Set[str]:
        codes = set(
            [d.id()[4:].upper() for d in District.query().fetch(keys_only=True)]
        )
        if "MAR" in codes:  # MAR renamed to FMA in 2019
            codes.add("FMA")
        if "TX" in codes:  # TX and FIT used interchangeably
            codes.add("FIT")
        if "IN" in codes:  # IN and FIN used interchangeably
            codes.add("FIN")
        return codes

    @classmethod
    def get_short_name(cls, name_str: str, district_code: Optional[str] = None) -> str:
        """
        Extracts a short name like "Silicon Valley" from an event name like
        "Silicon Valley Regional sponsored by Google.org".

        See https://github.com/the-blue-alliance/the-blue-alliance-android/blob/master/android/src/test/java/com/thebluealliance/androidclient/test/helpers/EventHelperTest.java
        """

        all_district_codes = cls._get_all_district_codes()
        if district_code is not None:
            all_district_codes.add(district_code)
        district_code_regex = "|".join(all_district_codes)

        # Account for 2020 suspensions
        if name_str.startswith("***SUSPENDED***"):
            name_str = name_str.replace("***SUSPENDED***", "")

        # 2015+ districts
        # Numbered events with no name
        re_string = r"({}) District Event (#\d+)".format(district_code_regex)
        match = re.match(re_string, name_str)
        if match:
            return "{} {}".format(match.group(1).strip(), match.group(2).strip())

        # The rest
        re_string = r"(?:{}) District -?(.+)".format(district_code_regex)
        match = re.match(re_string, name_str)
        if match:
            partial = match.group(1).strip()
            match2 = re.sub(r"(?<=[\w\s])Event\s*(?:[\w\s]*$)?", "", partial)
            return match2.strip()

        # 2014- districts
        # district championships, other districts, and regionals
        name_str = re.sub(r"\s?Event", "", name_str)
        match = re.match(
            r"\s*(?:MAR |PNW |)(?:FIRST Robotics|FRC|)(.+)(?:District|Regional|Region|Provincial|State|Tournament|FRC|Field)(?:\b)(?:[\w\s]+?(#\d*)*)?(Day \d+)?",
            name_str,
        )

        if match:
            short = "".join(match.groups(""))
            match = re.match(r"(.+)(?:FIRST Robotics|FRC)", short)
            if match:
                result = match.group(1).strip()
            else:
                result = short.strip()
            if result.startswith("FIRST"):
                result = result[5:]
            return result.strip()

        return name_str.strip()

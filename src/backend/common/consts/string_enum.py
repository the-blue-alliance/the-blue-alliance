try:
    # Breaking change introduced in python 3.11
    # see https://docs.python.org/3/whatsnew/3.11.html#enum
    #
    # Changed Enum.__format__() (the default for format(), str.format()
    # and f-strings) of enums with mixed-in types (e.g. int, str) to also
    # include the class name in the output, not just the member’s key.
    from enum import StrEnum
except ImportError:  # pragma: no cover
    from enum import Enum  # pragma: no cover

    class StrEnum(str, Enum):  # pragma: no cover
        pass  # pragma: no cover

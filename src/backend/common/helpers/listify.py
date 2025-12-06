from typing import overload, TypeVar

TThing = TypeVar("TThing")


@overload
def listify(thing: list[TThing]) -> list[TThing]: ...


@overload
def listify(thing: TThing) -> list[TThing]: ...


def listify(thing: TThing | list[TThing]) -> list[TThing]:
    if thing is None:
        return []
    elif not isinstance(thing, list):
        return [thing]
    else:
        return thing


def delistify(things: list[TThing]) -> None | TThing | list[TThing]:
    if len(things) == 0:
        return []
    if len(things) == 1:
        return things.pop()
    else:
        return things

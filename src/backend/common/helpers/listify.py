from typing import List, overload, TypeVar, Union

TThing = TypeVar("TThing")


@overload
def listify(thing: List[TThing]) -> List[TThing]:
    ...


@overload
def listify(thing: TThing) -> List[TThing]:
    ...


def listify(thing: Union[TThing, List[TThing]]) -> List[TThing]:
    if not isinstance(thing, list):
        return [thing]
    else:
        return thing


def delistify(things: List[TThing]) -> Union[None, TThing, List[TThing]]:
    if len(things) == 0:
        return None
    if len(things) == 1:
        return things.pop()
    else:
        return things

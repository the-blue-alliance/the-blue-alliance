from typing import overload, Tuple, Union

@overload
def raises(
    expected_exception: Union["Type[_E]", Tuple["Type[_E]", ...]],
    *,
    match: "Optional[Union[str, Pattern]]" = ...
) -> "RaisesContext[_E]":
    ...  # pragma: no cover


@overload  # noqa: F811
def raises(  # noqa: F811
    expected_exception: Union["Type[_E]", Tuple["Type[_E]", ...]],
    func: Callable,
    *args: Any,
    **kwargs: Any
) -> _pytest._code.ExceptionInfo[_E]:
    ...  # pragma: no cover

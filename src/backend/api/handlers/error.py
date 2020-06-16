from typing import Tuple, Union


def handle_404(_e: Union[int, Exception]) -> Tuple[dict, int]:
    return {"Error": "Invalid endpoint"}, 404

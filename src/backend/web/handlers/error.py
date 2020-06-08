from flask import render_template
from typing import Tuple, Union


def handle_404(_e: Union[int, Exception]) -> Tuple[str, int]:
    return render_template("404.html"), 404


def handle_500(_e: Union[int, Exception]) -> Tuple[str, int]:
    return render_template("500.html"), 500

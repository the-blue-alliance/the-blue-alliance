from flask import render_template


def handle_404(_e: int | Exception) -> tuple[str, int]:
    return render_template("404.html"), 404


def handle_500(_e: int | Exception) -> tuple[str, int]:
    return render_template("500.html"), 500

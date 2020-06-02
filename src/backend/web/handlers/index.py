from flask import render_template


def index() -> str:
    return render_template("base.html")

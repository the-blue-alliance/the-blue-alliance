from flask import Flask, request, Response


def index() -> Response:
    return Response(status=200)

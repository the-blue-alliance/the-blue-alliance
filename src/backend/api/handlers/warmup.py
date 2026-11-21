from flask import Response


def warmup() -> Response:
    return Response(status=200)

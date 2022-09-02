import importlib

from typing import Tuple

import bs4
from werkzeug.test import Client


def get_error_title(resp_data: str) -> Tuple[str, str]:
    soup = bs4.BeautifulSoup(resp_data, "html.parser")
    return soup.find("h1").string, soup.find("h2").string


def test_handle_404(web_client: Client) -> None:
    resp = web_client.get("/asdf")
    assert resp.status_code == 404

    error_header, error_type = get_error_title(resp.data)
    assert error_header == "Oh Noes!1!!"
    assert error_type == "Error 404"


def test_handle_500() -> None:
    from backend.web import main

    # Other tests might have run a request which dirties the previously
    # imported app, so let's forcibly clear it here to start clean
    importlib.reload(main)

    def always_throw() -> str:
        raise Exception("welp")

    main.app.add_url_rule("/throw_500", view_func=always_throw)
    client = main.app.test_client()

    resp = client.get("/throw_500")
    assert resp.status_code == 500

    error_header, error_type = get_error_title(resp.data)
    assert error_header == "Oh Noes!1!!"
    assert error_type == "Error 500"

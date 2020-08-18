from backend.web.redirect import is_safe_url, safe_next_redirect


def test_is_safe_url_scheme() -> None:
    from backend.web.main import app

    with app.test_request_context("/"):
        assert not is_safe_url("ftp://localhost/")


def test_is_safe_url_netloc() -> None:
    from backend.web.main import app

    with app.test_request_context("/"):
        assert not is_safe_url("https://thebluealliance.com/")


def test_is_safe_url() -> None:
    from backend.web.main import app

    with app.test_request_context("/"):
        assert is_safe_url("/account")
        assert is_safe_url("https://localhost/account")


def test_safe_next_redirect_no_next() -> None:
    from backend.web.main import app

    with app.test_request_context("/"):
        response = safe_next_redirect("/")
        assert response.headers["Location"] == "/"


def test_safe_next_redirect_not_safe() -> None:
    from backend.web.main import app

    with app.test_request_context("/?next=http%3A%2F%2Fthebluealliance.com%2Faccount"):
        response = safe_next_redirect("/")
        assert response.headers["Location"] == "/"


def test_safe_next_redirect() -> None:
    from backend.web.main import app

    with app.test_request_context("/?next=http%3A%2F%2Flocalhost%2Faccount"):
        response = safe_next_redirect("/")
        assert response.headers["Location"] == "http://localhost/account"

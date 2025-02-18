import csv
import itertools
from datetime import datetime
from io import StringIO
from typing import List, Optional

from flask import abort, redirect, request, url_for

from backend.common.helpers.deferred import defer_safe
from backend.common.models.account import Account
from backend.common.models.keys import TeamNumber, Year
from backend.common.models.team_admin_access import TeamAdminAccess
from backend.web.profiled_render import render_template


def team_media_mod_list(year: Optional[Year] = None, page_num: int = 0):
    MAX_PAGE = 10
    PAGE_SIZE = 1000

    if year is None:
        year = datetime.now().year

    if page_num < MAX_PAGE:
        start = PAGE_SIZE * page_num
        end = start + PAGE_SIZE
        auth_codes = (
            TeamAdminAccess.query(
                TeamAdminAccess.year == year,
                TeamAdminAccess.team_number >= start,
                TeamAdminAccess.team_number < end,
            )
            .order(TeamAdminAccess.team_number)
            .fetch()
        )
    else:
        start = PAGE_SIZE * MAX_PAGE
        auth_codes = (
            TeamAdminAccess.query(TeamAdminAccess.team_number >= start)
            .order(TeamAdminAccess.team_number)
            .fetch()
        )

    page_labels = []
    for page in range(MAX_PAGE):
        if page == 0:
            page_labels.append("1-999")
        else:
            page_labels.append("{}'s".format(1000 * page))
    page_labels.append("{}+".format(1000 * MAX_PAGE))

    template_values = {
        "year": year,
        "auth_codes": auth_codes,
        "page_labels": page_labels,
    }

    return render_template("admin/team_media_mod_list.html", template_values)


def team_media_mod_add():
    return render_template("admin/team_media_mod_add.html")


def team_media_add_single(year: Year, csv_row: List[str]) -> None:
    team_number = int(csv_row[0])
    access = TeamAdminAccess(
        id=TeamAdminAccess.render_key_name(team_number, year),
        team_number=team_number,
        year=year,
        access_code=csv_row[1],
        expiration=datetime(year=year, month=7, day=1),
    )
    access.put()


def team_media_add_group(year: Year, csv_rows: List[List[str]]) -> None:
    for row in csv_rows:
        defer_safe(team_media_add_single, year, row, _queue="admin")


def team_media_mod_add_post():
    year = int(request.form.get("year"))
    auth_codes_csv = request.form.get("auth_codes_csv")

    csv_data = list(csv.reader(StringIO(auth_codes_csv), delimiter=","))
    for row in itertools.batched(csv_data, 100):
        # defer the actual datastore write, because with a large number
        # of teams to add, we don't want to OOM the original request
        defer_safe(team_media_add_group, year, row, _queue="admin")

    return redirect(url_for("admin.team_media_mod_list", year=year))


def team_media_mod_edit(year: Year, team_number: TeamNumber):
    access = TeamAdminAccess.query(
        TeamAdminAccess.year == year, TeamAdminAccess.team_number == team_number
    ).fetch(1)

    if not access:
        abort(404)

    access = access[0]
    account_email = None
    if access.account:
        account = access.account.get()
        account_email = account.email

    template_values = {
        "access": access,
        "account_email": account_email,
    }

    return render_template("admin/team_media_mod_edit.html", template_values)


def team_media_mod_edit_post(year: Year, team_number: TeamNumber):
    access = TeamAdminAccess.query(
        TeamAdminAccess.year == year, TeamAdminAccess.team_number == team_number
    ).fetch()

    if not access:
        abort(404)

    access = access[0]
    access_code = request.form.get("access_code")
    expiration = request.form.get("expiration")
    account_email = request.form.get("account_email")

    account = None
    if account_email:
        accounts = Account.query(Account.email == account_email).fetch(1)
        if accounts:
            account = accounts[0]

    access.access_code = access_code
    access.expiration = datetime.strptime(expiration, "%Y-%m-%d")
    access.account = account.key if account else None
    access.put()

    return redirect(
        url_for("admin.team_media_mod_edit", team_number=team_number, year=year)
    )

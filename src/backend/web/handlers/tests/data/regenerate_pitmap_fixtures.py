"""Regenerate the pit-map golden SVG fixtures from the JSON inputs.

Two variants are written for each input:
  *_expected_light.svg  — adaptive @media block stripped, always renders light
  *_expected_dark.svg   — adaptive @media block forced on, always renders dark

Forcing a color scheme at fixture-write time keeps PR review (and any other
non-adaptive viewer) rendering consistently, while the live route still serves
the adaptive SVG that swaps with the user's `prefers-color-scheme`.

Run from the repo root inside the dev container:

    docker compose exec tba env PYTHONPATH=/tba/src uv run --group test \\
        python src/backend/web/handlers/tests/data/regenerate_pitmap_fixtures.py
"""

from __future__ import annotations

import json
import os

from backend.common.helpers.nexus_pit_map_svg_helper import NexusEventDetailsSVGHelper

DATA_DIR = os.path.dirname(os.path.abspath(__file__))


def render(
    json_name: str, base_name: str, *, highlight: set[str] | None = None
) -> None:
    with open(os.path.join(DATA_DIR, json_name)) as f:
        map_data = json.load(f)

    nexus_event_code = json_name.removesuffix("_pitmap.json")
    template_values = NexusEventDetailsSVGHelper.template_values(
        map_data,
        nexus_event_code,
        highlight_team_keys=highlight,
    )

    from flask import Flask

    app = Flask(__name__, template_folder=os.path.join(DATA_DIR, "../../../templates"))
    with app.app_context():
        from flask import render_template

        rendered = render_template("event_pitmap.svg", **template_values)

    for suffix, transform in (
        ("_light.svg", NexusEventDetailsSVGHelper.force_light_color_scheme),
        ("_dark.svg", NexusEventDetailsSVGHelper.force_dark_color_scheme),
    ):
        out_path = os.path.join(DATA_DIR, f"{base_name}{suffix}")
        with open(out_path, "w") as f:
            f.write(transform(rendered))
        print(f"wrote {out_path}")


if __name__ == "__main__":
    render("2026nyny_pitmap.json", "2026nyny_pitmap_expected")
    render(
        "2026nyny_pitmap.json",
        "2026nyny_pitmap_team3015_expected",
        highlight={"frc3015"},
    )
    render("2026nysu_pitmap.json", "2026nysu_pitmap_expected")
    render(
        "2026nysu_pitmap.json",
        "2026nysu_pitmap_team1796_expected",
        highlight={"frc1796"},
    )
    render(
        "2026nysu_pitmap.json",
        "2026nysu_pitmap_team10922_expected",
        highlight={"frc10922"},
    )

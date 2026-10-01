from backend.common.consts.api_version import ApiMajorVersion
from backend.common.models.team import Team
from backend.common.queries.dict_converters.team_converter import TeamConverter


def test_teamConverter_v3_default_names(ndb_context) -> None:
    team = Team(id="frc254", team_number=254)

    converted = TeamConverter(team).convert(ApiMajorVersion.API_V3)

    assert converted is not None
    assert converted["key"] == "frc254"
    assert converted["nickname"] == "Team 254"
    assert converted["name"] == "Team 254"
    assert converted["motto"] is None


def test_dictToModel_v3_round_trip(ndb_context) -> None:
    team = Team(
        id="frc254",
        team_number=254,
        nickname="The Cheesy Poofs",
        name="NASA Ames Research Center",
        website="https://www.team254.com",
        rookie_year=1999,
        city="San Jose",
        state_prov="CA",
        country="USA",
        school_name="Bellarmine College Preparatory",
    )

    model = TeamConverter.dictToModel_v3(TeamConverter.teamConverter_v3(team))

    assert model.key.id() == "frc254"
    assert model.team_number == 254
    assert model.nickname == "The Cheesy Poofs"
    assert model.name == "NASA Ames Research Center"
    assert model.website == "https://www.team254.com"
    assert model.rookie_year == 1999
    assert model.motto is None
    assert model.city == "San Jose"
    assert model.state_prov == "CA"
    assert model.country == "USA"
    assert model.school_name == "Bellarmine College Preparatory"

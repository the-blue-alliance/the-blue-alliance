from typing import Optional

import pytest

from backend.common.consts.award_type import AwardType
from backend.common.helpers.award_helper import AwardHelper
from backend.common.models.award import Award


def test_organize_awards() -> None:
    a1 = Award(award_type_enum=AwardType.SAFETY, name_str="Safety",)
    a2 = Award(award_type_enum=AwardType.CHAIRMANS, name_str="Chairmans",)
    a3 = Award(award_type_enum=AwardType.WINNER, name_str="Winner",)
    assert AwardHelper.organizeAwards([a1, a2, a3]) == [a2, a3, a1]


@pytest.mark.parametrize(
    "name,award_type",
    [
        ("Chairman's", AwardType.CHAIRMANS),
        ("Chairman", AwardType.CHAIRMANS),
        ("Chairman's Award Finalist", AwardType.CHAIRMANS_FINALIST),
        ("Winner #1", AwardType.WINNER),
        ("Division Winner #2", AwardType.WINNER),
        ("Newton - Division Champion #3", AwardType.WINNER),
        ("Championship Winner #3", AwardType.WINNER),
        ("Championship Champion #4", AwardType.WINNER),
        ("Championship Champion", AwardType.WINNER),
        ("Championship Winner", AwardType.WINNER),
        ("Winner", AwardType.WINNER),
        ("Finalist #1", AwardType.FINALIST),
        ("Division Finalist #2", AwardType.FINALIST),
        ("Championship Finalist #3", AwardType.FINALIST),
        ("Championship Finalist #4", AwardType.FINALIST),
        ("Championship Finalist", AwardType.FINALIST),
        ("Finalist", AwardType.FINALIST),
        ("Dean's List Finalist #1", AwardType.DEANS_LIST),
        ("Dean's List Finalist", AwardType.DEANS_LIST),
        ("Dean's List Winner #9", AwardType.DEANS_LIST),
        ("Dean's List Winner", AwardType.DEANS_LIST),
        ("Dean's List", AwardType.DEANS_LIST),
        (
            "Excellence in Design Award sponsored by Autodesk (3D CAD)",
            AwardType.EXCELLENCE_IN_DESIGN_CAD,
        ),
        (
            "Excellence in Design Award sponsored by Autodesk (Animation)",
            AwardType.EXCELLENCE_IN_DESIGN_ANIMATION,
        ),
        ("Excellence in Design Award", AwardType.EXCELLENCE_IN_DESIGN),
        ("Dr. Bart Kamen Memorial Scholarship #1", AwardType.BART_KAMEN_MEMORIAL),
        (
            "Media and Technology Award sponsored by Comcast",
            AwardType.MEDIA_AND_TECHNOLOGY,
        ),
        ("Make It Loud Award", AwardType.MAKE_IT_LOUD),
        ("Founder's Award", AwardType.FOUNDERS),
        ("Championship - Web Site Award", AwardType.WEBSITE),
        (
            "Recognition of Extraordinary Service",
            AwardType.RECOGNITION_OF_EXTRAORDINARY_SERVICE,
        ),
        ("Outstanding Cart Award", AwardType.OUTSTANDING_CART),
        ("Wayne State University Aim Higher Award", AwardType.WSU_AIM_HIGHER),
        (
            'Delphi "Driving Tommorow\'s Technology" Award',
            AwardType.DRIVING_TOMORROWS_TECHNOLOGY,
        ),
        ("Delphi Drive Tommorows Technology", AwardType.DRIVING_TOMORROWS_TECHNOLOGY),
        ("Kleiner, Perkins, Caufield and Byers", AwardType.ENTREPRENEURSHIP),
        ("Leadership in Control Award", AwardType.LEADERSHIP_IN_CONTROL),
        ("#1 Seed", AwardType.NUM_1_SEED),
        ("Incredible Play Award", AwardType.INCREDIBLE_PLAY),
        ("People's Choice Animation Award", AwardType.PEOPLES_CHOICE_ANIMATION),
        ("Autodesk Award for Visualization - Grand Prize", AwardType.VISUALIZATION),
        (
            "Autodesk Award for Visualization - Rising Star",
            AwardType.VISUALIZATION_RISING_STAR,
        ),
        ("Some Random Award Winner", None),
        ("Random Champion", None),
        ("An Award", None),
    ],
)
def test_parse_award_type(name: str, award_type: Optional[AwardType]) -> None:
    assert AwardHelper.parse_award_type(name) == award_type

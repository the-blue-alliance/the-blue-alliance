import pytest

from backend.common.consts.event_type import EventType
from backend.common.helpers.event_short_name_helper import EventShortNameHelper
from backend.common.manipulators.district_manipulator import DistrictManipulator
from backend.common.models.district import District


@pytest.fixture(autouse=True)
def create_districts(ndb_stub, taskqueue_stub):
    districts = []
    for code in [
        "mar",
        "isr",
        "nc",
        "ne",
        "pnw",
        "pch",
        "chs",
        "in",
        "ont",
        "fim",
        "tx",
    ]:
        year = 2017
        districts.append(
            District(
                id=District.render_key_name(year, code),
                year=year,
                abbreviation=code,
            )
        )
    DistrictManipulator.createOrUpdate(districts)


def test_event_get_short_name():
    # Edge cases.
    assert (
        EventShortNameHelper.get_short_name("  { Random 2.718 stuff! }  ")
        == "{ Random 2.718 stuff! }"
    )
    assert (
        EventShortNameHelper.get_short_name("IN District -Bee's Knee's LX  ")
        == "Bee's Knee's LX"
    )
    assert (
        EventShortNameHelper.get_short_name(
            "MAR District - Brussels Int'l Event sponsored by Sprouts"
        )
        == "Brussels Int'l"
    )
    assert (
        EventShortNameHelper.get_short_name(
            "FIM District - Brussels Int'l Eventapalooza sponsored by TBA"
        )
        == "Brussels Int'l"
    )
    assert (
        EventShortNameHelper.get_short_name(
            "NE District - ReallyBigEvent Scaling Up Every Year"
        )
        == "ReallyBig"
    )
    assert EventShortNameHelper.get_short_name("PNW District -  Event!  ") == "Event!"

    assert (
        EventShortNameHelper.get_short_name(
            "FRC Detroit FIRST Robotics District Competition"
        )
        == "Detroit"
    )
    assert (
        EventShortNameHelper.get_short_name(
            "FIRST Robotics Detroit FRC State Championship"
        )
        == "Detroit"
    )
    assert (
        EventShortNameHelper.get_short_name("Maui FIRST Robotics Regional and Luau")
        == "Maui"
    )
    assert (
        EventShortNameHelper.get_short_name(
            "California State Surf and Turf sponsored by TBA"
        )
        == "California"
    )
    assert (
        EventShortNameHelper.get_short_name("CarTalk Plaza Tournament")
        == "CarTalk Plaza"
    )
    assert EventShortNameHelper.get_short_name("IRI FRC Be-all and End-all") == "IRI"
    assert EventShortNameHelper.get_short_name("   Ada    Field  ") == "Ada"
    assert (
        EventShortNameHelper.get_short_name(" FIRST Robotics Einstein Field Equations ")
        == "Einstein"
    )
    assert (
        EventShortNameHelper.get_short_name(
            "FRC Martin Luther King Jr. Region Championship"
        )
        == "Martin Luther King Jr."
    )
    assert (
        EventShortNameHelper.get_short_name(
            "PNW   Ada Lovelace    Tournament of Software  "
        )
        == "Ada Lovelace"
    )
    assert (
        EventShortNameHelper.get_short_name(
            "\tPNW   Ada Lovelace    Tournament of Software  "
        )
        == "Ada Lovelace"
    )
    assert (
        EventShortNameHelper.get_short_name(
            " MAR FIRST Robotics   Rosa Parks    FRC Tournament of Roses  "
        )
        == "Rosa Parks"
    )
    assert (
        EventShortNameHelper.get_short_name("Washington D.C. FIRST Robotics Region")
        == "Washington D.C."
    )
    assert (
        EventShortNameHelper.get_short_name("Washington D.C. FIRST Robotics Region.")
        == "Washington D.C."
    )
    assert (
        EventShortNameHelper.get_short_name(
            "Washington D.C. FIRST Robotics Regiontonian"
        )
        == "Washington D.C. FIRST Robotics Regiontonian"
    )  # Does not match "Region\b"

    # Tests from various years
    assert (
        EventShortNameHelper.get_short_name("FIRST Robotics Competition")
        == "FIRST Robotics Competition"
    )
    assert (
        EventShortNameHelper.get_short_name("National Championship")
        == "National Championship"
    )
    assert (
        EventShortNameHelper.get_short_name("New England Tournament") == "New England"
    )
    assert (
        EventShortNameHelper.get_short_name("FIRST National Championship")
        == "FIRST National Championship"
    )
    assert (
        EventShortNameHelper.get_short_name("Motorola Midwest Regional")
        == "Motorola Midwest"
    )
    assert (
        EventShortNameHelper.get_short_name("DEKA New England Regional")
        == "DEKA New England"
    )
    assert (
        EventShortNameHelper.get_short_name("Johnson & Johnson Mid-Atlantic Regional")
        == "Johnson & Johnson Mid-Atlantic"
    )
    assert EventShortNameHelper.get_short_name("Great Lakes Regional") == "Great Lakes"
    assert EventShortNameHelper.get_short_name("New England Regional") == "New England"
    assert EventShortNameHelper.get_short_name("Southwest Regional") == "Southwest"
    assert EventShortNameHelper.get_short_name("NASA Ames Regional") == "NASA Ames"
    assert (
        EventShortNameHelper.get_short_name("Kennedy Space Center Regional")
        == "Kennedy Space Center"
    )
    assert (
        EventShortNameHelper.get_short_name("UTC New England Regional")
        == "UTC New England"
    )
    assert (
        EventShortNameHelper.get_short_name("Philadelphia Alliance Regional")
        == "Philadelphia Alliance"
    )
    assert (
        EventShortNameHelper.get_short_name("Kennedy Space Center Southeast Regional")
        == "Kennedy Space Center Southeast"
    )
    assert EventShortNameHelper.get_short_name("Long Island Regional") == "Long Island"
    assert EventShortNameHelper.get_short_name("Lone Star Regional") == "Lone Star"
    assert (
        EventShortNameHelper.get_short_name("NASA Langley/VCU Regional")
        == "NASA Langley/VCU"
    )
    assert EventShortNameHelper.get_short_name("Archimedes Field") == "Archimedes"
    assert (
        EventShortNameHelper.get_short_name("Southern California Regional")
        == "Southern California"
    )
    assert (
        EventShortNameHelper.get_short_name("Silicon Valley Regional")
        == "Silicon Valley"
    )
    assert (
        EventShortNameHelper.get_short_name("UTC/New England Regional")
        == "UTC/New England"
    )
    assert EventShortNameHelper.get_short_name("Curie Field") == "Curie"
    assert (
        EventShortNameHelper.get_short_name("NASA KSC Southeast Regional")
        == "NASA KSC Southeast"
    )
    assert EventShortNameHelper.get_short_name("Galileo Field") == "Galileo"
    assert (
        EventShortNameHelper.get_short_name("West Michigan Regional") == "West Michigan"
    )
    assert EventShortNameHelper.get_short_name("Newton Field") == "Newton"
    assert (
        EventShortNameHelper.get_short_name("J&J Mid-Atlantic Regional")
        == "J&J Mid-Atlantic"
    )
    assert (
        EventShortNameHelper.get_short_name("New York City Regional") == "New York City"
    )
    assert (
        EventShortNameHelper.get_short_name("NASA Langley Regional") == "NASA Langley"
    )
    assert (
        EventShortNameHelper.get_short_name("SBPLI Long Island Regional")
        == "SBPLI Long Island"
    )
    assert (
        EventShortNameHelper.get_short_name("Western Michigan Regional")
        == "Western Michigan"
    )
    assert EventShortNameHelper.get_short_name("St. Louis Regional") == "St. Louis"
    assert (
        EventShortNameHelper.get_short_name("J&J Mid Atlantic Regional")
        == "J&J Mid Atlantic"
    )
    assert EventShortNameHelper.get_short_name("Buckeye Regional") == "Buckeye"
    assert EventShortNameHelper.get_short_name("Canadian Regional") == "Canadian"
    assert (
        EventShortNameHelper.get_short_name("NASA Langley / VCU Regional")
        == "NASA Langley / VCU"
    )
    assert (
        EventShortNameHelper.get_short_name("Pacific Northwest Regional")
        == "Pacific Northwest"
    )
    assert EventShortNameHelper.get_short_name("Arizona Regional") == "Arizona"
    assert EventShortNameHelper.get_short_name("Einstein Field") == "Einstein"
    assert (
        EventShortNameHelper.get_short_name("Central Florida Regional")
        == "Central Florida"
    )
    assert EventShortNameHelper.get_short_name("Peachtree Regional") == "Peachtree"
    assert EventShortNameHelper.get_short_name("Midwest Regional") == "Midwest"
    assert EventShortNameHelper.get_short_name("Chesapeake Regional") == "Chesapeake"
    assert (
        EventShortNameHelper.get_short_name("BAE SYSTEMS Granite State Regional")
        == "BAE SYSTEMS Granite State"
    )
    assert (
        EventShortNameHelper.get_short_name("Philadelphia Regional") == "Philadelphia"
    )
    assert EventShortNameHelper.get_short_name("Pittsburgh Regional") == "Pittsburgh"
    assert EventShortNameHelper.get_short_name("Sacramento Regional") == "Sacramento"
    assert EventShortNameHelper.get_short_name("NASA / VCU Regional") == "NASA / VCU"
    assert EventShortNameHelper.get_short_name("Colorado Regional") == "Colorado"
    assert EventShortNameHelper.get_short_name("Detroit Regional") == "Detroit"
    assert EventShortNameHelper.get_short_name("Florida Regional") == "Florida"
    assert EventShortNameHelper.get_short_name("New Jersey Regional") == "New Jersey"
    assert (
        EventShortNameHelper.get_short_name("Greater Toronto Regional")
        == "Greater Toronto"
    )
    assert EventShortNameHelper.get_short_name("Palmetto Regional") == "Palmetto"
    assert EventShortNameHelper.get_short_name("Boilermaker Regional") == "Boilermaker"
    assert (
        EventShortNameHelper.get_short_name(
            "GM/Technion University Israel Pilot Regional"
        )
        == "GM/Technion University Israel Pilot"
    )
    assert EventShortNameHelper.get_short_name("Las Vegas Regional") == "Las Vegas"
    assert (
        EventShortNameHelper.get_short_name("Finger Lakes Regional") == "Finger Lakes"
    )
    assert EventShortNameHelper.get_short_name("Waterloo Regional") == "Waterloo"
    assert (
        EventShortNameHelper.get_short_name("GM/Technion Israel Regional")
        == "GM/Technion Israel"
    )
    assert EventShortNameHelper.get_short_name("Boston Regional") == "Boston"
    assert (
        EventShortNameHelper.get_short_name("Davis Sacramento Regional")
        == "Davis Sacramento"
    )
    assert EventShortNameHelper.get_short_name("Wisconsin Regional") == "Wisconsin"
    assert EventShortNameHelper.get_short_name("Brazil Pilot") == "Brazil Pilot"
    assert EventShortNameHelper.get_short_name("Los Angeles Regional") == "Los Angeles"
    assert (
        EventShortNameHelper.get_short_name("UTC Connecticut Regional")
        == "UTC Connecticut"
    )
    assert (
        EventShortNameHelper.get_short_name("Greater Kansas City Regional")
        == "Greater Kansas City"
    )
    assert EventShortNameHelper.get_short_name("Bayou Regional") == "Bayou"
    assert EventShortNameHelper.get_short_name("San Diego Regional") == "San Diego"
    assert EventShortNameHelper.get_short_name("Brazil Regional") == "Brazil"
    assert EventShortNameHelper.get_short_name("Connecticut Regional") == "Connecticut"
    assert EventShortNameHelper.get_short_name("Hawaii Regional") == "Hawaii"
    assert EventShortNameHelper.get_short_name("Israel Regional") == "Israel"
    assert EventShortNameHelper.get_short_name("Minnesota Regional") == "Minnesota"
    assert (
        EventShortNameHelper.get_short_name("BAE Systems Granite State Regional")
        == "BAE Systems Granite State"
    )
    assert (
        EventShortNameHelper.get_short_name("Oklahoma City Regional") == "Oklahoma City"
    )
    assert EventShortNameHelper.get_short_name("Oregon Regional") == "Oregon"
    assert (
        EventShortNameHelper.get_short_name("UC Davis Sacramento Regional")
        == "UC Davis Sacramento"
    )
    assert (
        EventShortNameHelper.get_short_name("Microsoft Seattle Regional")
        == "Microsoft Seattle"
    )
    assert (
        EventShortNameHelper.get_short_name(
            "Dallas Regional, Sponsored by JCPenney and the JCPenney Afterschool Fund"
        )
        == "Dallas"
    )
    assert (
        EventShortNameHelper.get_short_name("Washington DC  Regional")
        == "Washington DC"
    )
    assert (
        EventShortNameHelper.get_short_name(
            "Detroit FIRST Robotics District Competition"
        )
        == "Detroit"
    )
    assert (
        EventShortNameHelper.get_short_name(
            "Cass Tech FIRST Robotics District Competition"
        )
        == "Cass Tech"
    )
    assert (
        EventShortNameHelper.get_short_name(
            "Kettering University FIRST Robotics District Competition"
        )
        == "Kettering University"
    )
    assert (
        EventShortNameHelper.get_short_name(
            "Michigan FIRST Robotics Competition State Championship"
        )
        == "Michigan"
    )
    assert (
        EventShortNameHelper.get_short_name(
            "Lansing FIRST Robotics District Competition"
        )
        == "Lansing"
    )
    assert (
        EventShortNameHelper.get_short_name(
            "Traverse City FIRST Robotics District Competition"
        )
        == "Traverse City"
    )
    assert (
        EventShortNameHelper.get_short_name(
            "West Michigan FIRST Robotics District Competition"
        )
        == "West Michigan"
    )
    assert (
        EventShortNameHelper.get_short_name("Minnesota 10000 Lakes Regional")
        == "Minnesota 10000 Lakes"
    )
    assert (
        EventShortNameHelper.get_short_name("Minnesota North Star Regional")
        == "Minnesota North Star"
    )
    assert (
        EventShortNameHelper.get_short_name("BAE Granite State Regional")
        == "BAE Granite State"
    )
    assert (
        EventShortNameHelper.get_short_name("Troy FIRST Robotics District Competition")
        == "Troy"
    )
    assert EventShortNameHelper.get_short_name("NASA VCU Regional") == "NASA VCU"
    assert (
        EventShortNameHelper.get_short_name(
            "Northeast Utilities FIRST Connecticut Regional"
        )
        == "Northeast Utilities Connecticut"
    )
    assert (
        EventShortNameHelper.get_short_name(
            "Dallas Regional sponsored by JCPenney and the JCPenney Afterschool Fund"
        )
        == "Dallas"
    )
    assert (
        EventShortNameHelper.get_short_name("Hawaii Regional sponsored by BAE Systems")
        == "Hawaii"
    )
    assert (
        EventShortNameHelper.get_short_name("North Carolina Regional")
        == "North Carolina"
    )
    assert EventShortNameHelper.get_short_name("Oklahoma Regional") == "Oklahoma"
    assert (
        EventShortNameHelper.get_short_name("Autodesk Oregon Regional")
        == "Autodesk Oregon"
    )
    assert (
        EventShortNameHelper.get_short_name(
            "Silicon Valley Regional sponsored by Google and BAE Systems"
        )
        == "Silicon Valley"
    )
    assert (
        EventShortNameHelper.get_short_name("Utah Regional sponsored by NASA & Platt")
        == "Utah"
    )
    assert EventShortNameHelper.get_short_name("Virginia Regional") == "Virginia"
    assert (
        EventShortNameHelper.get_short_name(
            "Ann Arbor FIRST Robotics District Competition"
        )
        == "Ann Arbor"
    )
    assert EventShortNameHelper.get_short_name("WPI Regional") == "WPI"
    assert (
        EventShortNameHelper.get_short_name("Dallas Regional sponsored by jcpenney")
        == "Dallas"
    )
    assert (
        EventShortNameHelper.get_short_name("Lake Superior Regional") == "Lake Superior"
    )
    assert (
        EventShortNameHelper.get_short_name(
            "Michigan FIRST Robotics District Competition State Championship"
        )
        == "Michigan"
    )
    assert (
        EventShortNameHelper.get_short_name("BAE Systems/Granite State Regional")
        == "BAE Systems/Granite State"
    )
    assert (
        EventShortNameHelper.get_short_name(
            "Waterford FIRST Robotics District Competition"
        )
        == "Waterford"
    )
    assert (
        EventShortNameHelper.get_short_name("Greater Toronto East Regional")
        == "Greater Toronto East"
    )
    assert (
        EventShortNameHelper.get_short_name("Greater Toronto West Regional")
        == "Greater Toronto West"
    )
    assert EventShortNameHelper.get_short_name("Alamo Regional") == "Alamo"
    assert (
        EventShortNameHelper.get_short_name("Niles FIRST Robotics District Competition")
        == "Niles"
    )
    assert (
        EventShortNameHelper.get_short_name("Smoky Mountain Regional")
        == "Smoky Mountain"
    )
    assert (
        EventShortNameHelper.get_short_name(
            "Utah Regional co-sponsored by NASA and Platt"
        )
        == "Utah"
    )
    assert (
        EventShortNameHelper.get_short_name("Seattle Olympic Regional")
        == "Seattle Olympic"
    )
    assert (
        EventShortNameHelper.get_short_name("Seattle Cascade Regional")
        == "Seattle Cascade"
    )
    assert (
        EventShortNameHelper.get_short_name(
            "Livonia FIRST Robotics District Competition"
        )
        == "Livonia"
    )
    assert (
        EventShortNameHelper.get_short_name("Central Valley Regional")
        == "Central Valley"
    )
    assert (
        EventShortNameHelper.get_short_name(
            "Dallas East Regional sponsored by jcpenney"
        )
        == "Dallas East"
    )
    assert (
        EventShortNameHelper.get_short_name(
            "Dallas West Regional sponsored by jcpenney"
        )
        == "Dallas West"
    )
    assert EventShortNameHelper.get_short_name("Orlando Regional") == "Orlando"
    assert (
        EventShortNameHelper.get_short_name("Michigan FRC State Championship")
        == "Michigan"
    )
    assert (
        EventShortNameHelper.get_short_name(
            "Gull Lake FIRST Robotics District Competition"
        )
        == "Gull Lake"
    )
    assert (
        EventShortNameHelper.get_short_name(
            "Rutgers University FIRST Robotics District Competition"
        )
        == "Rutgers University"
    )
    assert (
        EventShortNameHelper.get_short_name(
            "Mount Olive FIRST Robotics District Competition"
        )
        == "Mount Olive"
    )
    assert (
        EventShortNameHelper.get_short_name(
            "Lenape FIRST Robotics District Competition"
        )
        == "Lenape"
    )
    assert EventShortNameHelper.get_short_name("Queen City Regional") == "Queen City"
    assert (
        EventShortNameHelper.get_short_name(
            "Mid-Atlantic Robotics FRC Region Championship"
        )
        == "Mid-Atlantic Robotics"
    )
    assert (
        EventShortNameHelper.get_short_name(
            "Hatboro-Horsham FIRST Robotics District Competition"
        )
        == "Hatboro-Horsham"
    )
    assert (
        EventShortNameHelper.get_short_name(
            "Chestnut Hill FIRST Robotics District Competition"
        )
        == "Chestnut Hill"
    )
    assert (
        EventShortNameHelper.get_short_name(
            "Festival de Robotique FRC a Montreal Regional"
        )
        == "Festival de Robotique"
    )
    assert (
        EventShortNameHelper.get_short_name("South Florida Regional") == "South Florida"
    )
    assert (
        EventShortNameHelper.get_short_name("Smoky Mountains Regional")
        == "Smoky Mountains"
    )
    assert EventShortNameHelper.get_short_name("Spokane Regional") == "Spokane"
    assert (
        EventShortNameHelper.get_short_name(
            "Northville FIRST Robotics District Competition"
        )
        == "Northville"
    )
    assert (
        EventShortNameHelper.get_short_name("Western Canadian FRC Regional")
        == "Western Canadian"
    )
    assert EventShortNameHelper.get_short_name("Razorback Regional") == "Razorback"
    assert EventShortNameHelper.get_short_name("Phoenix Regional") == "Phoenix"
    assert (
        EventShortNameHelper.get_short_name(
            "Los Angeles Regional sponsored by The Roddenberry Foundation"
        )
        == "Los Angeles"
    )
    assert (
        EventShortNameHelper.get_short_name("Inland Empire Regional") == "Inland Empire"
    )
    assert (
        EventShortNameHelper.get_short_name("Connecticut Regional sponsored by UTC")
        == "Connecticut"
    )
    assert EventShortNameHelper.get_short_name("Crossroads Regional") == "Crossroads"
    assert EventShortNameHelper.get_short_name("Pine Tree Regional") == "Pine Tree"
    assert (
        EventShortNameHelper.get_short_name(
            "Bedford FIRST Robotics District Competition"
        )
        == "Bedford"
    )
    assert (
        EventShortNameHelper.get_short_name(
            "Grand Blanc FIRST Robotics District Competition"
        )
        == "Grand Blanc"
    )
    assert (
        EventShortNameHelper.get_short_name(
            "St Joseph FIRST Robotics District Competition"
        )
        == "St Joseph"
    )
    assert (
        EventShortNameHelper.get_short_name("Northern Lights Regional")
        == "Northern Lights"
    )
    assert (
        EventShortNameHelper.get_short_name(
            "Bridgewater-Raritan FIRST Robotics District Competition"
        )
        == "Bridgewater-Raritan"
    )
    assert (
        EventShortNameHelper.get_short_name("TCNJ FIRST Robotics District Competition")
        == "TCNJ"
    )
    assert (
        EventShortNameHelper.get_short_name(
            "Lenape Seneca FIRST Robotics District Competition"
        )
        == "Lenape Seneca"
    )
    assert (
        EventShortNameHelper.get_short_name(
            "Springside - Chestnut Hill FIRST Robotics District Competition"
        )
        == "Springside - Chestnut Hill"
    )
    assert (
        EventShortNameHelper.get_short_name(
            "Festival de Robotique FRC de Montreal Regional"
        )
        == "Festival de Robotique"
    )
    assert EventShortNameHelper.get_short_name("Dallas Regional") == "Dallas"
    assert EventShortNameHelper.get_short_name("Hub City Regional") == "Hub City"
    assert (
        EventShortNameHelper.get_short_name(
            "Alamo Regional sponsored by Rackspace Hosting"
        )
        == "Alamo"
    )
    assert (
        EventShortNameHelper.get_short_name(
            "Utah Regional co-sponsored by the Larry H. Miller Group & Platt"
        )
        == "Utah"
    )
    assert EventShortNameHelper.get_short_name("Seattle Regional") == "Seattle"
    assert (
        EventShortNameHelper.get_short_name("Central Washington Regional")
        == "Central Washington"
    )
    assert (
        EventShortNameHelper.get_short_name("Western Canada Regional")
        == "Western Canada"
    )
    assert EventShortNameHelper.get_short_name("Arkansas Regional") == "Arkansas"
    assert EventShortNameHelper.get_short_name("Groton District Event") == "Groton"
    assert EventShortNameHelper.get_short_name("Hartford District Event") == "Hartford"
    assert (
        EventShortNameHelper.get_short_name("Southington District Event")
        == "Southington"
    )
    assert EventShortNameHelper.get_short_name("Greater DC Regional") == "Greater DC"
    assert (
        EventShortNameHelper.get_short_name("Central Illinois Regional")
        == "Central Illinois"
    )
    assert (
        EventShortNameHelper.get_short_name("Northeastern University District Event")
        == "Northeastern University"
    )
    assert EventShortNameHelper.get_short_name("WPI District Event") == "WPI"
    assert (
        EventShortNameHelper.get_short_name("Pine Tree District Event") == "Pine Tree"
    )
    assert (
        EventShortNameHelper.get_short_name(
            "Center Line FIRST Robotics District Competition"
        )
        == "Center Line"
    )
    assert (
        EventShortNameHelper.get_short_name(
            "Escanaba FIRST Robotics District Competition"
        )
        == "Escanaba"
    )
    assert (
        EventShortNameHelper.get_short_name(
            "Howell FIRST Robotics District Competition"
        )
        == "Howell"
    )
    assert (
        EventShortNameHelper.get_short_name(
            "St. Joseph FIRST Robotics District Competition"
        )
        == "St. Joseph"
    )
    assert (
        EventShortNameHelper.get_short_name(
            "Southfield FIRST Robotics District Competition"
        )
        == "Southfield"
    )
    assert EventShortNameHelper.get_short_name("Mexico City Regional") == "Mexico City"
    assert (
        EventShortNameHelper.get_short_name("New England FRC Region Championship")
        == "New England"
    )
    assert EventShortNameHelper.get_short_name("UNH District Event") == "UNH"
    assert (
        EventShortNameHelper.get_short_name("Granite State District Event")
        == "Granite State"
    )
    assert (
        EventShortNameHelper.get_short_name(
            "MAR FIRST Robotics Bridgewater-Raritan District Competition"
        )
        == "Bridgewater-Raritan"
    )
    assert (
        EventShortNameHelper.get_short_name(
            "MAR FIRST Robotics Clifton District Competition"
        )
        == "Clifton"
    )
    assert (
        EventShortNameHelper.get_short_name(
            "MAR FIRST Robotics Mt. Olive District Competition"
        )
        == "Mt. Olive"
    )
    assert (
        EventShortNameHelper.get_short_name(
            "MAR FIRST Robotics Lenape-Seneca District Competition"
        )
        == "Lenape-Seneca"
    )
    assert (
        EventShortNameHelper.get_short_name("New York Tech Valley Regional")
        == "New York Tech Valley"
    )
    assert EventShortNameHelper.get_short_name("North Bay Regional") == "North Bay"
    assert (
        EventShortNameHelper.get_short_name("Windsor Essex Great Lakes Regional")
        == "Windsor Essex Great Lakes"
    )
    assert (
        EventShortNameHelper.get_short_name(
            "PNW FIRST Robotics Oregon City District Event"
        )
        == "Oregon City"
    )
    assert (
        EventShortNameHelper.get_short_name(
            "PNW FIRST Robotics Oregon State University District Event"
        )
        == "Oregon State University"
    )
    assert (
        EventShortNameHelper.get_short_name(
            "PNW FIRST Robotics Wilsonville District Event"
        )
        == "Wilsonville"
    )
    assert (
        EventShortNameHelper.get_short_name(
            "MAR FIRST Robotics Hatboro-Horsham District Competition"
        )
        == "Hatboro-Horsham"
    )
    assert (
        EventShortNameHelper.get_short_name(
            "MAR FIRST Robotics Springside Chestnut Hill District Competition"
        )
        == "Springside Chestnut Hill"
    )
    assert (
        EventShortNameHelper.get_short_name("Greater Pittsburgh Regional")
        == "Greater Pittsburgh"
    )
    assert (
        EventShortNameHelper.get_short_name("Autodesk PNW FRC Championship")
        == "Autodesk PNW"
    )
    assert (
        EventShortNameHelper.get_short_name("Rhode Island District Event")
        == "Rhode Island"
    )
    assert EventShortNameHelper.get_short_name("Utah Regional") == "Utah"
    assert (
        EventShortNameHelper.get_short_name("PNW FIRST Robotics Auburn District Event")
        == "Auburn"
    )
    assert (
        EventShortNameHelper.get_short_name(
            "PNW FIRST Robotics Auburn Mountainview District Event"
        )
        == "Auburn Mountainview"
    )
    assert (
        EventShortNameHelper.get_short_name(
            "PNW FIRST Robotics Eastern Washington University District Event"
        )
        == "Eastern Washington University"
    )
    assert (
        EventShortNameHelper.get_short_name(
            "PNW FIRST Robotics Central Washington University District Event"
        )
        == "Central Washington University"
    )
    assert (
        EventShortNameHelper.get_short_name(
            "PNW FIRST Robotics Mt. Vernon District Event"
        )
        == "Mt. Vernon"
    )
    assert (
        EventShortNameHelper.get_short_name(
            "PNW FIRST Robotics Shorewood District Event"
        )
        == "Shorewood"
    )
    assert (
        EventShortNameHelper.get_short_name(
            "PNW FIRST Robotics Glacier Peak District Event"
        )
        == "Glacier Peak"
    )
    # 2015 edge cases
    assert (
        EventShortNameHelper.get_short_name("FIM District - Howell Event") == "Howell"
    )
    assert (
        EventShortNameHelper.get_short_name("NE District - Granite State Event")
        == "Granite State"
    )
    assert (
        EventShortNameHelper.get_short_name("PNW District - Oregon City Event")
        == "Oregon City"
    )
    assert (
        EventShortNameHelper.get_short_name("IN District -Indianapolis")
        == "Indianapolis"
    )
    assert (
        EventShortNameHelper.get_short_name("MAR District - Mt. Olive Event")
        == "Mt. Olive"
    )
    assert (
        EventShortNameHelper.get_short_name(
            "Israel Regional - see Site Info for additional information"
        )
        == "Israel"
    )
    assert (
        EventShortNameHelper.get_short_name(
            "IN District - Kokomo City of Firsts Event sponsored by AndyMark"
        )
        == "Kokomo City of Firsts"
    )
    # 2017 edge cases
    assert (
        EventShortNameHelper.get_short_name("ONT District - McMaster University Event")
        == "McMaster University"
    )
    assert (
        EventShortNameHelper.get_short_name("FIRST Ontario Provincial Championship")
        == "Ontario"
    )
    assert (
        EventShortNameHelper.get_short_name(
            "FIM District - Kettering University Event #1"
        )
        == "Kettering University #1"
    )
    assert EventShortNameHelper.get_short_name("ISR District Event #1") == "ISR #1"
    # 2018 edge cases
    assert (
        EventShortNameHelper.get_short_name("PNW District Clackamas Academy Event")
        == "Clackamas Academy"
    )
    # 2019 edge cases
    assert (
        EventShortNameHelper.get_short_name("FMA District Hatboro-Horsham Event")
        == "Hatboro-Horsham"
    )
    assert EventShortNameHelper.get_short_name("FIT District Austin Event") == "Austin"
    # 2020 edge cases
    assert (
        EventShortNameHelper.get_short_name("***SUSPENDED*** Silicon Valley Regional")
        == "Silicon Valley"
    )
    # 2022 edge cases
    assert (
        EventShortNameHelper.get_short_name("Festival de Robotique Regional Day 1")
        == "Festival de Robotique Day 1"
    )
    assert (
        EventShortNameHelper.get_short_name("Festival de Robotique Regional Day 23")
        == "Festival de Robotique Day 23"
    )
    # 2023 edge cases
    assert (
        EventShortNameHelper.get_short_name(
            "FIM District Kettering University Event #1 presented by Ford"
        )
        == "Kettering University #1"
    )
    assert (
        EventShortNameHelper.get_short_name(
            "FIRST in Michigan State Championship presented by DTE Foundation"
        )
        == "Michigan"
    )
    assert (
        EventShortNameHelper.get_short_name(
            "FIRST In Texas District Championship presented by Phillips 66"
        )
        == "Texas"
    )
    assert (
        EventShortNameHelper.get_short_name("FIRST Ontario Provincial Championship")
        == "Ontario"
    )
    assert (
        EventShortNameHelper.get_short_name("New England FIRST District Championship")
        == "New England"
    )
    assert (
        EventShortNameHelper.get_short_name(
            "FIRST in Michigan State Championship presented by DTE Foundation - APTIV Division",
            event_type=EventType.DISTRICT_CMP_DIVISION,
        )
        == "MSC - APTIV"
    )
    assert (
        EventShortNameHelper.get_short_name(
            "FIRST In Texas District Championship presented by Phillips 66 - MERCURY Division",
            event_type=EventType.DISTRICT_CMP_DIVISION,
        )
        == "TDC - MERCURY"
    )
    assert (
        EventShortNameHelper.get_short_name(
            "FIRST Ontario Provincial Championship - SCIENCE Division",
            event_type=EventType.DISTRICT_CMP_DIVISION,
        )
        == "OPC - SCIENCE"
    )
    assert (
        EventShortNameHelper.get_short_name(
            "New England FIRST District Championship - MEIR Division",
            event_type=EventType.DISTRICT_CMP_DIVISION,
        )
        == "NEDC - MEIR"
    )
    assert (
        EventShortNameHelper.get_short_name("FIRST Indiana State Championship")
        == "Indiana"
    )
    # 2024 edge cases
    assert (
        EventShortNameHelper.get_short_name("2024 FRC Taiwan Playoff", year=2024)
        == "FRC Taiwan Playoff"
    )

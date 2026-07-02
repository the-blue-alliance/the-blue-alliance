from typing import Dict

from backend.common.models.district_advancement import AdvancementCounts
from backend.common.models.keys import DistrictAbbreviation, Year

# Number of teams per district that qualify for DCMP/WCMP, as specified in the FIRST manual.
# This is NOT guaranteed to be the number of teams that *actually* attended the events from each district.
# There are other factors that can affect the real number, such as late drops, CMP waitlist additions, pre-qualification, etc.
FIRST_MANUAL_DISTRICT_ADVANCEMENT_COUNTS: Dict[
    Year, Dict[DistrictAbbreviation, AdvancementCounts]
] = {
    # https://www.chiefdelphi.com/t/new-first-competition-structure-in-michigan/90414/67
    2009: {"fim": {"dcmp": 64, "cmp": 18}},
    # https://web.archive.org/web/20100301091136/http://www.firstinmichigan.org/filemgmt_data/files/FiM_Rules_Supplement_2010_rev4.pdf
    2010: {"fim": {"dcmp": 64, "cmp": 18}},
    # https://web.archive.org/web/20150316061757/http://firstinmichigan.org/FRC_2011/2011_Rules_Supplement.pdf
    2011: {"fim": {"dcmp": 64, "cmp": 18}},
    2012: {
        # https://web.archive.org/web/20120316080915/http://firstinmichigan.org/FRC_2012/2012_Rules_Supplement.pdf
        "fim": {"dcmp": 64, "cmp": 18},
        # https://docs.google.com/spreadsheets/d/1s087OqNmn4xS_coJCsqX8bFfSPTKDocORiikkBvkXiE/edit?gid=595085150#gid=595085150
        "fma": {"dcmp": 53, "cmp": 12},
    },
    2013: {
        # https://web.archive.org/web/20130903031011/http://firstinmichigan.org/FRC_2013/2013_Rules_Supplement.pdf
        "fim": {"dcmp": 64, "cmp": 27},
        # https://docs.google.com/spreadsheets/d/1s087OqNmn4xS_coJCsqX8bFfSPTKDocORiikkBvkXiE/edit?gid=595085150#gid=595085150
        "fma": {"dcmp": 49, "cmp": 14},
    },
    # https://web.archive.org/web/20140727170559/http://www.usfirst.org/roboticsprograms/frc/blog-standard-district-points-ranking-system%E2%80%93more-info
    2014: {
        "fim": {"dcmp": 64, "cmp": 32},
        "fma": {"dcmp": 55, "cmp": 18},
        "ne": {"dcmp": 53, "cmp": 24},
        "pnw": {"dcmp": 63, "cmp": 24},
    },
    # From the manual
    2015: {
        "fim": {"dcmp": 102, "cmp": 68},
        "fin": {"dcmp": 32, "cmp": 10},
        "fma": {"dcmp": 55, "cmp": 25},
        "ne": {"dcmp": 60, "cmp": 35},
        "pnw": {"dcmp": 64, "cmp": 31},
    },
    # From the manual
    2016: {
        "fch": {"dcmp": 58, "cmp": 25},
        "fim": {"dcmp": 102, "cmp": 76},
        "fin": {"dcmp": 32, "cmp": 9},
        "fma": {"dcmp": 60, "cmp": 22},
        "fnc": {"dcmp": 32, "cmp": 10},
        "ne": {"dcmp": 64, "cmp": 34},
        "pch": {"dcmp": 45, "cmp": 12},
        "pnw": {"dcmp": 64, "cmp": 30},
    },
    # From the manual
    2017: {
        "fch": {"dcmp": 58, "cmp": 23},
        "fim": {"dcmp": 160, "cmp": 82},
        "fin": {"dcmp": 32, "cmp": 10},
        "fma": {"dcmp": 60, "cmp": 22},
        "fnc": {"dcmp": 32, "cmp": 15},
        "isr": {"dcmp": 45, "cmp": 16},
        "ne": {"dcmp": 64, "cmp": 37},
        "ont": {"dcmp": 60, "cmp": 29},
        "pch": {"dcmp": 45, "cmp": 18},
        "pnw": {"dcmp": 64, "cmp": 39},
    },
    # From the manual
    2018: {
        "fch": {"dcmp": 60, "cmp": 21},
        "fim": {"dcmp": 160, "cmp": 89},
        "fin": {"dcmp": 32, "cmp": 9},
        "fma": {"dcmp": 60, "cmp": 22},
        "fnc": {"dcmp": 32, "cmp": 14},
        "isr": {"dcmp": 45, "cmp": 15},
        "ne": {"dcmp": 64, "cmp": 37},
        "ont": {"dcmp": 80, "cmp": 29},
        "pch": {"dcmp": 45, "cmp": 16},
        "pnw": {"dcmp": 64, "cmp": 32},
    },
    # From the manual
    2019: {
        "fch": {"dcmp": 58, "cmp": 21},
        "fim": {"dcmp": 160, "cmp": 87},
        "fin": {"dcmp": 32, "cmp": 10},
        "fit": {"dcmp": 64, "cmp": 38},
        "fma": {"dcmp": 60, "cmp": 21},
        "fnc": {"dcmp": 32, "cmp": 15},
        "isr": {"dcmp": 45, "cmp": 11},
        "ne": {"dcmp": 64, "cmp": 33},
        "ont": {"dcmp": 80, "cmp": 29},
        "pch": {"dcmp": 45, "cmp": 17},
        "pnw": {"dcmp": 64, "cmp": 31},
    },
    # From the manual
    2020: {
        "fch": {"dcmp": 80, "cmp": 20},
        "fim": {"dcmp": 200, "cmp": 90},
        "fin": {"dcmp": 32, "cmp": 10},
        "fit": {"dcmp": 64, "cmp": 37},
        "fma": {"dcmp": 60, "cmp": 21},
        "fnc": {"dcmp": 32, "cmp": 14},
        "isr": {"dcmp": 45, "cmp": 13},
        "ne": {"dcmp": 64, "cmp": 33},
        "ont": {"dcmp": 80, "cmp": 27},
        "pch": {"dcmp": 45, "cmp": 16},
        "pnw": {"dcmp": 64, "cmp": 28},
    },
    # From the manual and also
    # web.archive.org/web/20220818200443/https://www.firstinspires.org/resource-library/frc/championship-eligibility-criteria
    2022: {
        "fch": {"dcmp": 60, "cmp": 16},
        "fim": {"dcmp": 160, "cmp": 64},
        "fin": {"dcmp": 32, "cmp": 8},
        "fit": {"dcmp": 80, "cmp": 23},
        "fma": {"dcmp": 60, "cmp": 18},
        "fnc": {"dcmp": 32, "cmp": 10},
        "isr": {"dcmp": 40, "cmp": 9},
        "ne": {"dcmp": 80, "cmp": 25},
        "ont": {"dcmp": 80, "cmp": 11},
        "pch": {"dcmp": 32, "cmp": 10},
        "pnw": {"dcmp": 50, "cmp": 18},
    },
    # From the manual
    2023: {
        "fch": {"dcmp": 60, "cmp": 19},
        "fim": {"dcmp": 160, "cmp": 82},
        "fin": {"dcmp": 32, "cmp": 10},
        "fit": {"dcmp": 80, "cmp": 30},
        "fma": {"dcmp": 60, "cmp": 23},
        "fnc": {"dcmp": 40, "cmp": 14},
        "isr": {"dcmp": 40, "cmp": 11},
        "ne": {"dcmp": 90, "cmp": 32},
        "ont": {"dcmp": 80, "cmp": 23},
        "pch": {"dcmp": 50, "cmp": 17},
        "pnw": {"dcmp": 50, "cmp": 22},
    },
    # From the manual
    2024: {
        "fch": {"dcmp": 54, "cmp": 17},
        "fim": {"dcmp": 160, "cmp": 86},
        "fin": {"dcmp": 38, "cmp": 11},
        "fit": {"dcmp": 86, "cmp": 29},
        "fma": {"dcmp": 60, "cmp": 22},
        "fnc": {"dcmp": 40, "cmp": 13},
        "isr": {"dcmp": 45, "cmp": 11},
        "ne": {"dcmp": 96, "cmp": 31},
        "ont": {"dcmp": 100, "cmp": 23},
        "pch": {"dcmp": 50, "cmp": 16},
        "pnw": {"dcmp": 50, "cmp": 22},
    },
    # From the manual
    2025: {
        "fch": {"dcmp": 54, "cmp": 17},
        "fim": {"dcmp": 160, "cmp": 80},
        "fin": {"dcmp": 38, "cmp": 12},
        "fit": {"dcmp": 90, "cmp": 28},
        "fma": {"dcmp": 60, "cmp": 23},
        "fnc": {"dcmp": 40, "cmp": 14},
        "fsc": {"dcmp": 28, "cmp": 5},
        "isr": {"dcmp": 45, "cmp": 10},
        "ne": {"dcmp": 96, "cmp": 31},
        "ont": {"dcmp": 100, "cmp": 22},
        "pch": {"dcmp": 45, "cmp": 12},
        "pnw": {"dcmp": 50, "cmp": 22},
    },
    # From the manual
    2026: {
        "ca": {"dcmp": 120, "cmp": 46},  # NorCal (60) + SoCal (60)
        "fch": {"dcmp": 54, "cmp": 19},
        "fim": {"dcmp": 160, "cmp": 83},
        "fin": {"dcmp": 38, "cmp": 12},
        "fit": {"dcmp": 90, "cmp": 28},
        "fma": {"dcmp": 66, "cmp": 23},
        "fnc": {"dcmp": 50, "cmp": 15},
        "fsc": {"dcmp": 32, "cmp": 7},
        "isr": {"dcmp": 42, "cmp": 12},
        "ne": {"dcmp": 100, "cmp": 32},
        "ont": {"dcmp": 100, "cmp": 21},
        "pch": {"dcmp": 45, "cmp": 13},
        "pnw": {"dcmp": 50, "cmp": 21},
        "win": {"dcmp": 36, "cmp": 12},
    },
}

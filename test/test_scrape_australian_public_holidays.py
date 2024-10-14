import pytest
import polars as pl

from src import scrape_australian_public_holidays


def test_getURL():
    year = 2025
    expectedURL = "https://www.fairwork.gov.au/employment-conditions/public-holidays/2025-public-holidays"

    assert scrape_australian_public_holidays.getURL(year) == expectedURL


def test_convertToDataFrame():
    regionMapping = {"ACT": "Australian Capital Territory"}
    holidaysList = [
        ["ACT", 2025, "New Year's Day", "2025-01-01", "00:00", "", "", ""],
        ["ACT", 2024, "New Year's Day", "2024-01-01", "00:00", "", "", ""],
    ]

    expectedResult = pl.DataFrame(
        [
            [
                "ACT",
                "Australian Capital Territory",
                2025,
                "New Year's Day",
                "2025-01-01",
                "00:00",
                "",
                "",
                "",
            ],
            [
                "ACT",
                "Australian Capital Territory",
                2024,
                "New Year's Day",
                "2024-01-01",
                "00:00",
                "",
                "",
                "",
            ],
        ],
        schema=[
            "region",
            "region_name",
            "year",
            "holiday_name",
            "date",
            "start_time",
            "public_service_flag",
            "regional_holiday_flag",
            "holiday_comment",
        ],
        orient="row",
    )

    result = scrape_australian_public_holidays.convertToDataFrame(
        holidaysList, regionMapping
    )

    assert result.equals(expectedResult)


def test_filterRegions():
    df = pl.DataFrame(
        [
            [
                "ACT",
                "Australian Capital Territory",
                2025,
                "New Year's Day",
                "2025-01-01",
                "00:00",
                "",
                "",
                "",
            ],
            [
                "QLD",
                "Queensland",
                2024,
                "New Year's Day",
                "2024-01-01",
                "00:00",
                "",
                "",
                "",
            ],
        ],
        schema=[
            "region",
            "region_name",
            "year",
            "holiday_name",
            "date",
            "start_time",
            "public_service_flag",
            "regional_holiday_flag",
            "holiday_comment",
        ],
        orient="row",
    )

    regionFilter = ["QLD"]

    expectedResult = pl.DataFrame(
        [
            [
                "QLD",
                "Queensland",
                2024,
                "New Year's Day",
                "2024-01-01",
                "00:00",
                "",
                "",
                "",
            ],
        ],
        schema=[
            "region",
            "region_name",
            "year",
            "holiday_name",
            "date",
            "start_time",
            "public_service_flag",
            "regional_holiday_flag",
            "holiday_comment",
        ],
        orient="row",
    )

    result = scrape_australian_public_holidays.filterRegions(df, regionFilter)

    assert result.equals(expectedResult)

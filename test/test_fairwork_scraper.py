import pytest

from src.webpage_scrapers import fairwork_scraper
from src.helpers.constants import STATES
from src.scrape_australian_public_holidays import readSavedWebData


def test_extractRegionMapping():
    year = 2025
    savedWebPages = {"fairwork_years": [2025]}
    data = readSavedWebData(year, savedWebPages)
    soup = data["soup"]
    mainContent = soup.find(id="primary-area")

    regionMapping = fairwork_scraper.extractRegionMapping(mainContent)

    expectedRegions = list(STATES)
    expectedRegions.sort()

    assert isinstance(regionMapping, dict)
    assert list(regionMapping.keys()) == expectedRegions


def test_extractHolidayDate():
    year = 2025
    thisHoliday = ["Wednesday 24 December ", "Christmas Eve - from 6pm to midnight"]

    expectedResult = "2025-12-24"
    result, dateComment = fairwork_scraper.extractHolidayDate(thisHoliday, year)

    assert result == expectedResult
    assert dateComment == ""


def test_extractHolidayDateTBD():
    year = 2025
    thisHoliday = [
        "Subject to AFL schedule (date TBC)",
        "Friday before AFL Grand Final",
    ]

    result, dateComment = fairwork_scraper.extractHolidayDate(thisHoliday, year)

    assert result == "TBD"
    assert dateComment == thisHoliday[0]


def test_extractHolidayName():
    thisHoliday = [
        "Saturday 19 April ",
        "Easter Saturday ",
        " the day after Good Friday",
    ]
    expectedResult = "Easter Saturday - the day after Good Friday"
    result = fairwork_scraper.extractHolidayName(thisHoliday)
    assert result == expectedResult


def test_extractHolidayComment():
    thisHolidayName = "Regional Holiday (regional area only)"
    dateComment = "Date TBD"
    thisHolidayName, thisHolidayComment = fairwork_scraper.extractHolidayComment(
        thisHolidayName, dateComment
    )

    assert thisHolidayName == "Regional Holiday"
    assert thisHolidayComment == "Date TBD. regional area only"


def test_extractHolidayStartTime():
    holidayComments = ["", "from 11am to midnight", "FROM 6PM TO MIDNIGHT"]
    expectedResults = ["00:00", "11:00", "18:00"]
    for thisHolidayComment, expectedResult in zip(holidayComments, expectedResults):
        result = fairwork_scraper.extractHolidayStartTime(thisHolidayComment)
        assert result == expectedResult


def test_extractPublicServiceFlag():
    for thisHolidayComment, expectedResult in zip(
        ["generally public service only holiday", ""], ["Y", ""]
    ):
        result = fairwork_scraper.extractPublicServiceFlag(thisHolidayComment)
        assert result == expectedResult


def test_extractRegionalHolidayFlag():
    for thisHolidayComment, expectedResult in zip(
        ["holiday may have different dates in regional areas", ""], ["Y", ""]
    ):
        result = fairwork_scraper.extractRegionalHolidayFlag(thisHolidayComment)
        assert result == expectedResult


def test_appendHolidayNamesAndDates():
    holidaysList = [
        [
            "ACT",
            2025,
            "New Year's Day",
            "2025-01-01",
            "00:00",
            "",
            "",
            "",
        ]
    ]
    year = 2024
    savedWebPages = {"fairwork_years": [2024]}

    orderedRegions = ["ACT", "NSW"]

    data = readSavedWebData(year, savedWebPages)
    soup = data["soup"]
    mainContent = soup.find(id="primary-area")

    expectedResult = [
        ["ACT", 2025, "New Year's Day", "2025-01-01", "00:00", "", "", ""],
        ["ACT", 2024, "New Year's Day", "2024-01-01", "00:00", "", "", ""],
        ["ACT", 2024, "Australia Day", "2024-01-26", "00:00", "", "", ""],
        ["ACT", 2024, "Canberra Day", "2024-03-11", "00:00", "", "", ""],
        ["ACT", 2024, "Good Friday", "2024-03-29", "00:00", "", "", ""],
        [
            "ACT",
            2024,
            "Easter Saturday – the day after Good Friday",
            "2024-03-30",
            "00:00",
            "",
            "",
            "",
        ],
        ["ACT", 2024, "Easter Sunday", "2024-03-31", "00:00", "", "", ""],
        ["ACT", 2024, "Easter Monday", "2024-04-01", "00:00", "", "", ""],
        ["ACT", 2024, "Anzac Day", "2024-04-25", "00:00", "", "", ""],
        ["ACT", 2024, "Reconciliation Day", "2024-05-27", "00:00", "", "", ""],
        ["ACT", 2024, "King’s Birthday", "2024-06-10", "00:00", "", "", ""],
        ["ACT", 2024, "Labour Day", "2024-10-07", "00:00", "", "", ""],
        ["ACT", 2024, "Christmas Day", "2024-12-25", "00:00", "", "", ""],
        ["ACT", 2024, "Boxing Day", "2024-12-26", "00:00", "", "", ""],
        ["NSW", 2024, "New Year's Day", "2024-01-01", "00:00", "", "", ""],
        ["NSW", 2024, "Australia Day", "2024-01-26", "00:00", "", "", ""],
        ["NSW", 2024, "Good Friday", "2024-03-29", "00:00", "", "", ""],
        ["NSW", 2024, "Easter Saturday", "2024-03-30", "00:00", "", "", ""],
        ["NSW", 2024, "Easter Sunday", "2024-03-31", "00:00", "", "", ""],
        ["NSW", 2024, "Easter Monday", "2024-04-01", "00:00", "", "", ""],
        ["NSW", 2024, "Anzac Day", "2024-04-25", "00:00", "", "", ""],
        ["NSW", 2024, "King's Birthday", "2024-06-10", "00:00", "", "", ""],
        ["NSW", 2024, "Labour Day", "2024-10-07", "00:00", "", "", ""],
        ["NSW", 2024, "Christmas Day", "2024-12-25", "00:00", "", "", ""],
        ["NSW", 2024, "Boxing Day", "2024-12-26", "00:00", "", "", ""],
    ]

    holidaysList = fairwork_scraper.appendHolidayNamesAndDates(
        holidaysList, orderedRegions, mainContent, year
    )

    assert holidaysList == expectedResult

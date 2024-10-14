import pytest
import polars as pl

from src.webpage_scrapers import timeanddate_scraper
from src.scrape_australian_public_holidays import readSavedWebData
from src.helpers.constants import STATES


def test_extractHolidayDate():
    year = 2025
    thisHoliday = "24 Dec"

    expectedResult = "2025-12-24"
    result = timeanddate_scraper.extractHolidayDate(thisHoliday, year)

    assert result == expectedResult


def test_extractHolidayDateTBD():
    year = 2025
    thisHoliday = ""

    expectedResult = "TBD"
    result = timeanddate_scraper.extractHolidayDate(thisHoliday, year)

    assert result == expectedResult


def test_extractHolidayDetails():
    year = 2022
    savedWebPages = {"timeanddate": [2022]}
    data = readSavedWebData(year, savedWebPages)
    soup = data["soup"]

    mainContent = soup.find("table", {"id": "holidays-table"})
    holidaysData = mainContent.find_all("tr")
  
    thisHolidayDetails = []

    thisHoliday = holidaysData[4]
    tdList = thisHoliday.find_all("td")
    timeanddate_scraper.extractHolidayDetails(thisHolidayDetails, tdList[3:])

    expectedResult = ["All except Heard and McDonald Islands"]

    assert thisHolidayDetails == expectedResult


def test_extractPublicServiceFlag():
    for thisHolidayType, expectedResult in zip(
        ["State Public Sector Holiday", "Other"], ["Y", ""]
    ):
        assert (
            timeanddate_scraper.extractPublicServiceFlag(thisHolidayType)
            == expectedResult
        )


def test_flagPartDayHoliday():
    for thisHolidayType, expectedResult in zip(
        ["Part Day Holiday", "Other"], [True, False]
    ):
        assert timeanddate_scraper.flagPartDayHoliday(thisHolidayType) == expectedResult


class Test_extractHolidayRegions:
    year = 2022
    savedWebPages = {"timeanddate": [2022]}
    data = readSavedWebData(year, savedWebPages)
    soup = data["soup"]

    mainContent = soup.find("table", {"id": "holidays-table"})
    holidaysData = mainContent.find_all("tr")

    def test_extractHolidayRegions_national(self):
        thisHoliday = self.holidaysData[3]

        tdList = thisHoliday.find_all("td")
        thisHolidayType = tdList[2].text

        (thisHolidayRegions, regionalHolidayFlag, thisHolidayComment) = (
            timeanddate_scraper.extractHolidayRegions(thisHolidayType, tdList)
        )
        assert thisHolidayRegions == STATES
        assert regionalHolidayFlag == ""
        assert thisHolidayComment == ""

    def test_extractHolidayRegions_excludedStates(self):
        thisHoliday = self.holidaysData[69]

        tdList = thisHoliday.find_all("td")
        thisHolidayType = tdList[2].text

        (thisHolidayRegions, regionalHolidayFlag, thisHolidayComment) = (
            timeanddate_scraper.extractHolidayRegions(thisHolidayType, tdList)
        )

        assert thisHolidayRegions == {"ACT", "NSW", "NT", "SA", "VIC", "TAS"}
        assert regionalHolidayFlag == ""
        assert thisHolidayComment == ""

    def test_extractStateHolidayRegions_regionalFlag(self):
        thisHoliday = self.holidaysData[14]

        tdList = thisHoliday.find_all("td")
        thisHolidayType = tdList[2].text

        (thisHolidayRegions, regionalHolidayFlag, thisHolidayComment) = (
            timeanddate_scraper.extractHolidayRegions(thisHolidayType, tdList)
        )

        assert thisHolidayRegions == {"TAS"}
        assert regionalHolidayFlag == "Y"
        assert thisHolidayComment == "Holiday is observed in Southern Tasmania."


def test_insertDefaultPartDayStartTime():
    thisRegion = "QLD"
    thisHolidayName = "Christmas Eve"
    expectedResult = "18:00"

    result = timeanddate_scraper.insertDefaultPartDayStartTime(
        thisRegion, thisHolidayName
    )
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
    year = 2022
    savedWebPages = {"timeanddate": [2022]}
    data = readSavedWebData(year, savedWebPages)
    soup = data["soup"]

    mainContent = soup.find("table", {"id": "holidays-table"})
    holidaysData = mainContent.find_all("tr")

    expectedResult = pl.DataFrame(
        [
            [
                "ACT",
                2025,
                "New Year's Day",
                "2025-01-01",
                "00:00",
                "",
                "",
                "",
            ],
            [
                "WA",
                2022,
                "New Year's Day",
                "2022-01-01",
                "00:00",
                "",
                "",
                "",
            ],
            [
                "QLD",
                2022,
                "New Year's Day",
                "2022-01-01",
                "00:00",
                "",
                "",
                "",
            ],
            [
                "TAS",
                2022,
                "New Year's Day",
                "2022-01-01",
                "00:00",
                "",
                "",
                "",
            ],
            [
                "ACT",
                2022,
                "New Year's Day",
                "2022-01-01",
                "00:00",
                "",
                "",
                "",
            ],
            [
                "NT",
                2022,
                "New Year's Day",
                "2022-01-01",
                "00:00",
                "",
                "",
                "",
            ],
            [
                "NSW",
                2022,
                "New Year's Day",
                "2022-01-01",
                "00:00",
                "",
                "",
                "",
            ],
            [
                "VIC",
                2022,
                "New Year's Day",
                "2022-01-01",
                "00:00",
                "",
                "",
                "",
            ],
            [
                "SA",
                2022,
                "New Year's Day",
                "2022-01-01",
                "00:00",
                "",
                "",
                "",
            ],
        ],
        schema=[
            "region",
            "year",
            "holiday_name",
            "date",
            "start_time",
            "public_service_flag",
            "regional_holiday_flag",
            "holiday_comment",
        ],
        orient="row",
    ).sort(["region", "year", "date"])

    for thisHoliday in holidaysData[0:4]:
        timeanddate_scraper.appendHolidayNamesAndDates(holidaysList, thisHoliday, year)

    result = pl.DataFrame(
        holidaysList,
        schema=[
            "region",
            "year",
            "holiday_name",
            "date",
            "start_time",
            "public_service_flag",
            "regional_holiday_flag",
            "holiday_comment",
        ],
        orient="row",
    ).sort(["region", "year", "date"])

    assert result.equals(expectedResult)

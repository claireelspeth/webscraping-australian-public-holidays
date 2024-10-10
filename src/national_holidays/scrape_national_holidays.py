from datetime import datetime as dt
import polars as pl
import pickle
import re
import requests
from bs4 import BeautifulSoup
# import Selenium


# from src.helpers.constants import STATES
# from src.helpers.get_settings import readJSONSettingsFile, extractSettingValue

staticStates = ["QLD", "NSW", "VIC", "WA", "TAS", "SA", "ACT", "NT"]


def saveWebData(soup, year):
    with open(
        f"./data/sample_webpage_soup_{year}.pickle",
        "wb",
    ) as f:
        pickle.dump(soup, f)


def readSavedWebData(year):
    with open(f"./data/sample_webpage_soup_{year}.pickle", "rb") as f:
        soup = pickle.load(f)
    return soup


def scrapeWebData(year):
    url = getURL(year)
    print(f"extract data for year {year} from {url}")
    page = requests.get(url)
    soup = BeautifulSoup(page.content, "html.parser")
    return soup


def getURL(year):
    urlBase = "https://www.fairwork.gov.au/employment-conditions/public-holidays/YEARID-public-holidays"
    url = urlBase.replace("YEARID", str(year))
    return url


def extractRegionMapping(mainContent):
    availableRegions = mainContent.find("ul", class_="link-list").find_all(
        "a", href=True
    )
    regionMapping = dict()
    for region in availableRegions:
        regionCode = region["href"].replace("#", "")
        if regionCode in staticStates:
            regionMapping[regionCode] = region.contents[0]

    return regionMapping


def extractHolidayDate(thisHoliday, year):
    thisHolidayDate = thisHoliday[0].strip()

    try:
        thisHolidayDate = dt.strptime(
            f"{thisHolidayDate} {year}", "%A %d %B %Y"
        ).strftime("%Y-%m-%d")
        dateComment = ""

    except Exception:
        dateComment = thisHolidayDate
        thisHolidayDate = "TBD"

    return thisHolidayDate, dateComment


def extractHolidayName(thisHoliday):
    return " - ".join([x.strip() for x in thisHoliday[1:]])


def extractHolidayComment(thisHolidayName, dateComment):
    thisHolidayComment = thisHolidayName.split("(")
    if len(thisHolidayComment) > 1:
        # assume only one comment can exist
        thisHolidayName = thisHolidayComment[0].strip()
        thisHolidayComment = thisHolidayComment[1].replace(")", "")
    else:
        thisHolidayComment = ""

    if dateComment:
        thisHolidayComment = f"{dateComment}. {thisHolidayComment}".strip()

    return thisHolidayName, thisHolidayComment


def extractHolidayStartTime(thisHolidayComment):
    partDayRegexPattern = re.compile("^from ((1[0-2]|0?[1-9])([AaPp][Mm])) to midnight")

    partialDayStartTime = partDayRegexPattern.findall(thisHolidayComment)

    if partialDayStartTime:
        holidayStartTime = dt.strptime(
            " ".join(partialDayStartTime[0][1:]).upper(), "%I %p"
        ).strftime("%H:%M")
    else:
        holidayStartTime = "00:00"

    return holidayStartTime


def extractPublicServiceFlag(thisHolidayComment):
    if "public service only" in thisHolidayComment.lower():
        return "Y"
    else:
        return ""


def extractRegionalHolidayFlag(thisHolidayComment):
    if "area" in thisHolidayComment.lower():
        return "Y"
    else:
        return ""


def appendHolidayNamesAndDates(holidaysList, orderedRegions, mainContent, year):
    holidaysData = mainContent.find_all("ul")

    regionId = 0
    for element in holidaysData:
        if element.find("a") is None:
            elementList = element.find_all("li")
            thisRegion = orderedRegions[regionId]
            for publicHoliday in elementList:
                thisHoliday = (
                    str(publicHoliday).replace("<li>", "").replace("</li>", "")
                )
                thisHoliday = thisHoliday.split("-")

                (thisHolidayDate, dateComment) = extractHolidayDate(thisHoliday, year)
                thisHolidayName = extractHolidayName(thisHoliday)
                (thisHolidayName, thisHolidayComment) = extractHolidayComment(
                    thisHolidayName, dateComment
                )
                holidayStartTime = extractHolidayStartTime(thisHolidayComment)
                publicServiceFlag = extractPublicServiceFlag(thisHolidayComment)
                regionalHolidayFlag = extractRegionalHolidayFlag(thisHolidayComment)

                holidaysList.append(
                    [
                        thisRegion,
                        year,
                        thisHolidayName,
                        thisHolidayDate,
                        holidayStartTime,
                        publicServiceFlag,
                        regionalHolidayFlag,
                        thisHolidayComment,
                    ]
                )

            regionId += 1
        if regionId >= len(orderedRegions):
            break

    return holidaysList


def saveExtractedHolidays(holidaysList, regionMapping, runId=""):
    holidaysDataFrame = pl.DataFrame(
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
    )

    holidaysDataFrame.insert_column(
        1,
        pl.col("region")
        .replace_strict(regionMapping, default=None)
        .alias("region_name"),
    )

    if runId == "":
        holidaysDataFrame.write_csv("./data/public_holidays_extraction.csv")
    else:
        holidaysDataFrame.with_columns(pl.lit(runId).alias("runId")).write_csv(
            f"./data/public_holidays_extraction_{runId}.csv"
        )


def extractAndSavePublicHolidays(yearRange, runMode=1, runId=""):
    holidaysList = []

    for year in yearRange:
        if runMode == 2:
            soup = readSavedWebData(year)
        else:
            soup = scrapeWebData(year)
            if runMode == 0:
                saveWebData(soup, year)

        mainContent = soup.find(id="primary-area")

        regionMapping = extractRegionMapping(mainContent)
        orderedRegions = list(regionMapping.keys())

        appendHolidayNamesAndDates(holidaysList, orderedRegions, mainContent, year)

    saveExtractedHolidays(holidaysList, regionMapping, runId)


if __name__ == "__main__":
    yearRange = [2024, 2025]
    runMode = 2  # [0: scrape and save data, 1: scrape data, 2: use saved data]
    runId = ""
    extractAndSavePublicHolidays(yearRange, runMode, runId)

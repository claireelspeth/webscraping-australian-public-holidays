from datetime import datetime as dt
import polars as pl
import pickle
import os
import re
import requests
from bs4 import BeautifulSoup
# import Selenium

from src.helpers.constants import STATES as staticStates


def saveWebData(soup, year):
    with open(
        f"./data/sample_webpage_soup_{year}.pickle",
        "wb",
    ) as f:
        pickle.dump(soup, f)


def readSavedWebData(year):
    filename = f"./data/sample_webpage_soup_{year}.pickle"
    if os.path.isfile(filename):
        with open(filename, "rb") as f:
            soup = pickle.load(f)
            return {"soup": soup}
    else:
        return {"soup": None}


def scrapeWebData(year):
    url = getURL(year)
    print(f"attempting to extract data for year {year} from {url}")

    page = requests.get(url)
    if page.status_code == 200:
        print("...success")
        return {"soup": BeautifulSoup(page.content, "html.parser")}

    else:
        print(f"...fail with response code {page.status_code}")
        return {"soup": None}


def getURL(year):
    # the following url is expected to work for the previous year, current year and following year
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
    partDayRegexPattern = re.compile("^from ((1[0-2]|0?[1-9])([ap][m])) to midnight")

    partialDayStartTime = partDayRegexPattern.findall(thisHolidayComment.lower())

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


def convertToDataFrame(holidaysList, regionMapping):
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

    return holidaysDataFrame


def saveExtractedHolidays(holidaysDataFrame, regionMapping, runId=None):
    if runId is None:
        holidaysDataFrame.write_csv("./data/public_holidays_extraction.csv")
    else:
        holidaysDataFrame.with_columns(pl.lit(runId).alias("runId")).write_csv(
            f"./data/public_holidays_extraction_{runId}.csv"
        )


def filterRegions(holidayDf, regionFilter):
    return holidayDf.filter(pl.col("region").is_in(regionFilter))


def extractAndSavePublicHolidays(yearRange, includedRegions, runMode=1, runId=None):
    holidaysList = []
    skippedYears = []

    for year in yearRange:
        if runMode == 2:
            data = readSavedWebData(year)
        else:
            data = scrapeWebData(year)

        if data["soup"] is not None:
            soup = data["soup"]
            if runMode == 0:
                saveWebData(soup, year)
        else:
            # go to next year if no data found
            skippedYears.append(str(year))
            continue

        mainContent = soup.find(id="primary-area")

        regionMapping = extractRegionMapping(mainContent)
        orderedRegions = list(regionMapping.keys())

        appendHolidayNamesAndDates(holidaysList, orderedRegions, mainContent, year)

    holidaysDataFrame = convertToDataFrame(holidaysList, regionMapping)
    holidaysDataFrame = filterRegions(holidaysDataFrame, includedRegions)
    saveExtractedHolidays(holidaysDataFrame, regionMapping, runId)

    return {"runStatus": "successful", "skippedYears": skippedYears}

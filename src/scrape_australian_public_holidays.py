from datetime import datetime as dt
import polars as pl
import pickle
import os
import re
import requests
from bs4 import BeautifulSoup
# import Selenium

from src.helpers.constants import (
    STATES as staticStates,
    STATES_ALIAS as statesAliasDict,
)


def saveWebData(soup, year):
    with open(
        f"./data/sample_webpage_soup_{year}.pickle",
        "wb",
    ) as f:
        pickle.dump(soup, f)


def readSavedWebData(year):
    # this is hard coded and needs to be generalised
    if year in [2024, 2025]:
        webpage = "fairwork"
    if year in [2022]:
        webpage = "timeanddate"
    else:
        webpage = None

    filename = f"./data/sample_webpage_soup_{year}.pickle"
    if os.path.isfile(filename):
        with open(filename, "rb") as f:
            soup = pickle.load(f)
            return {"soup": soup, "webpage": webpage}
    else:
        return {"soup": None, "webpage": webpage}


def scrapeWebData(year):
    webpage = "fairwork"
    url = getURL(year, webpage)
    print(f"attempting to extract data for year {year} from {url}")
    page = requests.get(url)

    if page.status_code == 200:
        print("...success")
        return {"soup": BeautifulSoup(page.content, "html.parser"), "webpage": webpage}
    else:
        print(f"...fail with response code {page.status_code}")
        # if more than two webpage options exist, make this recursive
        webpage = "timeanddate"
        url = getURL(year, webpage)
        print(f"attempting to extract data for year {year} from {url}")
        page = requests.get(url)

        if page.status_code == 200:
            print("...success")
            return {
                "soup": BeautifulSoup(page.content, "html.parser"),
                "webpage": webpage,
            }
        else:
            print(f"...fail with response code {page.status_code}")
            return {"soup": None, "webpage": None}


def getURL(year, webpage="fairwork"):
    if webpage == "fairwork":
        # the following url is expected to work for the previous year, current year and following year
        urlBase = "https://www.fairwork.gov.au/employment-conditions/public-holidays/YEARID-public-holidays"
        url = urlBase.replace("YEARID", str(year))

    elif webpage == "timeanddate":
        urlBase = "https://www.timeanddate.com/holidays/australia/YEARID"
        url = urlBase.replace("YEARID", str(year))
    else:
        raise Exception(f"unknown webpage type {webpage}")

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

        # if more than two types of webpage exist, split into modules and use eval() to call the correct function

        if data["webpage"] == "fairwork":
            mainContent = soup.find(id="primary-area")

            regionMapping = extractRegionMapping(mainContent)
            orderedRegions = list(regionMapping.keys())

            appendHolidayNamesAndDates(holidaysList, orderedRegions, mainContent, year)
        elif data["webpage"] == "timeanddate":
            # will requires tests
            mainContent = soup.find("table", {"id": "holidays-table"})
            holidaysData = mainContent.find_all("tr")
            holidaysList = []

            for thisHoliday in holidaysData:
                holidayFound = False

                # print(thisHoliday.attrs)
                # print(thisHoliday.findChild())

                thList = thisHoliday.find_all("th")
                tdList = thisHoliday.find_all("td")
                aList = thisHoliday.find_all("a")

                if len(thList) > 0:
                    thisHolidayDate = thList[0].text
                    if thisHolidayDate == "Date":
                        continue

                    thisHolidayName = tdList[1].text

                    if thisHolidayName == "Easter Tuesday":
                        print("is this the Public Sector Holiday")
                        import pdb

                        pdb.set_trace()
                    thisHolidayType = tdList[2].text

                    if not (
                        ("National Holiday" in thisHolidayType)
                        | ("State Holiday" in thisHolidayType)
                        | ("State Public Sector Holiday" in thisHolidayType)
                    ):
                        continue
                    thisHolidayDetails = []
                    print(f"({thisHolidayDate}, {thisHolidayName}, {thisHolidayType})")
                    for details in tdList[3:]:
                        thisHolidayDetails.append(details.text.strip())
                    thisHolidayDetails = ",".join(
                        [x.upper() for x in thisHolidayDetails if x != ""]
                    )
                    for key in statesAliasDict.keys():
                        thisHolidayDetails = thisHolidayDetails.replace(
                            key, statesAliasDict[key]
                        )

                    print(thisHolidayDetails)

                    thisHolidayRegions = set(staticStates)
                    thisHolidayComment = ""
                    regionalHolidayFlag = ""

                    if thisHolidayType == "State Public Sector Holiday":
                        publicServiceFlag = "Y"
                    else:
                        publicServiceFlag = ""

                    if thisHolidayType != "National Holiday":
                        if "ALL EXCEPT" in thisHolidayDetails:
                            excludedRegions = thisHolidayDetails.replace(
                                "ALL EXCEPT ", ""
                            ).split(",")
                            includedRegions = []
                        else:
                            excludedRegions = []
                            includedRegions = thisHolidayDetails.split(",")

                        if "*" in thisHolidayDetails:
                            # this could have bugs if the asterix appears next to one state within a list of states - not yet observed so not yet handled
                            thisHolidayComment = (
                                tdList[3]
                                .find_all("span")[0]
                                .find_all("span")[0]["title"]
                            )
                            thisHolidayDetails = thisHolidayDetails.replace("*", "")
                            regionalHolidayFlag = "Y"

                        if len(excludedRegions) > 0:
                            thisHolidayRegions = thisHolidayRegions.difference(
                                excludedRegions
                            )
                        if len(excludedRegions) > 0:
                            thisHolidayRegions = thisHolidayRegions.intersection(
                                includedRegions
                            )
                    print("\n")
               
            import pdb

            pdb.set_trace()

    holidaysDataFrame = convertToDataFrame(holidaysList, regionMapping)
    holidaysDataFrame = filterRegions(holidaysDataFrame, includedRegions)
    saveExtractedHolidays(holidaysDataFrame, regionMapping, runId)

    return {"runStatus": "successful", "skippedYears": skippedYears}

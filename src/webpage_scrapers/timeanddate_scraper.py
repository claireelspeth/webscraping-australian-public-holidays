from datetime import datetime as dt
import polars as pl

from src.helpers.constants import (
    STATES as staticStates,
    STATES_ALIAS as statesAliasDict,
    PART_TIME_START_TIMES,
)

partDayStartTimes = pl.DataFrame(
    PART_TIME_START_TIMES, orient="row", schema=["region", "holiday_name", "start_time"]
)


def extractHolidayDate(thisHolidayDate, year):
    try:
        thisHolidayDate = dt.strptime(
            f"{thisHolidayDate.strip()} {year}", "%d %b %Y"
        ).strftime("%Y-%m-%d")

    except Exception:
        thisHolidayDate = "TBD"

    return thisHolidayDate


def extractHolidayDetails(thisHolidayDetails, detailsList):
    for details in detailsList:
        thisHolidayDetails.append(details.text.strip())
        thisHolidayDetails = ",".join(
            [x.upper() for x in thisHolidayDetails if x != ""]
        )

        for key in statesAliasDict.keys():
            thisHolidayDetails = thisHolidayDetails.replace(key, statesAliasDict[key])

    return thisHolidayDetails


def extractPublicServiceFlag(thisHolidayType):
    if thisHolidayType == "State Public Sector Holiday":
        return "Y"
    else:
        return ""


def flagPartDayHoliday(thisHolidayType):
    return thisHolidayType == "Part Day Holiday"


def extractHolidayRegions(thisHolidayType, tdList):
    thisHolidayDetails = []
    thisHolidayDetails = extractHolidayDetails(thisHolidayDetails, tdList[3:])

    thisHolidayRegions = set(staticStates)
    thisHolidayComment = ""
    regionalHolidayFlag = ""

    if thisHolidayType != "National Holiday":
        if "ALL EXCEPT" in thisHolidayDetails:
            excludedRegions = thisHolidayDetails.replace("ALL EXCEPT ", "")
            excludedRegions = [x.strip() for x in excludedRegions.split(",")]
            includedRegions = []
        else:
            excludedRegions = []

            if "*" in thisHolidayDetails:
                # this could have bugs if the asterix appears next to one state within a list of states - not yet observed so not yet handled
                thisHolidayComment = (
                    tdList[3].find_all("span")[0].find_all("span")[0]["title"]
                )
                thisHolidayDetails = thisHolidayDetails.replace("*", "")
                regionalHolidayFlag = "Y"

            includedRegions = [x.strip() for x in thisHolidayDetails.split(",")]

        if len(excludedRegions) > 0:
            thisHolidayRegions = thisHolidayRegions.difference(excludedRegions)
        if len(includedRegions) > 0:
            thisHolidayRegions = thisHolidayRegions.intersection(includedRegions)

    return (thisHolidayRegions, regionalHolidayFlag, thisHolidayComment)


def insertDefaultPartDayStartTime(thisRegion, thisHolidayName):
    try:
        holidayStartTime = pl.Series(
            partDayStartTimes.filter(pl.col("region") == thisRegion)
            .filter(pl.col("holiday_name") == thisHolidayName)
            .select("start_time")
        )[0]
    except Exception:
        holidayStartTime = "TBD"

    return holidayStartTime


def appendHolidayNamesAndDates(holidaysList, thisHoliday, year):
    thList = thisHoliday.find_all("th")
    tdList = thisHoliday.find_all("td")

    if len(thList) > 0:
        thisHolidayDate = thList[0].text
        if thisHolidayDate == "Date":
            return
        thisHolidayDate = extractHolidayDate(thisHolidayDate, year)
        thisHolidayName = tdList[1].text
        thisHolidayType = tdList[2].text

        if not (
            ("National Holiday" in thisHolidayType)
            | ("State Holiday" in thisHolidayType)
            | ("State Public Sector Holiday" in thisHolidayType)
            | ("Part Day Holiday" in thisHolidayType)
        ):
            return

        publicServiceFlag = extractPublicServiceFlag(thisHolidayType)

        holidayStartTime = "00:00"
        useDefaultHolidayStartTime = flagPartDayHoliday(thisHolidayType)

        (thisHolidayRegions, regionalHolidayFlag, thisHolidayComment) = (
            extractHolidayRegions(thisHolidayType, tdList)
        )

        for thisRegion in thisHolidayRegions:
            if useDefaultHolidayStartTime:
                holidayStartTime = insertDefaultPartDayStartTime(
                    thisRegion, thisHolidayName
                )

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


def timeanddateExtraction(holidaysList, soup, year):
    mainContent = soup.find("table", {"id": "holidays-table"})
    holidaysData = mainContent.find_all("tr")

    for thisHoliday in holidaysData:
        appendHolidayNamesAndDates(holidaysList, thisHoliday, year)

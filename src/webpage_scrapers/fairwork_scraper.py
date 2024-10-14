from datetime import datetime as dt
import re

from src.helpers.constants import STATES as staticStates


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


def fairworkExtraction(holidaysList, soup, year):
    mainContent = soup.find(id="primary-area")

    regionMapping = extractRegionMapping(mainContent)
    orderedRegions = list(regionMapping.keys())

    appendHolidayNamesAndDates(holidaysList, orderedRegions, mainContent, year)

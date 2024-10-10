from datetime import datetime as dt
import polars as pl
import re
import requests
from bs4 import BeautifulSoup
# import Selenium


# from src.helpers.constants import STATES
# from src.helpers.get_settings import readJSONSettingsFile, extractSettingValue
runId = ""
staticStates = ["QLD", "NSW", "VIC", "WA", "TAS", "SA", "ACT", "NT"]
yearRange = [2025]  # for dev purposes, change to start and end year range later
URL_BASE = "https://www.fairwork.gov.au/employment-conditions/public-holidays/YEARID-public-holidays"
for year in yearRange:
    print(year)
    URL = URL_BASE.replace("YEARID",str(year))


    page = requests.get(URL)
    soup = BeautifulSoup(page.content, "html.parser")
    mainContent = soup.find(id="primary-area")

    availableRegions = mainContent.find("ul", class_="link-list").find_all("a", href=True)
    regionMapping = dict()
    for region in availableRegions:
        regionCode = region["href"].replace("#", "")
        if regionCode in staticStates:
            regionMapping[regionCode] = region.contents[0]


    orderedRegions = list(regionMapping.keys())

    partDayRegexPattern = re.compile("^from ((1[0-2]|0?[1-9])([AaPp][Mm])) to midnight")


    holidaysData = mainContent.find_all("ul")
    holidaysList = []
    holidayDatesTBD = []
    regionId = 0
    for element in holidaysData:
        if element.find("a") is None:
            elementList = element.find_all("li")
            thisRegion = orderedRegions[regionId]
            for publicHoliday in elementList:
                thisHoliday = str(publicHoliday).replace("<li>", "").replace("</li>", "")
                thisHoliday = thisHoliday.split("-")
                thisHolidayDate = thisHoliday[0].strip()
                thisHolidayName = " - ".join([x.strip() for x in thisHoliday[1:]])

                try:
                    thisHolidayDate = dt.strptime(
                        f"{thisHolidayDate} {year}", "%A %d %B %Y"
                    ).strftime("%Y-%m-%d")
                except:
                    holidayDatesTBD.append(
                        [
                            thisRegion,
                            year,
                            thisHolidayName,
                            thisHolidayDate,
                        ]
                    )

                thisHolidayComment = thisHolidayName.split("(")
                partialDayStartTime = []
                if len(thisHolidayComment) > 1:
                    # assume only one comment can exist
                    thisHolidayName = thisHolidayComment[0].strip()
                    thisHolidayComment = thisHolidayComment[1].replace(")", "")
                    partialDayStartTime = partDayRegexPattern.findall(thisHolidayComment)

                if partialDayStartTime:
                    partialDayStartTime = dt.strptime(
                        " ".join(partialDayStartTime[0][1:]).upper(), "%I %p"
                    ).strftime("%H:%M")
                else:
                    partialDayStartTime = "00:00"

                holidaysList.append(
                    [
                        thisRegion,
                        year,
                        thisHolidayName,
                        thisHolidayDate,
                        partialDayStartTime,
                    ]
                )

            regionId += 1
        if regionId >= len(orderedRegions):
            break


    holidaysDataFrame = pl.DataFrame(
        holidaysList,
        schema=["region", "year", "holiday_name", "date", "start_time"],
        orient="row",
    )
    if runId == "":
        holidaysDataFrame.write_csv("./data/public_holidays_extraction.csv")
    else:
        holidaysDataFrame.with_columns(pl.lit(runId).alias("runId")).write_csv(
            f"./data/public_holidays_extraction_{runId}.csv"
        )

    print(holidayDatesTBD)

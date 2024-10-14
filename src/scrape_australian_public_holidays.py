import polars as pl
import pickle
import os
import requests
from bs4 import BeautifulSoup
# import Selenium

from src.webpage_scrapers.fairwork_scraper import fairworkExtraction
from src.webpage_scrapers.timeanddate_scraper import timeanddateExtraction


from src.helpers.constants import (
    STATES_MAPPING as statesDict,
)


def saveWebData(soup, year):
    with open(
        f"./data/sample_webpage_soup_{year}.pickle",
        "wb",
    ) as f:
        pickle.dump(soup, f)


def readSavedWebData(year, savedWebPages):

    webpage = None
    for key, values in savedWebPages.items():
        if year in values:
            webpage = key.split("_years")[0]
            break

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


def saveExtractedHolidays(holidaysDataFrame, runId=None):
    if runId is None:
        holidaysDataFrame.write_csv("./data/public_holidays_extraction.csv")
    else:
        holidaysDataFrame.with_columns(pl.lit(runId).alias("runId")).write_csv(
            f"./data/public_holidays_extraction_{runId}.csv"
        )


def filterRegions(holidayDf, regionFilter):
    return holidayDf.filter(pl.col("region").is_in(regionFilter))


def sortResults(holidayDf):
    return holidayDf.sort(["region", "year", "date"])


def extractAndSavePublicHolidays(yearRange, regionsToFilter, savedWebPages, runMode=1, runId=None):
    holidaysList = []
    skippedYears = []

    for year in yearRange:
        if runMode == 2:
            data = readSavedWebData(year, savedWebPages)

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

        # run custom extraction script for webpage type
        eval(f"{data['webpage']}Extraction(holidaysList, soup,year)")

    holidaysDataFrame = convertToDataFrame(holidaysList, statesDict)
    holidaysDataFrame = filterRegions(holidaysDataFrame, regionsToFilter)
    holidaysDataFrame = sortResults(holidaysDataFrame)
    saveExtractedHolidays(holidaysDataFrame, runId)

    return {"runStatus": "successful", "skippedYears": skippedYears}

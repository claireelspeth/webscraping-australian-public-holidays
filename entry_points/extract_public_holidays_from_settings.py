import os
import sys

sys.path.insert(0, os.getcwd())

from src.scrape_australian_public_holidays import extractAndSavePublicHolidays
from src.helpers.get_settings import readJSONSettingsFile, validateSettings
from src.helpers.get_year_range import getYearRange

# read settings
settings = readJSONSettingsFile()
issuesWithSettings = validateSettings(settings)
if issuesWithSettings:
    print(issuesWithSettings)
    exit()

yearRange = getYearRange(settings)


# get run modes
if len(sys.argv) > 1:
    runId = sys.argv[1]
else:
    runId = ""

if len(sys.argv) > 2:
    runMode = sys.argv[2]
else:
    runMode = 2  # [0: scrape and save data, 1: scrape data, 2: use saved data]


# run script
status = extractAndSavePublicHolidays(yearRange, runMode, runId)
print(status)

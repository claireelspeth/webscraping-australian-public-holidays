import os
import sys

sys.path.insert(0, os.getcwd())

from src.scrape_australian_public_holidays import extractAndSavePublicHolidays
from src.helpers.get_settings import (
    extractSettingValue,
    readJSONSettingsFile,
    validateSettings,
)
from src.helpers.get_year_range import getYearRange
from src.helpers.constants import (
    SETTINGS_FILE_PATH,
    SAVED_WEB_PAGES,
    STATES_TO_INCLUDE,
    RUN_ID,
    RUN_MODE,
)


if len(sys.argv) > 1:
    settingsFilePath = sys.argv[1]
else:
    settingsFilePath = SETTINGS_FILE_PATH

# read settings
settings = readJSONSettingsFile(settingsFilePath)
issuesWithSettings = validateSettings(settings)
if issuesWithSettings:
    status = {"runStatus": "error", "errMsg": f"invalid settings {issuesWithSettings}"}
    print(status)
    exit()

yearRange = getYearRange(settings)
settings["year_range"] = yearRange
regionsToFilter = extractSettingValue(settings, STATES_TO_INCLUDE)
savedWebPages = extractSettingValue(settings, SAVED_WEB_PAGES)
runId = extractSettingValue(settings, RUN_ID)
runMode = extractSettingValue(settings, RUN_MODE)

# run script
try:
    status = extractAndSavePublicHolidays(
        yearRange, regionsToFilter, savedWebPages, runMode, runId
    )
    status["settings"] = settings
except Exception as e:
    status = {"runStatus": "error", "errMsg": e}
print(status)

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
from src.helpers.constants import SETTINGS_FILE_PATH


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
runId = extractSettingValue(settings, "run_id")
runMode = extractSettingValue(settings, "run_mode")


# run script
try:
    status = extractAndSavePublicHolidays(yearRange, runMode, runId)
    status["settings"] = settings
except Exception as e:
    status = {"runStatus": "error", "errMsg": e}
print(status)

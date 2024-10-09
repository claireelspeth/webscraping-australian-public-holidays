from datetime import datetime as dt

import get_settings
from constants import CUSTOM_START_YEAR, CUSTOM_END_YEAR

CURRENT_YEAR = dt.now().year


def get_year_range():
    settings = get_settings.readJSONSettingsFile()

    startYear = get_settings.extractSettingValue(settings, CUSTOM_START_YEAR)
    if startYear is None:
        startYear = CURRENT_YEAR - 7

    endYear = get_settings.extractSettingValue(settings, CUSTOM_END_YEAR)
    if endYear is None:
        endYear = CURRENT_YEAR + 1

    return (startYear, endYear)


if __name__ == "__main__":
    (startYear, endYear) = get_year_range()
    print(f"Extract public holidays for {startYear} to {endYear}")

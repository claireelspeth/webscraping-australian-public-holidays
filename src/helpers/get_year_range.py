from datetime import datetime as dt
import numpy as np

from src.helpers.get_settings import extractSettingValue
from src.helpers.constants import CUSTOM_START_YEAR, CUSTOM_END_YEAR

CURRENT_YEAR = dt.now().year


def getYearRange(settings):
    startYear = extractSettingValue(settings, CUSTOM_START_YEAR)
    if startYear is None:
        startYear = CURRENT_YEAR - 7

    endYear = extractSettingValue(settings, CUSTOM_END_YEAR)
    if endYear is None:
        endYear = CURRENT_YEAR + 1

    return np.arange(startYear, endYear + 1, 1)

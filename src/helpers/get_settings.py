import json

from constants import (
    SETTINGS_FILE_PATH,
    CUSTOM_START_YEAR,
    CUSTOM_END_YEAR,
    STATES,
    ADDITIONAL_REGIONS,
)


def readJSONSettingsFile():
    with open(SETTINGS_FILE_PATH) as f:
        return json.load(f)


def extractSettingValue(settings, key):
    value = settings.get(key, None)
    if value == "":
        value = None

    return value


def validateKeys(issues, settings):
    expectedKeys = {
        CUSTOM_START_YEAR,
        CUSTOM_END_YEAR,
        STATES,
        ADDITIONAL_REGIONS,
    }
    missingKeys = expectedKeys.difference(settings.keys())
    if missingKeys:
        issues["missingKeys"] = missingKeys


def validateValues(issues, settings):
    badValues = []
    # custom
    for yearKey in [CUSTOM_START_YEAR, CUSTOM_END_YEAR]:
        value = extractSettingValue(settings, yearKey)
        if not ((value is None) | (isinstance(value, int))):
            badValues.append(yearKey)
    for locationKey in [STATES, ADDITIONAL_REGIONS]:
        value = extractSettingValue(settings, locationKey)
        if not isinstance(value, list):
            badValues.append(locationKey)
    if badValues:
        issues["bad value types"] = badValues


def validateSettings(settings):
    issues = {}

    validateKeys(issues, settings)
    validateValues(issues, settings)

    return issues


if __name__ == "__main__":
    settings = readJSONSettingsFile()
    print(settings)

    issuesWithSettings = validateSettings(settings)
    if issuesWithSettings:
        print(issuesWithSettings)

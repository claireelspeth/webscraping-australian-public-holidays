import pytest

from src.helpers import get_settings, get_year_range


def test_getYearRange():
    settings = {"custom_start_year": 2000, "custom_end_year": 2002}
    expectedResult = [2000, 2001, 2002]

    result = get_year_range.getYearRange(settings)

    assert all(result == expectedResult)


def test_getYearRange_bad():
    settings = {"custom_start_year": 2002, "custom_end_year": 1999}

    result = get_year_range.getYearRange(settings)

    assert isinstance(result, list) & len(result) == 0


def test_extractSettingValue():
    settings = {"run_id": "", "run_mode": 2}
    expectedResults = [None, 2]
    for key, expectedValue in zip(settings, expectedResults):
        assert get_settings.extractSettingValue(settings, key) == expectedValue


def test_missingKeys():
    issues = {}
    settings = {"run_id": "", "run_mode": 2}
    get_settings.validateKeys(issues, settings)
    assert len(issues["missing_keys"]) > 0


def test_badValues():
    issues = {}
    settings = {"custom_start_year": 2000, "custom_end_year": "2002"}
    get_settings.validateValues(issues, settings)

    print(issues)

    assert ("custom_end_year" in issues["bad_value_types"]) & ~("custom_start_year" in issues['bad_value_types'])

def test_validateSettings():
    settings = {"custom_start_year": 2000, "custom_end_year": "2002"}

    issues = get_settings.validateSettings(settings)
    assert ("missing_keys" in issues) & ("bad_value_types" in issues)
SETTINGS_FILE_PATH = "settings.json"

# static data
STATES_MAPPING = {
    "ACT": "AUSTRALIAN CAPITAL TERRITORY",
    "NSW": "NEW SOUTH WALES",
    "NT": "NORTHERN TERRITORY",
    "QLD": "QUEENSLAND",
    "SA": "SOUTH_AUSTRALIA",
    "TAS": "TASMANIA",
    "VIC": "VICTORIA",
    "WA": "WESTERN AUSTRALIA",
}
STATES_ALIAS = {v: k for k, v in STATES_MAPPING.items()}
STATES = STATES_MAPPING.keys()


# expected settings
CUSTOM_START_YEAR = "custom_start_year"
CUSTOM_END_YEAR = "custom_end_year"
STATES_TO_INCLUDE = "states_to_return"
ADDITIONAL_REGIONS = "additional_local_regions"
RUN_ID = "run_id"
RUN_MODE = "run_mode"

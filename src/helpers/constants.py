SETTINGS_FILE_PATH = "settings.json"

# static data
STATES_MAPPING = {
    "ACT": "AUSTRALIAN CAPITAL TERRITORY",
    "NSW": "NEW SOUTH WALES",
    "NT": "NORTHERN TERRITORY",
    "QLD": "QUEENSLAND",
    "SA": "SOUTH AUSTRALIA",
    "TAS": "TASMANIA",
    "VIC": "VICTORIA",
    "WA": "WESTERN AUSTRALIA",
}
STATES_ALIAS = {v: k for k, v in STATES_MAPPING.items()}
STATES = STATES_MAPPING.keys()

# default data to insert if missing data
PART_TIME_START_TIMES = [
    ["QLD", "Christmas Eve", "18:00"],
    ["NT", "Christmas Eve", "19:00"],
    ["NT", "New Year's Eve", "19:00"],
    ["SA", "Christmas Eve", "19:00"],
    ["SA", "New Year's Eve", "19:00"],
]


# expected settings
CUSTOM_START_YEAR = "custom_start_year"
CUSTOM_END_YEAR = "custom_end_year"
STATES_TO_INCLUDE = "states_to_return"
ADDITIONAL_REGIONS = "additional_local_regions"
RUN_ID = "run_id"
RUN_MODE = "run_mode"

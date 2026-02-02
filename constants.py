"""
Constants for the category-v project.
"""

from datetime import datetime, timedelta

# Time range for data processing (2021-2023)
TS_MIN = datetime(2021, 1, 1, 0, 0, 0)
TS_MAX = datetime(2023, 12, 31, 23, 59, 59)

BIN_TIME_INTERVAL_MINUTES = 30
# Default region for hurricane data processing
DEFAULT_REGION = "atl"

# Default nearest neighbor tolerance for SHIPS data interpolation (3 hours)
DEFAULT_NN_TOLERANCE = timedelta(hours=3)

# Hurricane best track data paths
ATL_BEST_TRACK_URL = 'https://www.nhc.noaa.gov/data/hurdat/hurdat2-1851-2024-040425.txt'
NE_PAC_BEST_TRACK_URL = 'https://www.nhc.noaa.gov/data/hurdat/hurdat2-nepac-1949-2024-031725.txt'

# SHIPS data paths
ATL_SHIPS_URL = 'https://rammb-data.cira.colostate.edu/ships/data/AL/lsdiaga_1982_2023_sat_ts_7day.txt'
NE_PAC_SHIPS_URL = 'https://rammb-data.cira.colostate.edu/ships/data/EP/lsdiage_1982_2023_sat_ts_7day.txt'

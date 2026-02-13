# Category V - Hurricane and GLM Data Analysis

This project provides tools for downloading, processing, and analyzing Geostationary Lightning Mapper (GLM) data from Google Cloud Storage and correlating it with hurricane data from the HURDAT2 database and SHIPS data.

## Data Pipeline

![Data Pipeline](data_pipeline.png)

The data pipeline shows the flow from raw GLM NetCDF files downloaded from Google Cloud Storage, through processing to extract group components, and integration with hurricane tracking data.

## Requirements

- Python >= 3.8
- Conda (Miniconda or Anaconda)

## Installation

### 1. Clone or navigate to the project directory

```bash
cd category-v
```

### 2. Create and activate the conda environment

The project uses conda to manage dependencies. You can use the Makefile for easy environment management:

**Using Makefile (Recommended):**
```bash
# Create the conda environment
make setup

# Update the environment if needed
make update

# Show activation command
make activate
```

**Or manually:**
```bash
conda env create -f environment.yml
```

This will create a conda environment named `category-v` with all required dependencies including:
- Python 3.8+
- NetCDF-4 libraries (netcdf4, h5netcdf, h5py, xarray)
- Data processing (pandas, numpy)
- Visualization (matplotlib, cycler)
- Geographic libraries (pyproj, astropy)
- Google Cloud Storage libraries (gcsfs, fsspec)
- hurdat2parser

### 3. Activate the environment

```bash
conda activate category-v
```

Or use the Makefile:
```bash
make activate  # Shows the activation command
```

### 4. Verify installation

You can verify the installation by running:

```bash
# Using Makefile
make run

# Or manually
python main.py
```

## Running as Daemon (Background Process)

For long-running processes (like processing all hurricanes), you can run the script as a daemon that continues running even if you close your terminal or your screen goes blank:

```bash
# Start as daemon (background)
make daemon

# Check if daemon is running
make status

# View logs in real-time
make logs

# Stop the daemon
make stop
```

The daemon will:
- Continue running even if you disconnect or close your terminal
- Save all output to timestamped log files in `logs/`
- Save the process ID to `logs/main.pid` for easy management

**Note:** Processing all hurricanes can take many hours. Running as a daemon is recommended for this use case.

## Project Structure

```
category-v/
├── data/
│   ├── global/
│   │   ├── hurricane/
│   │   │   ├── {region}_all_hurricane_best_tracks_{start}_{end}.csv
│   │   │   └── {region}_hurricane_list_{start}_{end}.csv
│   │   └── ships/
│   │       └── {region}_ships_data_{start}_{end}.csv
│   ├── storms/
│   │   └── {NAME}_{YEAR}/
│   │       ├── hurricane/
│   │       │   └── besttrack.csv
│   │       ├── ships/
│   │       │   └── ships_interpolated.csv
│   │       └── glm/
│   │           └── groups.csv
│   ├── cache/
│   │   └── glm/          # Temporary cache for GLM files
├── helpers/
│   ├── glm_helpers.py    # GLM data processing
│   ├── hurricane_helpers.py  # Hurricane data manipulation
│   ├── ships_helpers.py  # SHIPS data processing
│   ├── time_helpers.py   # Date/time utilities
│   └── __init__.py
├── constants.py          # Global constants (time ranges, URLs, etc.)
├── main.py              # Main script with examples
├── Makefile             # Makefile for environment and daemon management
├── environment.yml      # Conda environment configuration
├── logs/                # Log files and PID files (created when running daemon)
└── README.md           # This file
```

## Usage

### Working with Hurricane Data

#### List all hurricanes (2021-2023)

```python
from helpers import list_all_hurricanes

# List all hurricanes in the default region (Atlantic)
hurricanes_df = list_all_hurricanes()

# Or specify a region
hurricanes_df = list_all_hurricanes(region="atl")  # or "pac"
print(hurricanes_df.head())
```

This creates `data/global/hurricane/{region}_hurricane_list_{start}_{end}.csv` with columns: `name`, `code`, `year`, `start_date`, `end_date`, `statuses_reached`.

#### Get hurricane path data

```python
from helpers import get_hurricane_path

# Get full best track data for a hurricane by code
hurricane_code = "AL092022"  # Hurricane IAN
path_df = get_hurricane_path(hurricane_code, region="atl")
if path_df is not None:
    print(path_df.head())
```

#### Interpolate best track data for a hurricane

```python
from helpers import interpolate_besttrack_for_code

# Interpolate best track data for a single hurricane
interp_df = interpolate_besttrack_for_code("AL092022", region="atl", time_interval=30)
# Saves to data/storms/IAN_2022/hurricane/besttrack.csv
```

#### Interpolate best track data for all hurricanes

```python
from helpers import interpolate_all_hurricanes_besttrack

# Process all hurricanes in the default region
results = interpolate_all_hurricanes_besttrack(region="atl", time_interval=30)
```

### Working with SHIPS Data

#### Save global SHIPS data

```python
from helpers import save_ships_data

# Save SHIPS data for the default region (Atlantic)
ships_df = save_ships_data(region="atl")
# Saves to data/global/ships/atl_ships_data_{start}_{end}.csv
```

#### Interpolate SHIPS data for a hurricane

```python
from helpers import interpolate_ships_info_for_hurricane

# Interpolate SHIPS data for a hurricane by code
interp_path = interpolate_ships_info_for_hurricane(
    "AL092022",  # Hurricane code
    nn_tolerance=None,  # Uses default (3 hours) from constants
    region="atl",
    time_interval=30
)
# Saves to data/storms/IAN_2022/ships/ships_interpolated.csv
```

#### Interpolate SHIPS data for all hurricanes

```python
from helpers import interpolate_all_hurricanes_ships

# Process all hurricanes
results = interpolate_all_hurricanes_ships(region="atl", time_interval=30)
```

### Working with GLM Data

#### Process GLM data for a hurricane

```python
from helpers import process_glm_info_for_hurricane

# Process GLM data for a single hurricane
csv_path = process_glm_info_for_hurricane(
    "AL092022",  # Hurricane code
    box_size=6,  # Size of lat/lon box in degrees
    region="atl",
    time_interval=30,
    cache_dir=None  # Uses default cache directory
)
# Saves to data/storms/IAN_2022/glm/groups.csv
```

#### Process GLM data for all hurricanes

```python
from helpers import process_all_hurricanes_glm

# Process GLM data for all hurricanes
results = process_all_hurricanes_glm(
    box_size=6,
    region="atl",
    time_interval=30
)
```

### Orchestrating Complete Data Processing

#### Download all data for a single hurricane

The orchestration helpers provide a convenient way to process all data types (hurricane best track, SHIPS, and GLM) for a hurricane in the correct order:

```python
from helpers import download_all_data_for_hurricane

# Process all data for a single hurricane
results = download_all_data_for_hurricane(
    "AL092022",  # Hurricane code
    region="atl",
    time_interval=30,
    box_size=6,
    nn_tolerance=None,  # Uses default (3 hours) from constants
    cache_dir=None  # Uses default cache directory
)
# Returns dictionary with paths:
# {
#     'hurricane': 'data/storms/IAN_2022/hurricane/besttrack.csv',
#     'ships': 'data/storms/IAN_2022/ships/ships_interpolated.csv',
#     'glm': 'data/storms/IAN_2022/glm/groups.csv'
# }
```

#### Download all data for all hurricanes

Process all data types for all hurricanes in a region:

```python
from helpers import download_all_data_for_all_hurricanes

# Process all data for all hurricanes
results = download_all_data_for_all_hurricanes(
    region="atl",
    time_interval=30,
    box_size=6,
    nn_tolerance=None,
    cache_dir=None
)
# Returns dictionary mapping hurricane codes to their processed data paths
```

### Working with Time Bins

#### Get bin times for a hurricane

```python
from helpers import (
    get_hurricane_bin_midpoint_times,
    get_hurricane_bin_start_times,
    get_hurricane_bin_end_times
)

hurricane_code = "AL092022"
bin_times = get_hurricane_bin_midpoint_times(hurricane_code, region="atl", time_interval=30)
bin_starts = get_hurricane_bin_start_times(hurricane_code, region="atl", time_interval=30)
bin_ends = get_hurricane_bin_end_times(hurricane_code, region="atl", time_interval=30)
```

## Makefile Commands

The project includes a Makefile for convenient environment and process management:

### Environment Management
- `make setup` - Create conda environment from `environment.yml`
- `make update` - Update conda environment from `environment.yml`
- `make activate` - Show command to activate the conda environment

### Running Scripts
- `make run` - Run `main.py` normally (foreground)
- `make daemon` - Run `main.py` as daemon (background process)
- `make stop` - Stop the daemon process
- `make status` - Check if daemon is running
- `make logs` - View latest log file in real-time (`tail -f`)
- `make clean` - Remove log files and PID file

### Example Workflow

```bash
# First time setup
make setup

# Update environment if needed
make update

# Run a quick test (foreground)
make run

# For long-running processes, use daemon
make daemon

# Monitor progress
make logs

# Check status
make status

# Stop when done
make stop
```

## Helper Modules

### `hurricane_helpers`
Functions for working with hurricane best track data:
- `read_best_track(bt_url)` - Parse best track files and extract hurricane data
- `save_best_track(bt_url, region)` - Save best track data to CSV
- `list_all_hurricanes(region=None)` - List all hurricanes with metadata, saves to CSV
- `get_hurricane_path(code, region=None)` - Get full best track DataFrame for a hurricane
- `interpolate_besttrack_for_code(hurricane_code, region=None, time_interval=30)` - Interpolate best track for a single hurricane
- `interpolate_all_hurricanes_besttrack(region=None, time_interval=30)` - Interpolate best track for all hurricanes
- `get_hurricane_bin_midpoint_times(hurricane_code, region=None, time_interval=30)` - Get bin midpoint times
- `get_hurricane_bin_start_times(hurricane_code, region=None, time_interval=30)` - Get bin start times
- `get_hurricane_bin_end_times(hurricane_code, region=None, time_interval=30)` - Get bin end times

### `ships_helpers`
Functions for working with SHIPS (Statistical Hurricane Intensity Prediction Scheme) data:
- `read_ships_data(region=None)` - Read SHIPS data from URL
- `save_ships_data(region=None)` - Save SHIPS data to CSV
- `interpolate_ships_info_for_hurricane(hurricane_code, nn_tolerance=None, region=None, time_interval=30)` - Interpolate SHIPS data for a single hurricane
- `interpolate_all_hurricanes_ships(region=None, time_interval=30, nn_tolerance=None)` - Interpolate SHIPS data for all hurricanes

### `glm_helpers`
Functions for working with GLM (Geostationary Lightning Mapper) data:
- `process_glm_file_h5py(url, center_lat, center_lon, box_size, geod, cache_dir)` - Process a single GLM file
- `aggregate_glm_data_for_urls(glm_urls, center_lat, center_lon, box_size, geod, cache_dir)` - Aggregate GLM data from multiple URLs
- `process_glm_info_for_hurricane(hurricane_code, box_size=6, region=None, time_interval=30, cache_dir=None)` - Process GLM data for a single hurricane
- `process_all_hurricanes_glm(box_size=6, region=None, time_interval=30, cache_dir=None)` - Process GLM data for all hurricanes

### `orchestration_helpers`
Functions for orchestrating complete data processing pipelines:
- `download_all_data_for_hurricane(hurricane_code, region=None, time_interval=30, box_size=6, nn_tolerance=None, cache_dir=None)` - Process all data (hurricane best track, SHIPS, and GLM) for a single hurricane
- `download_all_data_for_all_hurricanes(region=None, time_interval=30, box_size=6, nn_tolerance=None, cache_dir=None)` - Process all data for all hurricanes in a region

### `time_helpers`
Functions for working with dates and time bins:
- `get_bins_midpoint_times(start_datetime, end_datetime, time_interval)` - Get bin midpoint times
- `get_bins_start_times(start_datetime, end_datetime, time_interval)` - Get bin start times
- `get_bins_end_times(start_datetime, end_datetime, time_interval)` - Get bin end times
- `get_list_of_hours_between_dates(start_date, start_hour, end_date, end_hour)` - Get list of hours between dates

## Data Organization

### Global Data
- **Hurricane best tracks**: `data/global/hurricane/{region}_all_hurricane_best_tracks_{start}_{end}.csv`
- **Hurricane list**: `data/global/hurricane/{region}_hurricane_list_{start}_{end}.csv`
- **SHIPS data**: `data/global/ships/{region}_ships_data_{start}_{end}.csv`

### Storm-Specific Data
Each storm has its own directory: `data/storms/{NAME}_{YEAR}/`
- **Interpolated best track**: `hurricane/besttrack.csv`
- **Interpolated SHIPS data**: `ships/ships_interpolated.csv`
- **GLM lightning groups**: `glm/groups.csv`

### Cache
- **GLM cache**: `data/cache/glm/` - Temporary cache for GLM files (automatically cleared)

## Constants

All time ranges, URLs, and default values are defined in `constants.py`:
- `TS_MIN`, `TS_MAX` - Time range for data processing (2021-2023)
- `DEFAULT_REGION` - Default region ("atl")
- `DEFAULT_NN_TOLERANCE` - Default nearest neighbor tolerance (3 hours)
- `GLM_BUCKET_NAME` - Google Cloud Storage bucket name
- Best track and SHIPS URLs for Atlantic and Pacific regions

## Notes

- All hurricane data is filtered to years 2021-2023 (defined in `constants.py`)
- GLM data is read directly from Google Cloud Storage (no local download required)
- Cache is automatically cleared after each bin and hurricane to free up disk space
- All functions use constants from `constants.py` for time ranges and default values
- The project uses anonymous authentication for GCP (no credentials needed for public data)

## License

See [LICENSE](LICENSE) file for details.

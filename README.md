# Category V - Hurricane and GLM Data Analysis

This project provides tools for downloading, processing, and analyzing Geostationary Lightning Mapper (GLM) data from Google Cloud Storage and correlating it with hurricane data from the HURDAT2 database.

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

The project uses conda to manage dependencies. Create the environment from the `environment.yml` file:

```bash
conda env create -f environment.yml
```

This will create a conda environment named `category-v` with all required dependencies including:
- Python 3.8+
- NetCDF-4 libraries (netcdf4, h5netcdf, h5py, xarray)
- pandas
- Google Cloud Storage libraries
- hurdat2parser

### 3. Activate the environment

```bash
conda activate category-v
```

### 4. Verify installation

You can verify the installation by running:

```bash
python main.py
```

## Project Structure

```
category-v/
├── data/
│   └── glm/
│       ├── raw/          # Raw NetCDF files from GCP
│       └── group/         # Processed files with only group components
├── helpers/
│   ├── glm_helpers.py    # GLM data download and processing
│   ├── hurricane_helpers.py  # Hurricane data manipulation
│   ├── date_helpers.py   # Date/time utilities
│   ├── hurricane_interpolation_helper.py   # Hurricane path interpolation, wind and pressure assigned to closest timestamp
│   ├── tropycal_helpers.py   # Pull hurdat data using tropycal package
│   └── __init__.py
├── main.py               # Main script with examples
├── environment.yml       # Conda environment configuration
└── README.md            # This file
```

## Usage

### Downloading GLM Data

Download and process GLM data for a specific time range:

```python
from helpers.glm_helpers import get_and_parse_all_blobs_between_dates

bucket_name = "gcp-public-data-goes-16"
hours = get_and_parse_all_blobs_between_dates(
    bucket_name,
    '2022-12-13',  # Start date (YYYY-MM-DD)
    '08',           # Start hour (HH)
    '2022-12-13',   # End date (YYYY-MM-DD)
    '09'            # End hour (HH)
)
```

Data will be automatically organized in:
- `data/glm/raw/YYYY/DDD/HH/` - Raw NetCDF files
- `data/glm/group/YYYY/DDD/HH/` - Processed files with only group components

### Working with Hurricane Data

#### Get all hurricanes (2021-2023)

```python
from helpers.hurricane_helpers import HurdatDataManipulator

hurricane_manipulator = HurdatDataManipulator()
all_hurricanes = hurricane_manipulator.get_all_hurricanes(region="atl")
print(f"Found {len(all_hurricanes)} hurricanes")
```

#### Get specific hurricane information

```python
hurricane_info = hurricane_manipulator.get_hurricane_by_name(
    region="atl", 
    name="IAN"
)
if hurricane_info:
    name, start_date, end_date = hurricane_info
    print(f"{name} was active from {start_date} to {end_date}")
```

#### Get hurricane path data

```python
path_df = hurricane_manipulator.get_hurricane_path(
    name="IAN", 
    region="atl"
)
print(path_df.head())  # Shows lat, lon, time for each track point
```

#### Download GLM data for a hurricane's active period

```python
from helpers.glm_helpers import get_and_parse_all_blobs_between_dates

hurricane_info = hurricane_manipulator.get_hurricane_by_name(
    region="atl", 
    name="IAN"
)
if hurricane_info:
    name, start_date, end_date = hurricane_info
    hours = get_and_parse_all_blobs_between_dates(
        bucket_name,
        start_date.strftime('%Y-%m-%d'),
        start_date.strftime('%H'),
        end_date.strftime('%Y-%m-%d'),
        end_date.strftime('%H')
    )
    print(f"Downloaded GLM data for {name}: {len(hours)} files")
```

### Working with Interpolated Hurricane Data

#### Interpolate a hurricane path
```python
import tropycal.tracks as tracks

from helpers.tropycal_helpers import get_storm_list

interp_time_length = 30  # minutes
storm_list = get_storm_list()
# pull example storm name and year
test_storm_name = storm_list["name"].iloc[20]
test_storm_year = storm_list["year"].iloc[20]

# use tropycal to pull all storms 
basin = tracks.TrackDataset(basin='both')
storm = basin.get_storm((test_storm_name,test_storm_year))
storm_df = storm.to_dataframe()

# interpolate path
interp_path_df = hurricane_interpolator.interpolate_path(test_storm_name, test_storm_year, storm_df, interp_time_length)
```

#### Plot an interpolated path
```python
# first run the code above to create the storm_df and interp_path_df
hurricane_interpolator.plot_interpolated_path(storm_df, interp_path_df)
```

#### Interpolate the max wind speed and min pressure variables
```python
# first run the code above to create the storm_df and interp_path_df
wind_pressure_df = storm_df[["time","vmax","mslp"]]
full_hurdat_interp_df = hurricane_interpolator.interpolate_wind_and_pressure(interp_path_df,wind_pressure_df)
```

## Helper Modules

### `glm_helpers`
- `download_blob_from_google()` - Download NetCDF files from GCP
- `store_group_components()` - Extract and save only group variables
- `get_and_parse_all_blobs_for_hour()` - Download all files for a specific hour
- `get_and_parse_all_blobs_between_dates()` - Download files for a date range

### `hurricane_helpers`
- `HurdatDataManipulator` - Main class for hurricane data operations
  - `get_all_hurricanes(region)` - Get all hurricanes (2021-2023)
  - `get_hurricane_by_name(region, name)` - Get specific hurricane info
  - `get_hurricane_path(name, region)` - Get hurricane track data
  - `create_dataframe(region)` - Create pandas DataFrame of hurricane data

### `date_helpers`
- `get_list_of_hours_between_dates()` - Generate list of hours between two dates

### `hurricane_interpolation_helpers`
- `HurricaneInterpolator` - Main class for hurricane interpolation operations
  - `interpolate_path(hurricane_name, original_path_df, interval_minutes=30)` - Interpolate path for given hurricane
  - `plot_interpolated_path(interp_path_df)` - Plot the interpolated hurricane path
  - `interpolate_wind_and_pressure(interpolated_path_df, wind_pressure_df)` - Assign wind and pressure to closest timestamps
### `tropycal_helpers`
- `get_storm_list()` - Return storm name and year for 2021 to 2023 from HurDat dataset

## Data Organization

Downloaded files are automatically organized by:
- **Raw files**: `data/glm/raw/YYYY/DDD/HH/filename.nc`
- **Processed files**: `data/glm/group/YYYY/DDD/HH/filename.nc`

Where:
- `YYYY` = Year (e.g., 2022)
- `DDD` = Day of year (001-365/366)
- `HH` = Hour (00-23)

## Notes

- All hurricane data is filtered to years 2021-2023
- GLM data is downloaded from the public Google Cloud Storage bucket `gcp-public-data-goes-16`
- Processed NetCDF files contain only "group" variables, significantly reducing file size
- The project uses anonymous authentication for GCP (no credentials needed for public data)

## License

See [LICENSE](LICENSE) file for details.

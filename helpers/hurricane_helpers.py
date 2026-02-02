"""
Helper functions for hurricane data.
"""

import os
import fsspec
import pandas as pd
import numpy as np
from datetime import datetime
from pyproj import Geod
from helpers.time_helpers import get_bins_midpoint_times, get_bins_start_times, get_bins_end_times
from constants import TS_MIN, TS_MAX, ATL_BEST_TRACK_URL, NE_PAC_BEST_TRACK_URL, DEFAULT_REGION

## Functions to save all hurricane best track data

def read_best_track(bt_url):
    """
    Parse best track files and extract hurricane intensity and position info

    Args:
        bt_url: URL of hurricane best track file
    
    Returns:
        Dataframe containing intensity/position data from best track file
        (filtered to TS_MIN to TS_MAX from constants)
    """
    
    #Array to store hurricane location data
    hurr_info_array = []
    #Open best track file in fsspec
    with fsspec.open(bt_url, mode="rt") as fobj:
        #Loop through hurricanes
        while True:
            #Data includes a combination of timestamp data and overall hurricane
            #data. 
            #File format: https://www.aoml.noaa.gov/hrd/hurdat/hurdat2-format.pdf

            hurr_info = fobj.readline()
            #print(hurr_info)

            #If the end of the file is reached readline() returns an empty 
            #string.
            if not hurr_info:
                break
            
            try:
                hurr_code, hurr_name, n_lines = hurr_info.replace(" ", "").split(",")[:-1]
            except (ValueError, IndexError):
                # Skip malformed header line
                continue
            
            #Loop through timestamps within each hurricane
            try:
                n_lines_int = int(n_lines)
            except ValueError:
                # Skip if n_lines is not a valid integer
                continue
                
            for row in range(n_lines_int):
                timestamp_info = fobj.readline()
                if not timestamp_info:
                    # EOF reached unexpectedly
                    break
                    
                try:
                    ts_day, ts_min_str, record_identifier, sys_status, lat_hem, lon_hem,\
                    max_sust, min_pres, rad34_ne, rad34_se, rad34_sw, rad34_nw,\
                    rad50_ne, rad50_se, rad50_sw, rad50_nw, rad64_ne, rad64_se,\
                    rad64_sw, rad64_nw, rad_mw = timestamp_info.replace(" ", "").replace("\n", "").split(",")
                except (ValueError, IndexError):
                    # Skip malformed timestamp line
                    continue
                
                #Parse timestamps - only continue if timestamp is in desired
                #range
                try:
                    ts_full = datetime.strptime((ts_day+ts_min_str),"%Y%m%d%H%M")
                except (ValueError, TypeError):
                    # Skip if timestamp parsing fails
                    continue
                    
                if ((ts_full < TS_MIN) or (ts_full > TS_MAX)):
                    continue
                
                #Parse lat/lon (convert coords with hemisphere to absolute)
                try:
                    if len(lat_hem) < 2:
                        continue
                    lat = float(lat_hem[:-1])
                    hem = lat_hem[-1]
                    if hem != 'N':
                        lat *= -1

                    if len(lon_hem) < 2:
                        continue
                    lon = float(lon_hem[:-1])
                    hem = lon_hem[-1]
                    if hem != 'E':
                        lon *= -1
                except (ValueError, IndexError):
                    # Skip if lat/lon parsing fails
                    continue

                timestamp_info_array = [hurr_code, hurr_name, ts_full, sys_status,
                                        lat, lon, max_sust, min_pres,
                                        rad_mw]
                hurr_info_array.append(timestamp_info_array)
    
    #Convert hurr_info_array into a dataframe
    hurr_info_df = pd.DataFrame(hurr_info_array,
                                columns = ['Hurricane Code', 'Hurricane Name',
                                            'Timestamp', 'Status', 'Latitude',
                                            'Longitude',
                                            'Maximum Sustained Winds', 
                                            'Minimum Pressure', 
                                            'Radius of Maximum Winds'])
    
    return hurr_info_df

def save_best_track(bt_url, region):
    """
    Save best track data to a csv file.
    
    Args:
        bt_url: URL of hurricane best track file
        region: Region must be either "atl" (Atlantic) or "pac" (Pacific)
    """
    if region not in ["atl", "pac"]:
        raise ValueError(f"Region must be 'atl' or 'pac', got '{region}'")
    
    best_track_df = read_best_track(bt_url)
    
    # Create directory if it doesn't exist
    os.makedirs('data/global/hurricane', exist_ok=True)
    
    csv_path = f'data/global/hurricane/{region}_all_hurricane_best_tracks_{TS_MIN.strftime("%Y%m%d")}_{TS_MAX.strftime("%Y%m%d")}.csv'
    best_track_df.to_csv(csv_path, index=False)
    print(f"Saved best track data to {csv_path}")
    return best_track_df

def _load_best_track_csv(region):
    """
    Load best track CSV file, creating it if it doesn't exist.
    
    Args:
        region: Region must be either "atl" (Atlantic) or "pac" (Pacific)
    
    Returns:
        pandas.DataFrame with best track data (filtered to TS_MIN to TS_MAX from constants)
    """
    # Determine URL based on region
    if region == "atl":
        bt_url = ATL_BEST_TRACK_URL
    elif region == "pac":
        bt_url = NE_PAC_BEST_TRACK_URL
    else:
        raise ValueError(f"Region must be 'atl' or 'pac', got '{region}'")
    
    # CSV file path
    csv_path = f'data/global/hurricane/{region}_all_hurricane_best_tracks_{TS_MIN.strftime("%Y%m%d")}_{TS_MAX.strftime("%Y%m%d")}.csv'
    
    # Try to load CSV, create if it doesn't exist
    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path, parse_dates=['Timestamp'])
        print(f"Loaded best track data from {csv_path}")
    else:
        print(f"CSV not found at {csv_path}, creating it...")
        df = save_best_track(bt_url, region)
    
    return df

def _list_unique_storms(region):
    """
    Get list of unique hurricanes for a region.
    
    Args:
        region: Region must be either "atl" (Atlantic) or "pac" (Pacific)
    
    Returns:
        List of dictionaries, each representing a hurricane with:
        - name: Hurricane name
        - code: Hurricane code (ATCF ID)
        - year: Start year
        - start_date: First timestamp
        - end_date: Last timestamp
        - statuses_reached: Set of statuses reached
        - entries: DataFrame of all entries for this hurricane
    """
    # Load CSV data (already filtered by time range when created)
    df = _load_best_track_csv(region)
    
    # Group by hurricane code to get unique hurricanes
    hurricanes = []
    for code, group in df.groupby('Hurricane Code'):
        # Get unique name (should be same for all entries)
        name = group['Hurricane Name'].iloc[0]
        
        # Get start and end dates
        start_date = group['Timestamp'].min()
        end_date = group['Timestamp'].max()
        year = start_date.year
        
        # Get all unique statuses reached
        statuses_reached = set(group['Status'].unique())
        
        # Create a simple object-like structure
        hurricane = {
            'name': name,
            'code': code,
            'year': year,
            'start_date': start_date,
            'end_date': end_date,
            'statuses_reached': statuses_reached,
            'entries': group  # DataFrame with all entries
        }
        
        hurricanes.append(hurricane)
    
    return hurricanes

def list_all_hurricanes(region=None):
    """
    List all hurricanes with name, code, start year, dates, and statuses.
    Saves the list to a CSV file in the global directory.
    
    Args:
        region: Region must be either "atl" (Atlantic) or "pac" (Pacific) (defaults to DEFAULT_REGION from constants)
    
    Returns:
        pandas.DataFrame with columns: ['name', 'code', 'year', 'start_date', 'end_date', 'statuses_reached']
    """
    if region is None:
        region = DEFAULT_REGION
    
    filtered_tcs = _list_unique_storms(region)
    hurricanes = []
    
    for tc in filtered_tcs:
        if "HU" in tc['statuses_reached']:  # Only hurricanes
            hurricanes.append({
                "name": tc['name'],
                "code": tc['code'],
                "year": tc['year'],
                "start_date": tc['start_date'],
                "end_date": tc['end_date'],
                "statuses_reached": ",".join(sorted(tc['statuses_reached']))
            })
    
    hurricanes_df = pd.DataFrame(hurricanes)
    
    # Save to CSV
    os.makedirs('data/global/hurricane', exist_ok=True)
    csv_path = f'data/global/hurricane/{region}_hurricane_list_{TS_MIN.strftime("%Y%m%d")}_{TS_MAX.strftime("%Y%m%d")}.csv'
    hurricanes_df.to_csv(csv_path, index=False)
    print(f"Saved hurricane list to {csv_path}")
    
    return hurricanes_df

## Functions to save specific hurricane best track data

def get_hurricane_path(code, region=None):
    """
    Get the full best track DataFrame for a specific hurricane by code.
    
    Args:
        code: Hurricane code (ATCF ID, ex. "AL092022")
        region: Region must be either "atl" (Atlantic) or "pac" (Pacific) (defaults to DEFAULT_REGION from constants)
    
    Returns:
        pandas.DataFrame with full best track data for the hurricane (all columns from the CSV)
        Returns None if hurricane not found
    """
    if region is None:
        region = DEFAULT_REGION
    
    # Load the global CSV
    df = _load_best_track_csv(region)
    
    # Filter by hurricane code
    hurricane_df = df[df['Hurricane Code'] == code].copy()
    
    if len(hurricane_df) == 0:
        return None
    
    return hurricane_df

def interpolate_besttrack_info(besttrack_data_df, bin_times, bin_starts, bin_ends, geod, hurricane_name, hurricane_start_year):
    """
    Interpolate hurricane data df to get storm info at specified times.
    Lat/lon coordinates are interpolated between nearest best-track points, 
    other fields simply are assigned the value of the nearest timestamp.
    Saves the interpolated data to a CSV file.

    Note: bin_times, bin_starts, and bin_ends must be the same length

    Args:
        besttrack_data_df: Dataframe of hurricane info from best track. 
            Should be filtered to one storm.
        bin_times: List of midpoint datetimes of bins where interpolated data is 
            needed
        bin_starts: List of start datetimes of bins
        bin_ends: List of end datetimes of bins
        geod: Geographic datum to use for calculating storm motion direction
        hurricane_name: Name of the hurricane (e.g., "IAN")
        hurricane_start_year: Start year of the hurricane (e.g., 2022)
        
    
    Returns:
        Dataframe containing interpolated hurricane info for times in bin_times
    """
    # Validate inputs
    if len(bin_times) != len(bin_starts) or len(bin_times) != len(bin_ends):
        raise ValueError(f"bin_times ({len(bin_times)}), bin_starts ({len(bin_starts)}), and bin_ends ({len(bin_ends)}) must have the same length")
    
    if len(besttrack_data_df) == 0:
        raise ValueError("besttrack_data_df is empty. Cannot interpolate.")
    
    if len(bin_times) == 0:
        raise ValueError("bin_times is empty. Cannot interpolate.")
    
    #Initialize df to return
    besttrack_interp_df = pd.DataFrame(bin_times, columns = ['Timestamp'])

    #Turn timestamp lists into numerical format
    bin_times_num = [bin_time.timestamp() for bin_time in bin_times]
    bin_starts_num = [bin_start.timestamp() for bin_start in bin_starts]
    bin_ends_num = [bin_end.timestamp() for bin_end in bin_ends]
    hurricane_data_ts_num = [ts.timestamp() for ts in besttrack_data_df['Timestamp']]
    
    # Sort hurricane data by timestamp for interpolation (required by np.interp)
    sort_idx = np.argsort(hurricane_data_ts_num)
    hurricane_data_ts_num_sorted = np.array(hurricane_data_ts_num)[sort_idx]
    hurricane_lats_sorted = besttrack_data_df['Latitude'].values[sort_idx]
    hurricane_lons_sorted = besttrack_data_df['Longitude'].values[sort_idx]

    #Nearest neighbor for hurricane status
    besttrack_interp_df['Status'] = pd.merge_asof(besttrack_interp_df['Timestamp'], 
                                                besttrack_data_df[["Timestamp", "Status"]], 
                                                on="Timestamp", direction="nearest")['Status']

    #Interpolate latitudes/longitudes (np.interp requires sorted x values)
    besttrack_interp_df['Latitude'] = np.interp(bin_times_num, hurricane_data_ts_num_sorted, hurricane_lats_sorted)
    besttrack_interp_df['Longitude'] = np.interp(bin_times_num, hurricane_data_ts_num_sorted, hurricane_lons_sorted)

    #Find storm motion
    #Really janky solution - basically interpolate storm position for start and
    #end times of bin and calculate direction between those
    bin_start_lats = np.interp(bin_starts_num, hurricane_data_ts_num_sorted, hurricane_lats_sorted)
    bin_start_lons = np.interp(bin_starts_num, hurricane_data_ts_num_sorted, hurricane_lons_sorted)
    bin_end_lats = np.interp(bin_ends_num, hurricane_data_ts_num_sorted, hurricane_lats_sorted)
    bin_end_lons = np.interp(bin_ends_num, hurricane_data_ts_num_sorted, hurricane_lons_sorted)

    #List to populate with storm motion directions
    sm_dirs, _, dists = geod.inv(bin_start_lons, bin_start_lats, bin_end_lons, bin_end_lats)
    besttrack_interp_df['Storm Motion Direction (deg)'] = sm_dirs % 360

    #Nearest neighbor interpolation for other storm characteristics
    besttrack_interp_df['Maximum Sustained Winds'] = pd.merge_asof(besttrack_interp_df['Timestamp'], 
                                                                besttrack_data_df[["Timestamp", "Maximum Sustained Winds"]], 
                                                                on="Timestamp", direction="nearest")['Maximum Sustained Winds']
    
    besttrack_interp_df['Minimum Pressure'] = pd.merge_asof(besttrack_interp_df['Timestamp'], 
                                                            besttrack_data_df[["Timestamp", "Minimum Pressure"]], 
                                                            on="Timestamp", direction="nearest")['Minimum Pressure']
    
    besttrack_interp_df['Radius of Maximum Winds'] = pd.merge_asof(besttrack_interp_df['Timestamp'], 
                                                                besttrack_data_df[["Timestamp", "Radius of Maximum Winds"]], 
                                                                on="Timestamp", direction="nearest")['Radius of Maximum Winds'] 

    # Save the interpolated data to CSV
    destination_path = f'data/storms/{hurricane_name}_{hurricane_start_year}/hurricane'
    os.makedirs(destination_path, exist_ok=True)
    
    csv_path = f'{destination_path}/besttrack.csv'
    besttrack_interp_df.to_csv(csv_path, index=False)
    print(f"Saved interpolated best track data to {csv_path}")

    return besttrack_interp_df

def interpolate_besttrack_for_code(hurricane_code, region=None, time_interval=30):
    """
    Interpolate best track data for a hurricane given only its code.
    Automatically determines name, year, region, and creates bins.
    
    Args:
        hurricane_code: Hurricane code (ATCF ID, e.g., "AL092022")
        region: Region ("atl" or "pac"). If None, determined from code (AL=atl, EP=pac)
        time_interval: Time interval in minutes for bins (default: 30)
    
    Returns:
        Dataframe containing interpolated hurricane info
    """
    # Determine region from code if not provided
    if region is None:
        if hurricane_code.startswith('AL'):
            region = 'atl'
        elif hurricane_code.startswith('EP'):
            region = 'pac'
        else:
            raise ValueError(f"Could not determine region from code {hurricane_code}. Please specify region.")
    
    # Load hurricane list to get name and year
    # Use default time range from constants for the CSV filename
    list_csv_path = f'data/global/hurricane/{region}_hurricane_list_{TS_MIN.strftime("%Y%m%d")}_{TS_MAX.strftime("%Y%m%d")}.csv'
    if not os.path.exists(list_csv_path):
        raise FileNotFoundError(f"Hurricane list CSV not found at {list_csv_path}. Run list_all_hurricanes(region='{region}') first.")
    
    hurricanes_df = pd.read_csv(list_csv_path, parse_dates=['start_date', 'end_date'])
    hurricane_info = hurricanes_df[hurricanes_df['code'] == hurricane_code]
    
    if len(hurricane_info) == 0:
        raise ValueError(f"Hurricane code {hurricane_code} not found in hurricane list.")
    
    hurricane_name = hurricane_info['name'].iloc[0]
    hurricane_start_year = int(hurricane_info['year'].iloc[0])
    start_date = hurricane_info['start_date'].iloc[0]
    end_date = hurricane_info['end_date'].iloc[0]
    
    # Get best track data for this hurricane using get_hurricane_path
    # get_hurricane_path uses default time range from constants
    hurricane_besttrack = get_hurricane_path(hurricane_code, region)
    
    if hurricane_besttrack is None or len(hurricane_besttrack) == 0:
        raise ValueError(f"No best track data found for hurricane code {hurricane_code}")
    
    # Create bins
    bin_times = get_bins_midpoint_times(start_date, end_date, time_interval)
    
    if len(bin_times) == 0:
        raise ValueError(f"No bins created for hurricane {hurricane_code}. Check start_date ({start_date}) and end_date ({end_date}).")
    
    # Create bin_starts and bin_ends
    bin_starts = get_bins_start_times(start_date, end_date, time_interval)
    bin_ends = get_bins_end_times(start_date, end_date, time_interval)
    
    # Create geographic datum
    geod = Geod(ellps="WGS84")
    
    # Call interpolate_besttrack_info
    return interpolate_besttrack_info(
        hurricane_besttrack,
        bin_times,
        bin_starts,
        bin_ends,
        geod,
        hurricane_name,
        hurricane_start_year
    )

def interpolate_all_hurricanes_besttrack(region=None, time_interval=30):
    """
    Interpolate best track data for all hurricanes in the hurricane list CSV.
    
    Args:
        region: Region ("atl" or "pac") (defaults to DEFAULT_REGION from constants)
        time_interval: Time interval in minutes for bins (default: 30)
    
    Returns:
        Dictionary mapping hurricane codes to their interpolated DataFrames
    """
    if region is None:
        region = DEFAULT_REGION
    
    # Load hurricane list
    list_csv_path = f'data/global/hurricane/{region}_hurricane_list_{TS_MIN.strftime("%Y%m%d")}_{TS_MAX.strftime("%Y%m%d")}.csv'
    if not os.path.exists(list_csv_path):
        raise FileNotFoundError(f"Hurricane list CSV not found at {list_csv_path}. Run list_all_hurricanes(region='{region}') first.")
    
    hurricanes_df = pd.read_csv(list_csv_path, parse_dates=['start_date', 'end_date'])
    
    # Filter by region (codes starting with AL for atl, EP for pac)
    if region == "atl":
        hurricanes_df = hurricanes_df[hurricanes_df['code'].str.startswith('AL')]
    elif region == "pac":
        hurricanes_df = hurricanes_df[hurricanes_df['code'].str.startswith('EP')]
    else:
        raise ValueError(f"Region must be 'atl' or 'pac', got '{region}'")
    
    results = {}
    total = len(hurricanes_df)
    
    print(f"Processing {total} hurricanes from {region} region...")
    
    for idx, row in hurricanes_df.iterrows():
        code = row['code']
        name = row['name']
        print(f"  [{idx+1}/{total}] Processing {name} ({code})...")
        
        try:
            interp_df = interpolate_besttrack_for_code(
                code,
                region=region,
                time_interval=time_interval
            )
            results[code] = interp_df
        except Exception as e:
            print(f"    Error processing {code}: {e}")
            continue
    
    print(f"Completed: Successfully processed {len(results)}/{total} hurricanes")
    return results

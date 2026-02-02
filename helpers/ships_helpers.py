"""
Helper functions for SHIPS data.
"""

import os
import pandas as pd
import fsspec
from datetime import datetime
from helpers.hurricane_helpers import get_hurricane_bin_midpoint_times, get_hurricane_bin_start_times, get_hurricane_bin_end_times
from constants import TS_MIN, TS_MAX, DEFAULT_REGION, ATL_SHIPS_URL, NE_PAC_SHIPS_URL, DEFAULT_NN_TOLERANCE

# Helper functions to read SHIPS data

def _count_entries_in_range(ships_url):
    """
    Helper function to count how many entries are in the time range.
    This allows us to show percentage progress.
    """
    count = 0
    with fsspec.open(ships_url, mode="rt") as fobj:
        while True:
            result = find_ships_code(fobj, 'HEAD')
            if result is None:
                break
            fobj, header_split = result
            
            try:
                hurr_name, ts_day, ts_hr, max_sust, lat_hem, lon_hem, min_pres,\
                hurr_code, line_code = header_split
            except (ValueError, IndexError):
                continue

            try:
                ts_full = datetime.strptime((ts_day+ts_hr),"%y%m%d%H")
            except (ValueError, TypeError):
                continue
                
            if (ts_full >= TS_MIN) and (ts_full <= TS_MAX):
                count += 1
                # Skip to next section
                result = find_ships_code(fobj, 'LAST')
                if result is not None:
                    fobj, last_split = result
            else:
                # Skip to next section
                result = find_ships_code(fobj, 'LAST')
                if result is not None:
                    fobj, last_split = result
    
    return count

def find_ships_code(fobj, desired_code):
    """
    Helper function for finding a specific line code in SHIPS data files

    Args:
        fobj: data file with current pointer
        desired_code: line code of next line we're interested in. We'll just scan
            through the file until we find a line with that code
    
    Returns:
        Returns that line once we find it. If no line is found, returns None
    """
    #Loop through lines of file
    while True:
        ships_info = fobj.readline()
        #print(ships_info)
        #If no line found, we have reached the end of the file. In the run of
        #this program, that should only occur at the end of a section (we would
        #be looking for code 'HEAD' in that instance)
        if not ships_info:
            if desired_code != 'HEAD':
                print("SHIPS Error: something went wrong while parsing ships data file")
            return None
        
        ships_info_split = ships_info.split()
        line_code = ships_info_split[-1]
        if not line_code == desired_code:
            continue
        else:
            return fobj, ships_info_split

# Functions to save all SHIPS data
def read_ships_data(region=None):
    """
    Helper function for reading through SHIPS data files.

    Args:
        region: Region must be either "atl" (Atlantic) or "pac" (Pacific) (defaults to DEFAULT_REGION from constants)
    
    Returns:
        Dataframe of shear directions and magnitudes for each hurricane and
            timestamp (filtered to TS_MIN to TS_MAX from constants)
    """
    if region is None:
        region = DEFAULT_REGION
    
    # Determine SHIPS URL based on region
    if region == "atl":
        ships_url = ATL_SHIPS_URL
    elif region == "pac":
        ships_url = NE_PAC_SHIPS_URL
    else:
        raise ValueError(f"Region must be 'atl' or 'pac', got '{region}'")

    print(f"Reading SHIPS data from {ships_url}")
    print(f"Time range: {TS_MIN} to {TS_MAX}")
    print("Counting entries in time range...")
    
    # Count total entries in range for progress reporting
    total_entries = _count_entries_in_range(ships_url)
    print(f"Found {total_entries} entries in time range. Processing...")
    
    ships_info_array = []
    processed_count = 0
    skipped_count = 0

    with fsspec.open(ships_url, mode="rt") as fobj:
        while True:
            result = find_ships_code(fobj, 'HEAD')
            if result is None:
                break
            fobj, header_split = result
            
            try:
                hurr_name, ts_day, ts_hr, max_sust, lat_hem, lon_hem, min_pres,\
                hurr_code, line_code = header_split
            except (ValueError, IndexError):
                continue

            try:
                ts_full = datetime.strptime((ts_day+ts_hr),"%y%m%d%H")
            except (ValueError, TypeError):
                continue
                
            if ((ts_full < TS_MIN) or (ts_full > TS_MAX)):
                skipped_count += 1
                continue
            
            result = find_ships_code(fobj, 'SHRD')
            if result is None:
                continue
            fobj, shearmag_split = result
            try:
                shear_850_200_mag = float(shearmag_split[0])/10
            except (ValueError, IndexError):
                continue

            result = find_ships_code(fobj, 'SHTD')
            if result is None:
                continue
            fobj, sheardir_split = result
            try:
                shear_850_200_dir = sheardir_split[0]
            except IndexError:
                continue

            result = find_ships_code(fobj, 'LAST')
            if result is not None:
                fobj, last_split = result

            ships_info_array.append([hurr_code, ts_full, shear_850_200_mag, shear_850_200_dir])
            processed_count += 1
            
            if total_entries > 0:
                percentage = (processed_count / total_entries) * 100
                update_interval = max(10, total_entries // 10)
                if processed_count % update_interval == 0:
                    print(f"  Progress: {processed_count}/{total_entries} ({percentage:.1f}%)", end='\r')
    
    print(f"\nCompleted: Processed {processed_count}/{total_entries} entries, skipped {skipped_count} entries")
    
    #Convert ships info array to dataframe
    ships_info_df = pd.DataFrame(ships_info_array,
                                 columns = ['Hurricane Code', 'Timestamp',
                                            'Shear Magnitude (kts)',
                                            'Shear Direction (deg)'])
    
    return ships_info_df

def save_ships_data(region=None):
    """
    Save SHIPS data for the default time range.

    Args:
        region: Region must be either "atl" (Atlantic) or "pac" (Pacific) (defaults to DEFAULT_REGION from constants)
    """
    if region is None:
        region = DEFAULT_REGION
    
    ships_df = read_ships_data(region)

    # Create directory if it doesn't exist
    os.makedirs('data/global/ships', exist_ok=True)
    
    # Store the data in a csv file
    csv_path = f'data/global/ships/{region}_ships_data_{TS_MIN.strftime("%Y%m%d")}_{TS_MAX.strftime("%Y%m%d")}.csv'
    ships_df.to_csv(csv_path, index=False)
    print(f"Saved SHIPS data to {csv_path}")
    return ships_df

# Functions to interpolate SHIPS data for a given hurricane

def interpolate_ships_info(ships_data_df, bin_times, bin_starts, bin_ends, nn_tolerance):
    """
    Interpolate hurricane data df to get storm info at specified times.
    Lat/lon coordinates are interpolated between nearest best-track points, 
    other fields simply are assigned the value of the nearest timestamp.

    Note: bin_times, bin_starts, and bin_ends must be the same length

    Args:
        ships_data_df: Dataframe of hurricane info (from SHIPS). 
            Should be filtered to one storm.
        bin_times: List of midpoint datetimes of bins where interpolated data is 
            needed
        bin_starts: List of start datetimes of bins
        bin_ends: List of end datetimes of bins
        nn_tolerance: Maximum allowable time from nearest SHIPS data. If nearest
            data is farther away, that timestamp will be assigned nan.
        
    
    Returns:
        Dataframe containing interpolated SHIPS info for times in bin_times
    """
    #Initialize df to return
    ships_interp_df = pd.DataFrame(bin_times, columns = ['Timestamp'])

    #Turn timestamp lists into numerical format
    bin_times_num = [bin_time.timestamp() for bin_time in bin_times]
    bin_starts_num = [bin_start.timestamp() for bin_start in bin_starts]
    bin_ends_num = [bin_end.timestamp() for bin_end in bin_ends]
    hurricane_data_ts_num = [ts.timestamp() for ts in ships_data_df['Timestamp']]
    
    #Assign shear magnitude and direction to nearest neighbor
    ships_interp_df['Shear Magnitude (kts)'] = pd.merge_asof(ships_interp_df['Timestamp'], 
                                                                 ships_data_df[["Timestamp", "Shear Magnitude (kts)"]], 
                                                                 on="Timestamp", direction="nearest", 
                                                                 tolerance=nn_tolerance)['Shear Magnitude (kts)']

    ships_interp_df['Shear Direction (deg)'] = pd.merge_asof(ships_interp_df['Timestamp'], 
                                                                 ships_data_df[["Timestamp", "Shear Direction (deg)"]], 
                                                                 on="Timestamp", direction="nearest",
                                                                  tolerance=nn_tolerance)['Shear Direction (deg)']     

    return ships_interp_df

def interpolate_ships_info_for_hurricane(hurricane_code, nn_tolerance=None, region=None, time_interval=30):
    """
    Interpolate SHIPS data for a given hurricane.

    Args:
        hurricane_code: Hurricane code (e.g., 'AL092022')
        nn_tolerance: Maximum allowable time from nearest SHIPS data (defaults to DEFAULT_NN_TOLERANCE from constants)
        region: Region must be either "atl" (Atlantic) or "pac" (Pacific) (defaults to DEFAULT_REGION from constants)
        time_interval: Time interval in minutes for bins (default: 30)

    Returns:
        Path to the saved interpolated data
    """
    if region is None:
        region = DEFAULT_REGION
    
    if nn_tolerance is None:
        nn_tolerance = DEFAULT_NN_TOLERANCE
    
    # Get hurricane name and year from the hurricane list
    list_csv_path = f'data/global/hurricane/{region}_hurricane_list_{TS_MIN.strftime("%Y%m%d")}_{TS_MAX.strftime("%Y%m%d")}.csv'
    if not os.path.exists(list_csv_path):
        raise FileNotFoundError(f"Hurricane list CSV not found at {list_csv_path}. Run list_all_hurricanes(region='{region}') first.")
    
    hurricanes_df = pd.read_csv(list_csv_path, parse_dates=['start_date', 'end_date'])
    hurricane_info = hurricanes_df[hurricanes_df['code'] == hurricane_code]
    
    if len(hurricane_info) == 0:
        raise ValueError(f"Hurricane code {hurricane_code} not found in hurricane list.")
    
    hurricane_name = hurricane_info['name'].iloc[0]
    hurricane_start_year = int(hurricane_info['year'].iloc[0])
    
    # Get bin times using the new helper functions
    bin_times = get_hurricane_bin_midpoint_times(hurricane_code, region, time_interval)
    bin_starts = get_hurricane_bin_start_times(hurricane_code, region, time_interval)
    bin_ends = get_hurricane_bin_end_times(hurricane_code, region, time_interval)
    
    # Create the directory path to store the interpolated data
    destination_path = f'data/storms/{hurricane_name}_{hurricane_start_year}/ships'
    os.makedirs(destination_path, exist_ok=True)

    # Try reading ships data if it doesn't exist, call save_ships_data
    csv_filename = f'data/global/ships/{region}_ships_data_{TS_MIN.strftime("%Y%m%d")}_{TS_MAX.strftime("%Y%m%d")}.csv'
    try:
        ships_data_df = pd.read_csv(csv_filename, parse_dates=['Timestamp'])
        print(f"Read ships data from {csv_filename}")
    except:
        print(f"SHIPS data not found, downloading and saving to {csv_filename}")
        ships_data_df = save_ships_data(region)

    # Filter the SHIPS data to only include the hurricane
    ships_data_df = ships_data_df[ships_data_df['Hurricane Code'] == hurricane_code]

    # Interpolate the SHIPS data
    ships_interp_df = interpolate_ships_info(ships_data_df, bin_times, bin_starts, bin_ends, nn_tolerance)

    # Save the interpolated data
    csv_path = f'{destination_path}/ships_interpolated.csv'
    ships_interp_df.to_csv(csv_path, index=False)
    print(f"Saved interpolated SHIPS data to {csv_path}")

    return destination_path

def interpolate_all_hurricanes_ships(region=None, time_interval=30, nn_tolerance=None):
    """
    Interpolate SHIPS data for all hurricanes in the hurricane list CSV.
    
    Args:
        region: Region ("atl" or "pac") (defaults to DEFAULT_REGION from constants)
        time_interval: Time interval in minutes for bins (default: 30)
        nn_tolerance: Maximum allowable time from nearest SHIPS data (defaults to DEFAULT_NN_TOLERANCE from constants)
    
    Returns:
        Dictionary mapping hurricane codes to their interpolated data paths
    """
    if region is None:
        region = DEFAULT_REGION
    
    if nn_tolerance is None:
        nn_tolerance = DEFAULT_NN_TOLERANCE    
    
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
    
    print(f"Processing SHIPS data for {total} hurricanes from {region} region...")
    
    for idx, row in hurricanes_df.iterrows():
        code = row['code']
        name = row['name']
        print(f"  [{idx+1}/{total}] Processing {name} ({code})...")
        
        try:
            destination_path = interpolate_ships_info_for_hurricane(
                code,
                nn_tolerance=nn_tolerance,
                region=region,
                time_interval=time_interval
            )
            results[code] = destination_path
        except Exception as e:
            print(f"    Error processing {code}: {e}")
            continue
    
    print(f"Completed: Successfully processed {len(results)}/{total} hurricanes")
    return results

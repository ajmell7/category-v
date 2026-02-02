"""
Helper functions for orchestrating data processing pipelines.
"""

import os
import pandas as pd
from helpers.hurricane_helpers import interpolate_besttrack_for_code
from helpers.ships_helpers import interpolate_ships_info_for_hurricane
from helpers.glm_helpers import process_glm_info_for_hurricane
from constants import TS_MIN, TS_MAX, DEFAULT_REGION

def download_all_data_for_hurricane(hurricane_code, region=None, time_interval=30, 
                                    box_size=6, nn_tolerance=None, cache_dir=None):
    """
    Download and process all data (hurricane best track, SHIPS, and GLM) for a single hurricane.
    Processes data in order: hurricane best track -> SHIPS -> GLM.
    
    Args:
        hurricane_code: Hurricane code (e.g., 'AL092022')
        region: Region ("atl" or "pac"). If None, determined from code (AL=atl, EP=pac)
        time_interval: Time interval in minutes for bins (default: 30)
        box_size: Size of lat/lon box for GLM data in degrees (default: 6)
        nn_tolerance: Maximum allowable time from nearest SHIPS data (defaults to DEFAULT_NN_TOLERANCE from constants)
        cache_dir: Directory to store cached GLM files (default: None, uses temp directory)
    
    Returns:
        Dictionary with paths to processed data:
        {
            'hurricane': path to besttrack.csv,
            'ships': path to ships_interpolated.csv,
            'glm': path to groups.csv
        }
    """
    # Determine region from code if not provided
    if region is None:
        if hurricane_code.startswith('AL'):
            region = 'atl'
        elif hurricane_code.startswith('EP'):
            region = 'pac'
        else:
            raise ValueError(f"Could not determine region from code {hurricane_code}. Please specify region.")
    
    # Load hurricane list to get name
    list_csv_path = f'data/global/hurricane/{region}_hurricane_list_{TS_MIN.strftime("%Y%m%d")}_{TS_MAX.strftime("%Y%m%d")}.csv'
    if not os.path.exists(list_csv_path):
        raise FileNotFoundError(f"Hurricane list CSV not found at {list_csv_path}. Run list_all_hurricanes(region='{region}') first.")
    
    hurricanes_df = pd.read_csv(list_csv_path, parse_dates=['start_date', 'end_date'])
    hurricane_info = hurricanes_df[hurricanes_df['code'] == hurricane_code]
    
    if len(hurricane_info) == 0:
        raise ValueError(f"Hurricane code {hurricane_code} not found in hurricane list.")
    
    hurricane_name = hurricane_info['name'].iloc[0]
    hurricane_start_year = int(hurricane_info['year'].iloc[0])
    
    results = {}
    
    print(f"\n{'='*60}")
    print(f"Processing all data for {hurricane_name} ({hurricane_code})")
    print(f"{'='*60}")
    
    # Step 1: Process hurricane best track data
    print(f"\n[1/3] Processing hurricane best track data...")
    try:
        besttrack_df = interpolate_besttrack_for_code(hurricane_code, region, time_interval)
        # interpolate_besttrack_for_code saves the file internally
        besttrack_path = f'data/storms/{hurricane_name}_{hurricane_start_year}/hurricane/besttrack.csv'
        results['hurricane'] = besttrack_path
        print(f"  ✓ Best track data saved to {besttrack_path}")
    except Exception as e:
        print(f"  ✗ Error processing best track data: {e}")
        results['hurricane'] = None
    
    # Step 2: Process SHIPS data
    print(f"\n[2/3] Processing SHIPS data...")
    try:
        ships_dest_path = interpolate_ships_info_for_hurricane(
            hurricane_code,
            nn_tolerance=nn_tolerance,
            region=region,
            time_interval=time_interval
        )
        # interpolate_ships_info_for_hurricane returns the destination directory, construct full path
        ships_path = f'{ships_dest_path}/ships_interpolated.csv'
        results['ships'] = ships_path
        print(f"  ✓ SHIPS data saved to {ships_path}")
    except Exception as e:
        print(f"  ✗ Error processing SHIPS data: {e}")
        results['ships'] = None
    
    # Step 3: Process GLM data
    print(f"\n[3/3] Processing GLM data...")
    try:
        glm_path = process_glm_info_for_hurricane(
            hurricane_code,
            box_size=box_size,
            region=region,
            time_interval=time_interval,
            cache_dir=cache_dir
        )
        results['glm'] = glm_path
        if glm_path:
            print(f"  ✓ GLM data saved to {glm_path}")
        else:
            print(f"  ⚠ No GLM data found for {hurricane_name}")
    except Exception as e:
        print(f"  ✗ Error processing GLM data: {e}")
        results['glm'] = None
    
    print(f"\n{'='*60}")
    print(f"Completed processing all data for {hurricane_name} ({hurricane_code})")
    print(f"{'='*60}\n")
    
    return results

def download_all_data_for_all_hurricanes(region=None, time_interval=30, 
                                         box_size=6, nn_tolerance=None, cache_dir=None):
    """
    Download and process all data (hurricane best track, SHIPS, and GLM) for all hurricanes.
    Processes data in order: hurricane best track -> SHIPS -> GLM for each hurricane.
    
    Args:
        region: Region ("atl" or "pac") (defaults to DEFAULT_REGION from constants)
        time_interval: Time interval in minutes for bins (default: 30)
        box_size: Size of lat/lon box for GLM data in degrees (default: 6)
        nn_tolerance: Maximum allowable time from nearest SHIPS data (defaults to DEFAULT_NN_TOLERANCE from constants)
        cache_dir: Directory to store cached GLM files (default: None, uses temp directory)
    
    Returns:
        Dictionary mapping hurricane codes to their processed data paths:
        {
            'AL092022': {
                'hurricane': path to besttrack.csv,
                'ships': path to ships_interpolated.csv,
                'glm': path to groups.csv
            },
            ...
        }
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
    
    print(f"\n{'='*80}")
    print(f"Processing all data for {total} hurricanes from {region} region")
    print(f"{'='*80}\n")
    
    for idx, row in hurricanes_df.iterrows():
        code = row['code']
        name = row['name']
        
        try:
            hurricane_results = download_all_data_for_hurricane(
                code,
                region=region,
                time_interval=time_interval,
                box_size=box_size,
                nn_tolerance=nn_tolerance,
                cache_dir=cache_dir
            )
            results[code] = hurricane_results
        except Exception as e:
            print(f"  ✗ Error processing {name} ({code}): {e}")
            results[code] = {
                'hurricane': None,
                'ships': None,
                'glm': None
            }
            continue
    
    # Print summary
    successful_hurricanes = sum(1 for r in results.values() if r.get('hurricane') is not None)
    successful_ships = sum(1 for r in results.values() if r.get('ships') is not None)
    successful_glm = sum(1 for r in results.values() if r.get('glm') is not None)
    
    print(f"\n{'='*80}")
    print(f"Summary: Processed {total} hurricanes")
    print(f"  Best track: {successful_hurricanes}/{total} successful")
    print(f"  SHIPS: {successful_ships}/{total} successful")
    print(f"  GLM: {successful_glm}/{total} successful")
    print(f"{'='*80}\n")
    
    return results

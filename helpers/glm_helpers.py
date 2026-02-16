"""
Helper functions for GLM data.
"""
import math
import os
import shutil
import pandas as pd
import numpy as np
import fsspec
import h5py
from datetime import datetime, timedelta
from google.cloud import storage
from concurrent.futures import ThreadPoolExecutor
from itertools import repeat
from astropy.time import Time
from pyproj import Geod

from helpers.hurricane_helpers import (
    get_hurricane_bin_midpoint_times,
    get_hurricane_bin_start_times,
    get_hurricane_bin_end_times,
    interpolate_besttrack_for_code
)
from constants import DEFAULT_REGION, TS_MIN, TS_MAX, GLM_BUCKET_NAME, METERS_PER_KT, KTS_PER_DEGREE

def process_glm_file_h5py(url, hurricane_code, bin_time, center_lat, center_lon, glm_max_dist, box_size, geod, cache_dir):
    """
    Get lightning group data for a lat/lon box around a hurricane center from a
    GLM file

    Args:
        url: URL of the GLM file
        hurricane_code: Storm code of hurricane
        bin_time: Midpoint time of bin for which to download GLM data
        center_lat: Latitude of hurricane center
        center_lon: Longitude of hurricane center
        glm_max_dist: Distance around hurricane center to get data (in meters)
        box_size: Size of lat/lon box to get data. For instance, if box_size = 6
            and hurricane center is at 0,0, we get lightning data for the area
            between -6 and +6 in latitude and longitude)
        geod: Geographic datum to use for calculating lightning distance from
            hurricane center
        cache_dir: Directory to store cached GLM files

    Returns:
        Dataframe with group data for the specified GLM file and lat/lon box
    """
    try:
        # Cache GLM file (faster to cache locally than scan over network)
        with fsspec.open(f"simplecache::{url}", "rb", cache_storage=cache_dir) as f:
            with h5py.File(f, "r") as ds:
                # Get desired fields from dataset
                lat = ds["group_lat"][:]
                lon = ds["group_lon"][:]
                area = ds["group_area"][:]
                energy = ds["group_energy"][:]
                time_offsets = ds["group_time_offset"][:]
                qflag = ds["group_quality_flag"][:]

                # Mask to filter data by lightning lat/lon coordinates
                mask = (
                    (lat >= center_lat - box_size) & (lat <= center_lat + box_size) &
                    (lon >= center_lon - box_size) & (lon <= center_lon + box_size)
                )
                
                lat = lat[mask]
                lon = lon[mask]
                area = area[mask]
                energy = energy[mask]
                time_offsets = time_offsets[mask]
                qflag = qflag[mask]

                if len(lat) == 0:
                    return None
            
                # product_time is in seconds since J2000 epoch
                product_time = Time("J2000").datetime + timedelta(seconds=int(ds["product_time"][()]))
                
                # Convert time offsets to actual time (all of the group times are
                # saved as offsets from product_time variable). The format is
                # documented on about page 596 here:
                # https://www.goes-r.gov/products/docs/PUG-L2+-vol5.pdf
                time = [product_time + timedelta(seconds=(float(np.uint16(offset))*25/65536)-5) for offset in time_offsets]

                # Calculate lightning distance and direction from storm center
                az, _, dist = geod.inv(
                    np.full_like(lon, center_lon),
                    np.full_like(lat, center_lat),
                    lon,
                    lat
                )

                az = az % 360

                # Compile GLM data into dataframe
                df = pd.DataFrame({
                    "Hurricane Code": hurricane_code,
                    "Bin Time": bin_time,
                    "Group Time": time,
                    "Group Latitude": lat,
                    "Group Longitude": lon,
                    "Group Area": area,
                    "Group Energy": energy,
                    "Group Quality Flag": qflag,
                    "Distance From Hurricane Center (m)": dist,
                    "Direction from Hurricane Center (deg)": az
                })

                #Filter by max distance
                df = df[df["Distance From Hurricane Center (m)"] < glm_max_dist]

                return df

    except Exception as e:
        print(f"Error processing {url}: {e}")
        return None

def aggregate_glm_data_for_urls(glm_urls, hurricane_code, bin_time, center_lat, center_lon, glm_max_dist, geod, cache_dir):
    """
    Get lightning group data for a list of URLs using process_glm_file_h5py
    function

    Args:
        glm_urls: List of URLs of GLM files to process
        hurricane_code: Storm code of hurricane
        bin_time: Midpoint time of bin for which to download GLM data
        center_lat: Latitude of hurricane center
        center_lon: Longitude of hurricane center
        glm_max_dist: Distance around hurricane center to get data (in meters)
        geod: Geographic datum to use for calculating lightning distance from
            hurricane center
        cache_dir: Directory to store cached GLM files

    Returns:
        Dataframe with group data for all the listed GLM files 
    """
    
    #Define box size for filtering GLM data (find rmw_mult_rmw_dist in units of
    #longitude, with a slight 1.1 buffer factor)
    meters_per_degree = METERS_PER_KT*KTS_PER_DEGREE
    box_size = glm_max_dist/math.cos(center_lat*math.pi/180)/meters_per_degree*1.1

    #Place to store individual file outputs from process_glm_file_h5py
    dfs = []

    #Parallelize individual file data reads (48 workers was best in my testing)
    with ThreadPoolExecutor(max_workers=48) as executor:
        for df in executor.map(process_glm_file_h5py, glm_urls, 
                               repeat(hurricane_code), repeat(bin_time), 
                               repeat(center_lat), repeat(center_lon), 
                               repeat(glm_max_dist), repeat(box_size), 
                               repeat(geod), repeat(cache_dir)):
            if df is not None:
                dfs.append(df)

    #Concatenate GLM file outputs into one dataframe and return
    final_df = None
    try:
        if dfs:
            final_df = pd.concat(dfs, ignore_index=True)
    except Exception as e:
        print(f"Error concatenating GLM dataframes: {e}")
    return final_df

def _get_glm_urls_for_time_range(start_date, end_date):
    """
    Get GCS URLs for GLM files in a time range.
    Filters URLs by parsing the filename to extract the start time.
    
    Args:
        start_date: Start datetime
        end_date: End datetime
    
    Returns:
        List of GCS URLs to GLM files within the time range
    """
    glm_urls = []
    current_date = start_date
    
    while current_date <= end_date:
        year = current_date.year
        day_of_year = current_date.timetuple().tm_yday
        hour = current_date.hour
        
        # Construct GCS URL pattern
        prefix = f"GLM-L2-LCFA/{year}/{str(day_of_year).zfill(3)}/{str(hour).zfill(2)}"
        
        # List blobs in GCS
        client = storage.Client.create_anonymous_client()
        bucket = client.bucket(GLM_BUCKET_NAME)
        blobs = list(bucket.list_blobs(prefix=prefix))
        
        for blob in blobs:
            url = f"gs://{GLM_BUCKET_NAME}/{blob.name}"
            glm_urls.append(url)
        
        # Move to next hour
        current_date += timedelta(hours=1)
    
    return glm_urls

def _filter_urls_by_time_range(urls, start_date, end_date):
    """
    Filter a list of GLM URLs to only include files that start within a time range.
    
    Args:
        urls: List of GLM file URLs
        start_date: Start datetime
        end_date: End datetime
    
    Returns:
        List of URLs where file start time is within the time range
    """
    filtered_urls = []
    
    for url in urls:
        try:
            filename = url.split('/')[-1]
            start_time_str = filename.split('_')[3][1:-1]  # Extract s20223140753200, remove 's' and last char
            curr_start_time = datetime.strptime(start_time_str, "%Y%j%H%M%S")
            
            # Only include URLs where start time is within the desired range
            if (curr_start_time >= start_date) and (curr_start_time < end_date):
                filtered_urls.append(url)
        except (IndexError, ValueError):
            # Skip files that don't match expected format
            continue
    
    return filtered_urls

def process_glm_info_for_hurricane(hurricane_code, rmw_mult=5, region=None, time_interval=30, cache_dir=None):
    """
    Process and aggregate GLM data for a given hurricane.
    
    For each bin, gets GLM file URLs and aggregates lightning data around the hurricane center.
    
    Args:
        hurricane_code: Hurricane code (e.g., 'AL092022')
        rmw_mult: Distance around hurricane center to get data (as a multiple
            of the radius of maximum winds)
        region: Region must be either "atl" (Atlantic) or "pac" (Pacific) (defaults to DEFAULT_REGION from constants)
        time_interval: Time interval in minutes for bins (default: 30)
        cache_dir: Directory to store cached GLM files (default: None, uses temp directory)
    
    Returns:
        Path to the saved GLM data CSV
    """
    if region is None:
        region = DEFAULT_REGION
    
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
    start_date = hurricane_info['start_date'].iloc[0]
    end_date = hurricane_info['end_date'].iloc[0]
    
    # Get interpolated best track data to get lat/lon for each bin
    besttrack_interp_df = interpolate_besttrack_for_code(hurricane_code, region, time_interval)
    
    # Get bin times
    bin_times = get_hurricane_bin_midpoint_times(hurricane_code, region, time_interval)
    bin_starts = get_hurricane_bin_start_times(hurricane_code, region, time_interval)
    bin_ends = get_hurricane_bin_end_times(hurricane_code, region, time_interval)
    
    # Create geographic datum
    geod = Geod(ellps="WGS84")
    
    # Create the directory path to store the GLM data
    destination_path = f'data/storms/{hurricane_name}_{hurricane_start_year}/glm'
    os.makedirs(destination_path, exist_ok=True)
    
    if cache_dir is None:
        cache_dir = os.path.join(os.getcwd(), 'data', 'cache', 'glm')
    os.makedirs(cache_dir, exist_ok=True)
    
    print(f"Processing GLM data for {hurricane_name} ({hurricane_code})...")
    print(f"  Time range: {start_date} to {end_date}")
    print(f"  Number of bins: {len(bin_times)}")
    
    # Get all GLM URLs for the entire hurricane time range
    all_glm_urls = _get_glm_urls_for_time_range(start_date, end_date)
    print(f"Found {len(all_glm_urls)} GLM URLs in total")
    
    # Filter URLs to only include files within the hurricane's time range
    all_hurricane_glm_urls = _filter_urls_by_time_range(all_glm_urls, start_date, end_date)
    print(f"  Found {len(all_hurricane_glm_urls)} GLM URLSs within hurricane time range")
    
    # Process each bin
    all_glm_data = []
    for idx, bin_time in enumerate(bin_times):
        print(f"  Processing bin {idx+1}/{len(bin_times)}: {bin_time}")
        
        bin_start = bin_starts[idx]
        bin_end = bin_ends[idx]
        
        # Get hurricane center lat/lon for this bin
        bin_besttrack = besttrack_interp_df[besttrack_interp_df['Timestamp'] == bin_time]
        if len(bin_besttrack) == 0:
            print(f"    Warning: No best track data for bin time {bin_time}")
            continue
        
        center_lat = bin_besttrack['Latitude'].iloc[0]
        center_lon = bin_besttrack['Longitude'].iloc[0]

        #Get radius of maximum winds distance (convert to meters)
        rmw_dist = bin_besttrack['Radius of Maximum Winds'].iloc[0]*METERS_PER_KT
        #Use this to calculate maximum distance from hurricane center to save
        #GLM data
        glm_max_dist = rmw_mult*rmw_dist
        
        # Get GLM URLs for this bin's time range (process_glm_file_h5py reads directly from GCS)
        print(f"    Getting GLM URLs for bin {bin_time}...")
        glm_urls = _filter_urls_by_time_range(all_hurricane_glm_urls, bin_start, bin_end)
        
        if not glm_urls:
            print(f"    No GLM files found for bin {bin_time}")
            continue
        
        # Aggregate GLM data for this bin
        print(f"    Aggregating GLM data from {len(glm_urls)} files...")
        bin_glm_data = aggregate_glm_data_for_urls(glm_urls, hurricane_code, bin_time, center_lat, center_lon, glm_max_dist, geod, cache_dir)
        
        if bin_glm_data is not None and len(bin_glm_data) > 0:
            all_glm_data.append(bin_glm_data)
            print(f"    Found {len(bin_glm_data)} lightning groups")
        else:
            print(f"    No lightning data for bin {bin_time}")
        
        # Clear cache after each bin to free up space
        if os.path.exists(cache_dir):
            shutil.rmtree(cache_dir)
            os.makedirs(cache_dir)
    
    # Combine all bin data
    if all_glm_data:
        merged_glm_data = pd.concat(all_glm_data, ignore_index=True)

        # Save the GLM data
        csv_path = f'{destination_path}/groups.csv'
        merged_glm_data.to_csv(csv_path, index=False)
        print(f"Saved GLM data to {csv_path}")
        print(f"Total lightning groups: {len(merged_glm_data)}")
        
        return csv_path
    else:
        print(f"No GLM data found for {hurricane_name}")
        return None

def process_all_hurricanes_glm(rmw_mult=5, region=None, time_interval=30, cache_dir=None):
    """
    Process GLM data for all hurricanes in the hurricane list CSV.
    
    Args:
        rmw_mult: Distance around hurricane center to get data (as a multiple
            of the radius of maximum winds)
        region: Region ("atl" or "pac") (defaults to DEFAULT_REGION from constants)
        time_interval: Time interval in minutes for bins (default: 30)
        cache_dir: Directory to store cached GLM files (default: None, uses temp directory)
    
    Returns:
        Dictionary mapping hurricane codes to their GLM data paths
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
    
    print(f"Processing GLM data for {total} hurricanes from {region} region...")
    
    for idx, row in hurricanes_df.iterrows():
        code = row['code']
        name = row['name']
        print(f"\n[{idx+1}/{total}] Processing {name} ({code})...")
        
        try:
            csv_path = process_glm_info_for_hurricane(
                code,
                rmw_mult=rmw_mult,
                region=region,
                time_interval=time_interval,
                cache_dir=cache_dir
            )
            if csv_path:
                results[code] = csv_path
            
            # Clear cache after each hurricane to free up space
            if cache_dir and os.path.exists(cache_dir):
                shutil.rmtree(cache_dir)
                os.makedirs(cache_dir)
        except Exception as e:
            print(f"    Error processing {code}: {e}")
            # Clear cache even on error
            if cache_dir and os.path.exists(cache_dir):
                shutil.rmtree(cache_dir)
                os.makedirs(cache_dir)
            continue
    
    print(f"\nCompleted: Successfully processed {len(results)}/{total} hurricanes")
    return results
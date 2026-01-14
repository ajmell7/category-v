"""
Helper functions for GLM data.
"""
import xarray as xr
import os
from google.cloud import storage
from helpers.date_helpers import get_list_of_hours_between_dates

def download_blob_from_google(bucket_name, blob_name):
    """
    Download a file from Google Cloud Storage.
    
    Args:
        bucket_name: Name of the GCS bucket (gcp-public-data-goes-16)
        blob_name: Path to the file within the bucket (GLM-L2-LCFA/YYYY/DDD/HH/filename.nc)
    
    Returns:
        Stores the file in the data/glm/raw/year/day/hour/filename directory
        str: Path to the downloaded file
    """
    client = storage.Client.create_anonymous_client()
    
    # Get the bucket and blob
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)

    # Parse blob_name to extract year, day, hour
    path_parts = blob_name.split('/')
    
    if len(path_parts) >= 4:
        year = path_parts[1]
        day = str(int(path_parts[2]))
        hour = str(int(path_parts[3]))
        filename = os.path.basename(blob_name)
        
        # Create directory structure: data/glm/raw/year/day/hour
        destination_path = os.path.join('data', 'glm', 'raw', year, day, hour, filename)
    else:        
        # Log a warning if the blob_name format is invalid
        print(f"ERROR: Invalid blob_name format: {blob_name}")

        return None
    
    # Make directory structure if it doesn't exist
    os.makedirs(os.path.dirname(destination_path), exist_ok=True)
    
    # Download the file
    blob.download_to_filename(destination_path)
    
    return destination_path

def store_group_components(nc_file):    
    """
    Store the group components of a NetCDF file.

    Args:
        nc_file: Path to the NetCDF file
    
    Returns:
        Stores the NetCDF file with only the group components under the data/glm/group/ directory
    """

    # Parse the file name to extract the year, day, hour
    file_name = os.path.basename(nc_file)
    path_parts = nc_file.split('/')
    year = path_parts[3]
    day = path_parts[4]
    hour = path_parts[5]

    # Create the directory structure: data/glm/group/year/day/hour
    destination_path = os.path.join('data', 'glm', 'group', year, day, hour)
    os.makedirs(destination_path, exist_ok=True)
    
    # Open the NetCDF file
    ds = xr.open_dataset(nc_file)

    # Find all group dimensions in the dataset
    group_data_vars = [var for var in ds.data_vars if var.startswith('group')]
    group_coords = {var: ds.coords[var] for var in ds.coords if var.startswith('group')}

    # Create a new dataset with only the group components
    ds_group = ds[group_data_vars].assign_coords(group_coords)

    # TODO: Ensure that we are grabbing the correct group data and any needed attributes

    # Save global attributes
    ds_group.attrs = ds.attrs

    # NOTE: Filtering the nc_file significantly reduces the file size.

    # Save the filtered group dataset to the destination path
    ds_group.to_netcdf(os.path.join(destination_path, file_name))

    return destination_path

def get_and_parse_all_blobs_for_hour(bucket_name, year, day, hour):
    """
    Download all blobs for a given hour.
    
    Args:
        bucket_name: Name of the Google Cloud Storage bucket
        year: Year (YYYY)
        day: Day (DDD)
        hour: Hour (HH)
    
    Returns:
        List of downloaded files

        Stores the blobs in the data/glm/raw/year/day/hour directory
        Stores the group components in the data/glm/group/year/day/hour directory
    """
    client = storage.Client.create_anonymous_client()
    bucket = client.bucket(bucket_name)
    blobs = list(bucket.list_blobs(prefix=f"GLM-L2-LCFA/{year}/{day}/{hour}"))
    
    if not blobs:
        print(f"No blobs found for hour {hour} of day {day} in year {year}")
        return []

    # Download each blob
    downloaded_files = []
    for blob in blobs:
        raw_nc_file = download_blob_from_google(bucket_name, blob.name)
        if raw_nc_file:
            store_group_components(raw_nc_file)
            downloaded_files.append(raw_nc_file)

    print(f"Downloaded and parsed {len(downloaded_files)} nc_files for the hour {hour} of day {day} in year {year}")
    
    return downloaded_files

def get_and_parse_all_blobs_between_dates(bucket_name, start_date, start_hour, end_date, end_hour):
    """
    Get and parse all blobs between two dates.

    Args:
        bucket_name: Name of the Google Cloud Storage bucket
        start_date: Start date (YYYY-MM-DD)
        start_hour: Start hour (HH)
        end_date: End date (YYYY-MM-DD)
        end_hour: End hour (HH)
    """

    # Get the list of hours between the start and end dates
    hours = get_list_of_hours_between_dates(start_date, start_hour, end_date, end_hour)
    
    # Get and parse all blobs for each hour
    for year, day, hour in hours:
        get_and_parse_all_blobs_for_hour(bucket_name, year, day, hour)

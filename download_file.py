#!/usr/bin/env python3
"""
Simple script to download a NetCDF file from Google Cloud Storage.
"""

import xarray as xr
import os

from helpers import download_blob_from_google, store_group_components

def download_gcs_file(bucket_name, blob_name):
    """
    Download a file from Google Cloud Storage.
    
    Args:
        bucket_name: Name of the GCS bucket
        blob_name: Path to the file within the bucket
        destination_path: Local path to save the file (defaults to filename)
    """
    # Download the file using the helper function
    destination_path = download_blob_from_google(bucket_name, blob_name)
    print(f"Downloaded file to: {destination_path}")

    # Store the group components
    output_path = store_group_components(destination_path)    
    print(f"Stored group components to: {output_path}")

if __name__ == "__main__":
    # GCS URL: https://storage.googleapis.com/gcp-public-data-goes-16/GLM-L2-LCFA/2022/010/16/OR_GLM-L2-LCFA_G16_s20220101600400_e20220101601000_c20220101601026.nc
    bucket_name = "gcp-public-data-goes-16"
    blob_name = "GLM-L2-LCFA/2022/010/16/OR_GLM-L2-LCFA_G16_s20220101600400_e20220101601000_c20220101601026.nc"
    
    download_gcs_file(bucket_name, blob_name)

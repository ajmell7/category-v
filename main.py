#!/usr/bin/env python3
"""
Main file to test the helper functions.
"""
import os

from helpers.glm_helpers import get_and_parse_all_blobs_between_dates
from helpers.hurricane_helpers import HurdatDataManipulator
from helpers.hurricane_interpolation_helpers import HurricaneInterpolator

if __name__ == "__main__":
    bucket_name = "gcp-public-data-goes-16"
    

    # Example: Get GLM data for a specific time range
    # Creates the directory paths to store the raw and parsed data.
    # hours = get_and_parse_all_blobs_between_dates(bucket_name,'2022-12-13', '08', '2022-12-13', '09')
    # print(f"Hours: {hours}")
    
    # Example: Use HurdatDataManipulator to get hurricane data
    hurricane_manipulator = HurdatDataManipulator()
    hurricane_interpolator = HurricaneInterpolator()
    
    # Example: Get all hurricanes
    all_hurricanes = hurricane_manipulator.get_all_hurricanes(region="atl")
    print(f"Found {len(all_hurricanes)} hurricanes in Atlantic basin")
    print("First 5 hurricanes:", all_hurricanes[:5])
    
    # Example: Get specific hurricane by name
    hurricane_name = "IAN"  # Example hurricane name
    hurricane_info = hurricane_manipulator.get_hurricane_by_name(region="atl", name=hurricane_name)
    if hurricane_info:
        name, start_date, end_date = hurricane_info
        print(f"{name} was active from {start_date} to {end_date}")
    
    # Example: Get hurricane path data
    path_df = hurricane_manipulator.get_hurricane_path(name=hurricane_name, region="atl")
    if path_df is not None:
        print(f"\n{hurricane_name} path data:")
        print(path_df.head())
        print(f"Total track points: {len(path_df)}")

    # Example: Interpolate hurricane path
    interp_path_df = hurricane_interpolator.interpolate_path(hurricane_name, path_df, 30)
    #hurricane_interpolator.plot_interpolated_path(interp_path_df)
    wind_pressure_df = hurricane_manipulator.get_hurricane_wind_and_pressure(name=hurricane_name, region="atl")
    if wind_pressure_df is not None:
        print(f"\n{hurricane_name} wind and pressure data:")
        print(wind_pressure_df.head())
        print(f"Total points: {len(wind_pressure_df)}")
    full_hurdat_interp_df = hurricane_interpolator.interpolate_wind_and_pressure(interp_path_df,wind_pressure_df)
    
    # Example: Download GLM data for a hurricane's active period
    # if start_date and end_date:
    #     hours = get_and_parse_all_blobs_between_dates(
    #         bucket_name,
    #         start_date.strftime('%Y-%m-%d'),
    #         start_date.strftime('%H'),
    #         end_date.strftime('%Y-%m-%d'),
    #         end_date.strftime('%H')
    #     )
    #     print(f"Downloaded GLM data for {hurricane_name}: {len(hours)} files")

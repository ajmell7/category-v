#!/usr/bin/env python3
"""
Main file to test the helper functions.
"""
import os
import pandas as pd

from helpers.hurricane_helpers import (
    list_all_hurricanes,
    interpolate_besttrack_for_code,
    interpolate_all_hurricanes_besttrack
)
from helpers.ships_helpers import save_ships_data, interpolate_ships_info_for_hurricane, interpolate_all_hurricanes_ships
from helpers.glm_helpers import process_all_hurricanes_glm, process_glm_info_for_hurricane

from helpers.orchestration_helpers import download_all_data_for_hurricane, download_all_data_for_all_hurricanes


if __name__ == "__main__":

    # Download all hurricanes in the Atlantic region
    list_all_hurricanes()

    # You can inspect the full list of hurricanes in the Atlantic region in the data/global/hurricane/atl_hurricane_list_20220101_20220131.csv file
    # It has the following columns: name, code, year, start_date, end_date, statuses_reached

    # Download all data for a specific hurricane
    NICOLE = "AL172022"
    IAN = "AL092022"

    # download_all_data_for_hurricane("AL172022")

    # Analyze quality flag counts for NICOLE_2022
    glm_csv_path = "data/storms/NICOLE_2022/glm/groups.csv"
    
    if os.path.exists(glm_csv_path):
        print(f"Reading GLM data from {glm_csv_path}...")
        glm_df = pd.read_csv(glm_csv_path)
        
        print(f"\nTotal lightning groups: {len(glm_df)}")
        print("\nQuality Flag Value Counts:")
        print("=" * 50)
        quality_flag_counts = glm_df['Group Quality Flag'].value_counts().sort_index()
        for flag_value, count in quality_flag_counts.items():
            percentage = (count / len(glm_df)) * 100
            print(f"  {flag_value}: {count:,} ({percentage:.2f}%)")
        print("=" * 50)
    else:
        print(f"GLM data file not found at {glm_csv_path}")

#!/usr/bin/env python3
"""
Main file to test the helper functions.
"""
import os
import pandas as pd

from helpers.hurricane_helpers import list_all_hurricanes
from helpers.orchestration_helpers import download_all_data_for_hurricane, download_all_data_for_all_hurricanes
from helpers.glm_density import plot_glm_density_gif
from datetime import datetime


if __name__ == "__main__":
    import sys
    
    # Force unbuffered output
    sys.stdout = sys.__stdout__
    sys.stderr = sys.__stderr__
    
    print("Starting hurricane data processing...", flush=True)
    # Download all hurricanes in the Atlantic region
    list_all_hurricanes()

    # You can inspect the full list of hurricanes in the Atlantic region in the data/global/hurricane/atl_hurricane_list_20220101_20220131.csv file
    # It has the following columns: name, code, year, start_date, end_date, statuses_reached

    # Download all data for a specific hurricane
    NICOLE = "AL172022"
    IAN = "AL092022"
    DON = "AL052023"
    LISA = "AL152022"
    BONNIE = "AL022022"

    # Uncomment to download data (requires google.cloud.storage and protobuf)
    # download_all_data_for_hurricane(BONNIE)
    
    # Plot GLM data for DON as animated GIF
    don_glm_path = "data/storms/IAN_2022/glm/groups.csv"
    if os.path.exists(don_glm_path):
        # Create density plot GIF for all bin times
        print(f"\nCreating density plot GIF for DON GLM data...")
        # density_gif_path = plot_glm_density_gif(
        #     don_glm_path,
        #     quality_flag=0,
        #     cell_size=0.1,
        #     save_path="data/storms/IAN_2022/glm/density_animation.gif",
        #     interval=100,
        #     fps=10
        # )

        density_gif_path = plot_glm_density_gif(
            don_glm_path,
            besttrack_path='data/storms/IAN_2022/hurricane/besttrack.csv',
            quality_flag=0,
            cell_size=0.1,
            box_size=10  # ±10 degrees
        )

        if density_gif_path:
            print(f"Density GIF saved to {density_gif_path}")
    else:
        print(f"GLM data not found at {don_glm_path}")

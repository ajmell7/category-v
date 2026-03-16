"""
Home Install page for the Tropical Storm Visualization Tool.
"""

import streamlit as st
import pandas as pd
import os

from helpers.hurricane_helpers import (
    list_all_hurricanes,
    interpolate_besttrack_for_code,
    get_hurricane_bin_midpoint_times,
)
from helpers.ships_helpers import (
    save_ships_data,
    interpolate_all_hurricanes_ships,
)
from helpers.glm_helpers import (
    process_glm_info_for_hurricane,
)
from constants import DEFAULT_REGION, TS_MIN, TS_MAX

st.set_page_config(layout="wide")
st.title("Home/Installation")

st.header("Welcome to the Tropical Storm Visualization Tool")
st.markdown("""
This tool helps you visualize and analyze tropical storm data including:
- Lightning group histograms
- Hurricane paths
- Density GIFs
- Shear plots

**Getting Started:**

Before you can use the visualization features, you need to set up the hurricane data.
This will download and process the best track data for all hurricanes in the database.
""")

st.divider()

st.subheader("Step 1: Download All Tropical Storms")
st.markdown("""
This step will download and create a list of all tropical storms from the best track database.
This may take a few minutes depending on your internet connection.
""")

if st.button("Download all tropical storms", key="list_hurricanes_btn"):
    with st.spinner("Downloading and processing hurricane list..."):
        try:
            hurricanes_df = list_all_hurricanes(region=DEFAULT_REGION)
            st.success(f"Successfully listed {len(hurricanes_df)} hurricanes!")
            st.dataframe(hurricanes_df, use_container_width=True)
            st.session_state['hurricanes_listed'] = True
            st.session_state['hurricanes_df'] = hurricanes_df
        except Exception as e:
            st.error(f"Error listing hurricanes: {e}")
            st.session_state['hurricanes_listed'] = False

st.divider()

st.subheader("Step 2: Interpolate Best Track Data")
st.markdown("""
This step will interpolate the best track data for all hurricanes.
This creates time-binned data that is used by the visualization tools.
This process may take several minutes.
""")

if st.button("Interpolate All Hurricanes", key="interpolate_btn"):
    if 'hurricanes_listed' not in st.session_state or not st.session_state['hurricanes_listed']:
        st.warning("Please complete Step 1 first (Download all tropical storms).")
    else:
        hurricanes_df = st.session_state.get('hurricanes_df')
        if hurricanes_df is None or len(hurricanes_df) == 0:
            st.warning("No hurricanes found. Please complete Step 1 first.")
        else:
            progress_bar = st.progress(0)
            status_text = st.empty()
            results = []
            
            total = len(hurricanes_df)
            for idx, row in hurricanes_df.iterrows():
                code = row['code']
                name = row['name']
                status_text.text(f"Processing {name} ({code})... [{idx+1}/{total}]")
                
                try:
                    interp_df = interpolate_besttrack_for_code(code, region=DEFAULT_REGION)
                    results.append({"code": code, "name": name, "status": "Success"})
                except Exception as e:
                    results.append({"code": code, "name": name, "status": f"Error: {str(e)}"})
                
                progress_bar.progress((idx + 1) / total)
            
            status_text.text("Completed!")
            st.success(f"Successfully processed {sum(1 for r in results if r['status'] == 'Success')}/{total} hurricanes")
            
            # Show results table
            results_df = pd.DataFrame(results)
            st.dataframe(results_df, use_container_width=True)
            
            st.session_state['interpolation_complete'] = True

st.divider()

st.subheader("Step 3: Download SHIPS Data")
st.markdown("""
This step will download and save SHIPS (Statistical Hurricane Intensity Prediction Scheme) data.
This data contains environmental information such as wind shear for tropical storms.
This may take a few minutes depending on your internet connection.
""")

if st.button("Download SHIPS Data", key="download_ships_btn"):
    with st.spinner("Downloading and processing SHIPS data..."):
        try:
            ships_df = save_ships_data(region=DEFAULT_REGION)
            st.success(f"Successfully downloaded SHIPS data with {len(ships_df)} entries!")
            st.session_state['ships_downloaded'] = True
        except Exception as e:
            st.error(f"Error downloading SHIPS data: {e}")
            st.session_state['ships_downloaded'] = False

st.divider()

st.subheader("Step 4: Interpolate SHIPS Data")
st.markdown("""
This step will interpolate the SHIPS data for all hurricanes.
This creates time-binned SHIPS data that is used by the visualization tools.
This process may take several minutes.
""")

if st.button("Interpolate All Hurricanes SHIPS Data", key="interpolate_ships_btn"):
    # Check if hurricane list CSV exists (from Step 1)
    list_csv_path = f'data/global/hurricane/{DEFAULT_REGION}_hurricane_list_{TS_MIN.strftime("%Y%m%d")}_{TS_MAX.strftime("%Y%m%d")}.csv'
    ships_csv_path = f'data/global/ships/{DEFAULT_REGION}_ships_data_{TS_MIN.strftime("%Y%m%d")}_{TS_MAX.strftime("%Y%m%d")}.csv'
    
    if not os.path.exists(list_csv_path):
        st.warning("Please complete Step 1 first (Download all tropical storms).")
    elif not os.path.exists(ships_csv_path):
        st.warning("Please complete Step 3 first (Download SHIPS Data).")
    else:
        with st.spinner("Interpolating SHIPS data for all hurricanes..."):
            try:
                results = interpolate_all_hurricanes_ships(region=DEFAULT_REGION)
                st.success(f"Successfully interpolated SHIPS data for {len(results)} hurricanes!")
                st.session_state['ships_interpolation_complete'] = True
            except Exception as e:
                st.error(f"Error interpolating SHIPS data: {e}")
                st.session_state['ships_interpolation_complete'] = False

st.divider()

st.subheader("Step 5: Download GLM Data")
st.markdown("""
This step will download GLM (Geostationary Lightning Mapper) data for a selected hurricane.
This data contains lightning group information around the hurricane center.
This process may take several minutes per hurricane.

**Note:** You can only process one hurricane at a time. Select a hurricane from the dropdown below.
""")

# Check if hurricane list exists
list_csv_path = f'data/global/hurricane/{DEFAULT_REGION}_hurricane_list_{TS_MIN.strftime("%Y%m%d")}_{TS_MAX.strftime("%Y%m%d")}.csv'

if not os.path.exists(list_csv_path):
    st.warning("Please complete Step 1 first (Download all tropical storms).")
else:
    # Load hurricane list for dropdown
    try:
        hurricanes_df = pd.read_csv(list_csv_path)
        hurricane_options = hurricanes_df.apply(lambda row: f"{row['name']} ({row['code']}) - {row['year']}", axis=1).tolist()
        
        selected_hurricane = st.selectbox(
            "Select Hurricane to Process",
            options=[""] + hurricane_options,
            key="glm_hurricane_selectbox"
        )
        
        if selected_hurricane:
            # Extract hurricane code from selection
            hurricane_code = selected_hurricane.split('(')[1].split(')')[0]
            
            if st.button("Download GLM Data", key="download_glm_btn"):
                # Optional: estimate number of bins to give the user a sense of scale
                try:
                    bin_times = get_hurricane_bin_midpoint_times(hurricane_code, region=DEFAULT_REGION)
                    num_bins = len(bin_times)
                    estimate_msg = (
                        f"Processing approximately {num_bins} 30-minute bins. "
                        "This may take 10–30 minutes depending on the storm duration."
                    )
                except Exception:
                    num_bins = None
                    estimate_msg = "This may take 10–30 minutes depending on the storm duration."
                
                # Show a spinner and an info message while the long-running
                # function executes. Streamlit will update this once when the
                # function starts and again when it finishes.
                with st.spinner("Downloading GLM data..."):
                    st.info(f"🔄 Starting GLM data download for {selected_hurricane}.\n{estimate_msg}")
                    try:
                        csv_path = process_glm_info_for_hurricane(
                            hurricane_code,
                            region=DEFAULT_REGION,
                        )
                        if csv_path:
                            st.success(f"Successfully downloaded GLM data for {selected_hurricane}!")
                            st.info(f"📁 Data saved to: `{csv_path}`")
                        else:
                            st.warning(f"No GLM data found for {selected_hurricane}")
                    except Exception as e:
                        st.error(f"Error downloading GLM data: {e}")
    except Exception as e:
        st.error(f"Error loading hurricane list: {e}")

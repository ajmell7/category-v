import streamlit as st 
import pandas as pd
import imageio.v2 as imageio
import io
import random

from helpers.plot_helpers import (
    pull_hurricane_data, 
    get_lightining_groups, 
    create_histogram, 
    plot_hurricane_path_interactive,
    plot_bin_lightning
)

from helpers.hurricane_helpers import (
    get_hurricane_bin_midpoint_times,
    get_hurricane_bin_start_times,
    get_hurricane_bin_end_times
)

st.set_page_config(layout="wide")
st.title("Hurricane Plots")

# Get all hurricane information
@st.cache_data
def load_hurricane_list():
    return pd.read_csv(
        "data/global/hurricane/atl_hurricane_list_20210101_20231231.csv"
    )

all_hurricanes = load_hurricane_list()
hurricane_names = sorted(all_hurricanes["name"].unique())


#st.subheader("Select Hurricane")

col1, col2, col3 = st.columns([1, 1, 3])  # 1 = small, 4 = large

with col1:
    hurricane_name = st.selectbox("Select Hurricane", hurricane_names, key="hurricane_selectbox")
# with col2:
#     land_or_ocean = st.multiselect("Surface Geography", ["Land", "Ocean"], default = ["Land","Ocean"], key="land_ocean_selectbox")

hurricane_code, hurricane_year, glm_df, best_track_df = pull_hurricane_data(all_hurricanes, hurricane_name)

# initialize bin times 
bin_times = get_hurricane_bin_midpoint_times(hurricane_code, region="atl", time_interval=30)
bin_starts = get_hurricane_bin_start_times(hurricane_code, region="atl", time_interval=30)
bin_ends = get_hurricane_bin_end_times(hurricane_code, region="atl", time_interval=30)

# Get Lightning group dataframe for each bin time
lightning_groups_inner_core_df, lightning_groups_outer_core_df, lightning_groups_all_df = get_lightining_groups(bin_times, bin_starts, bin_ends, best_track_df, glm_df)

# Create tabs
tab1, tab2, tab3 = st.tabs(["Lightning Group Histogram", "Hurricane Path", "GIF Testing"])

with tab1:
    st.header("Lightning Group Histogram")
    #st.write("Content for the first sheet.")

    fig = create_histogram(lightning_groups_inner_core_df,lightning_groups_outer_core_df,best_track_df,hurricane_name,hurricane_year)
    st.pyplot(fig)

with tab2:
    st.header("Hurricane Path")
    #st.write("Content for the second sheet.")

    fig = plot_hurricane_path_interactive(best_track_df, hurricane_name)
    st.plotly_chart(fig, use_container_width=True)

# with tab3:
#     st.header("GIF Testing")
#     #Get and plot GLM data for each bin
#     frames = []

#     for idx in range(len(bin_times)):
#         bin_time = bin_times[idx]
#         bin_start = bin_starts[idx]
#         bin_end = bin_ends[idx]
        
#         center_lat = best_track_df.loc[best_track_df['Timestamp'] == bin_time, 'Latitude'].iloc[0]
#         center_lon = best_track_df.loc[best_track_df['Timestamp'] == bin_time, 'Longitude'].iloc[0]

#         random_numbers = [random.randint(-5, 5) for _ in range(100)]

#         bin_df = pd.DataFrame(columns=['lat', 'long'])

#         bin_df['lat'] = center_lat + random_numbers
#         bin_df['long'] = center_lon + random_numbers

#         # bin_df = lightning_groups_all_df[
#         #     (lightning_groups_all_df["time"] >= bin_start) &
#         #     (lightning_groups_all_df["time"] < bin_end)
#         # ]

#         # if bin_df.empty:
#         #     st.write(f"No lightning for {bin_start}")
#         #     continue

#         frame = plot_bin_lightning(
#             bin_df,
#             bin_start,
#             bin_end,
#             center_lat,
#             center_lon,
#             box_size=6
#         )

#         frames.append(imageio.imread(frame))

#     gif_buf = io.BytesIO()
#     imageio.mimsave(gif_buf, frames, format="GIF", duration=0.5)
#     gif_buf.seek(0)
#     st.image(gif_buf, caption="Lightning Evolution Near Hurricane Center")
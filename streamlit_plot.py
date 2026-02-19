import streamlit as st 
import pandas as pd

from helpers.plot_helpers import (
    pull_hurricane_data, 
    get_lightining_groups, 
    create_histogram, 
    plot_hurricane_path_interactive
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

col1, col2 = st.columns([1, 4])  # 1 = small, 4 = large

with col1:
    hurricane_name = st.selectbox("Select Hurricane", hurricane_names, key="hurricane_selectbox")


hurricane_code, hurricane_year, glm_df, best_track_df = pull_hurricane_data(all_hurricanes, hurricane_name)

# initialize bin times 
bin_times = get_hurricane_bin_midpoint_times(hurricane_code, region="atl", time_interval=30)
bin_starts = get_hurricane_bin_start_times(hurricane_code, region="atl", time_interval=30)
bin_ends = get_hurricane_bin_end_times(hurricane_code, region="atl", time_interval=30)

# Get Lightning group dataframe for each bin time
lightning_groups_inner_core_df, lightning_groups_outer_core_df = get_lightining_groups(bin_times, bin_starts, bin_ends, best_track_df, glm_df)

# Create tabs
tab1, tab2 = st.tabs(["Lightning Group Histogram", "Hurricane Path"])

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
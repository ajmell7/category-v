import streamlit as st 
import pandas as pd
import imageio.v2 as imageio
import base64

from PIL import Image

from helpers.plot_helpers import (
    pull_minimal_hurricane_data,
    plot_hurricane_path_interactive
)

st.set_page_config(layout="wide")
st.title("Tropical Storm Visualization Tool")

# Create tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs(["Lightning Group Histogram", 
                                        "Hurricane Path", 
                                        "Density GIFs", 
                                        "Shear Plots (all)", 
                                        "Shear Plots (individual)"])

# Get all hurricane information (only if available)
try:
    @st.cache_data
    def load_hurricane_list():
        return pd.read_csv("data/global/hurricane/atl_hurricane_list_20190101_20231231.csv")
    
    all_hurricanes = load_hurricane_list()
    hurricane_names = sorted(all_hurricanes["name"].unique())
except:
    all_hurricanes = pd.DataFrame()
    hurricane_names = []

t_numbers = ["All", "1_5", "2", "2_5", "3", "3_5", "4", "4_5", "5", "5_5", "6", "6_5", "7", "7_5", "8"]
intensification_stages = ["All", "NC", "I", "RI", "W", "RW"]

# Only show other tabs if hurricane data is available
if len(hurricane_names) > 0:
    col1, col2, col3 = st.columns([1, 1, 3])
    
    with col1:
        hurricane_name = st.selectbox("Select Hurricane", hurricane_names, key="hurricane_selectbox")
    
    hurricane_code, hurricane_year, best_track_df = pull_minimal_hurricane_data(all_hurricanes, hurricane_name)
else:
    # Create dummy variables to prevent errors
    hurricane_name = None
    hurricane_code = None
    hurricane_year = None
    best_track_df = None

with tab1:
    st.header("Lightning Group Histogram")
    
    if hurricane_name is None:
        st.warning("Please complete the setup steps in the 'Home Install' tab first.")
    else:
        try:
            image = Image.open(f'plots/histograms/{hurricane_name}_{hurricane_year}_histogram.png')
            st.image(image, width="stretch")
        except:
            st.warning("No histogram available for this hurricane.")

with tab2:
    st.header("Hurricane Path")
    
    if hurricane_name is None or best_track_df is None:
        st.warning("Please complete the setup steps in the 'Home Install' tab first.")
    else:
        try:
            fig = plot_hurricane_path_interactive(best_track_df, hurricane_name)
            st.plotly_chart(fig, width="stretch")
        except Exception as e:
            st.warning(f"Error displaying hurricane path: {e}")

with tab3:
    st.header("Density GIFs")
    
    if hurricane_name is None:
        st.warning("Please complete the setup steps in the 'Home Install' tab first.")
    else:
        try:
            file_ = open(f"plots/density_gifs/{hurricane_name}_{hurricane_year}_density.gif", "rb")
            contents = file_.read()
            data_url = base64.b64encode(contents).decode("utf-8")
            file_.close()

            st.markdown(
                f'''
                <img src="data:image/gif;base64,{data_url}" 
                    alt="density gif" 
                    width=50%>
                ''',
                unsafe_allow_html=True,
            )
        except:
            st.warning("No density GIF available for this hurricane.")

with tab4:
    st.header("Shear Plots (all)")

    ##############
    ## Create selectbox for T-number
    col1, col2, col3 = st.columns([1, 1, 3])  # 1 = small, 4 = large
    with col1:
        t_number = st.selectbox("T Number", t_numbers, key="t_number_selectbox_all")
    with col2:
        intensification_stage = st.selectbox("Intensification Stage", intensification_stages, key="intensity_selectbox_all")
    ##############

    col1, col2 = st.columns([3, 3])  # 1 = small, 4 = large
    
    with col1:
        st.caption("Shear Plots using Azimuth")
        try:
            if t_number == "All" and intensification_stage == "All":
                image = Image.open(f'plots/shear_plots/azimuth/Atlantic_Basin_All_Hurricanes__azimuth.png')
            elif intensification_stage == "All":
                image = Image.open(f'plots/shear_plots/azimuth/Atlantic_Basin_All_Hurricanes_T__{t_number}__azimuth.png')
            elif t_number == "All":
                image = Image.open(f'plots/shear_plots/azimuth/Atlantic_Basin_All_Hurricanes_{intensification_stage}_Only__azimuth.png')
            else:
                image = Image.open(f'plots/shear_plots/azimuth/Atlantic_Basin_All_Hurricanes_T__{t_number}_{intensification_stage}_Only__azimuth.png')
            st.image(image, width="stretch")
        except:
            st.warning("No plot available for this combination of T-number and Intensification Stage.")

    with col2:
        st.caption("Shear Plots using RMW")
        try:
            if t_number == "All" and intensification_stage == "All":
                image = Image.open(f'plots/shear_plots/rmwxy/Atlantic_Basin_All_Hurricanes__RMWXY.png')
            elif intensification_stage == "All":
                image = Image.open(f'plots/shear_plots/rmwxy/Atlantic_Basin_All_Hurricanes_T__{t_number}__RMWXY.png')
            elif t_number == "All":
                image = Image.open(f'plots/shear_plots/rmwxy/Atlantic_Basin_All_Hurricanes_{intensification_stage}_Only__RMWXY.png')
            else:
                image = Image.open(f'plots/shear_plots/rmwxy/Atlantic_Basin_All_Hurricanes_T__{t_number}_{intensification_stage}_Only__RMWXY.png')
            st.image(image, width="stretch")
        except:
            st.warning("No plot available for this combination of T-number and Intensification Stage.")

with tab5:
    st.header("Shear Plots (individual)")

    ##############
    ## Create selectbox for T-number
    col1, col2, col3 = st.columns([1, 1, 3])  # 1 = small, 4 = large
    with col1:
        t_number = st.selectbox("T Number", t_numbers, key="t_number_selectbox_individual")
    with col2:
        intensification_stage = st.selectbox("Intensification Stage", intensification_stages, key="intensity_selectbox_individual")
    ##############

    col1, col2 = st.columns([3, 3])  # 1 = small, 4 = large
    
    with col1:
        st.caption("Shear Plots using Azimuth")
        try:
            if t_number == "All" and intensification_stage == "All":
                image = Image.open(f'plots/shear_plots/azimuth/Atlantic_Basin_Hurricane_{hurricane_name.capitalize()}__azimuth.png')
            elif intensification_stage == "All":
                image = Image.open(f'plots/shear_plots/azimuth/Atlantic_Basin_Hurricane_{hurricane_name.capitalize()}_T__{t_number}__azimuth.png')
            elif t_number == "All":
                image = Image.open(f'plots/shear_plots/azimuth/Atlantic_Basin_Hurricane_{hurricane_name.capitalize()}_{intensification_stage}_Only__azimuth.png')
            else:
                image = Image.open(f'plots/shear_plots/azimuth/Atlantic_Basin_Hurricane_{hurricane_name.capitalize()}_T__{t_number}_{intensification_stage}_Only__azimuth.png')
            st.image(image, width="stretch")
        except:
            st.warning("No plot available for this combination of T-number and Intensification Stage.")

    with col2:
        st.caption("Shear Plots using RMW")
        try:
            if t_number == "All" and intensification_stage == "All":
                image = Image.open(f'plots/shear_plots/rmwxy/Atlantic_Basin_Hurricane_{hurricane_name.capitalize()}__RMWXY.png')
            elif intensification_stage == "All":
                image = Image.open(f'plots/shear_plots/azimuth/Atlantic_Basin_Hurricane_{hurricane_name.capitalize()}_T__{t_number}__RMWXY.png')
            elif t_number == "All":
                image = Image.open(f'plots/shear_plots/azimuth/Atlantic_Basin_Hurricane_{hurricane_name.capitalize()}_{intensification_stage}_Only__RMWXY.png')
            else:
                image = Image.open(f'plots/shear_plots/azimuth/Atlantic_Basin_Hurricane_{hurricane_name.capitalize()}_T__{t_number}_{intensification_stage}_Only__RMWXY.png')
            st.image(image, width="stretch")
        except:
            st.warning("No plot available for this combination of T-number and Intensification Stage.")
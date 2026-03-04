#Imports
import matplotlib.pyplot as plt
import pandas as pd
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import plotly.express as px
import plotly.graph_objects as go
import contextily as cx
import io
import traceback

def nautical_miles_to_meters(nautical_miles):
    """
    Converts a distance in nautical miles to meters.

    Args:
        nautical_miles (float or int): The distance in nautical miles.

    Returns:
        float: The equivalent distance in meters.
    """
    conversion_factor = 1852
    meters = nautical_miles * conversion_factor
    return meters


def pull_hurricane_data(all_hurricanes, hurricane_name):
    # Select specific hurricane and pull corresponding data
    specific_hurricane = all_hurricanes[all_hurricanes['name'] == hurricane_name]
    hurricane_code = specific_hurricane['code'].values[0]
    hurricane_year = specific_hurricane['year'].values[0]

    glm_df = pd.read_csv(f"data/storms/{hurricane_name}_{hurricane_year}/glm/groups.csv", parse_dates=['Group Time'])
    best_track_df = pd.read_csv(f'data/storms/{hurricane_name}_{hurricane_year}/hurricane/besttrack.csv', parse_dates=['Timestamp'])
    return hurricane_code, hurricane_year, glm_df, best_track_df

def pull_minimal_hurricane_data(all_hurricanes, hurricane_name):
    # Select specific hurricane and pull corresponding data
    specific_hurricane = all_hurricanes[all_hurricanes['name'] == hurricane_name]
    hurricane_code = specific_hurricane['code'].values[0]
    hurricane_year = specific_hurricane['year'].values[0]

    best_track_df = pd.read_csv(f'data/storms/{hurricane_name}_{hurricane_year}/hurricane/besttrack.csv', parse_dates=['Timestamp'])
    return hurricane_code, hurricane_year, best_track_df

def get_lightining_groups(bin_times, bin_starts, bin_ends, best_track_df, glm_df):
    # Get lightning group counts for each bin of histogram
    lightning_groups_inner_core = []
    lightning_groups_outer_core = []
    lightning_groups_all = []
    glm_df = glm_df[glm_df["Group Quality Flag"] == 0] # filter to only include quality flag 0

    for idx in range(len(bin_times)):
        bin_time = bin_times[idx]
        #print(bin_time)
        bin_start = bin_starts[idx]
        bin_end = bin_ends[idx]

        try:
            # get RMW at bin time
            rmw_nautical = best_track_df[best_track_df['Timestamp'] == bin_time]['Radius of Maximum Winds'].values[0]
            rmw_meters = nautical_miles_to_meters(rmw_nautical)
            inner_core_filter = 1.5*rmw_meters
            outer_core_filter = 5*rmw_meters
            # get land vs ocean at bin time 
            physical_geography = best_track_df[best_track_df['Timestamp'] == bin_time]['Geography'].values[0]
            # filter bin time
            filter_glm_data = glm_df[(glm_df["Group Time"] >= bin_start) & (glm_df["Group Time"] < bin_end)]
            # filter data to only include lightning within 400 km of hurricane center
            filter_glm_data_inner_core = filter_glm_data[filter_glm_data["Distance From Hurricane Center (m)"] <= inner_core_filter]
            filter_glm_data_outer_core = filter_glm_data[(filter_glm_data["Distance From Hurricane Center (m)"] > inner_core_filter) & (filter_glm_data["Distance From Hurricane Center (m)"] <= outer_core_filter)]
            num_groups_inner_core = len(filter_glm_data_inner_core)
            num_groups_outer_core = len(filter_glm_data_outer_core)
            num_groups_all = num_groups_inner_core + num_groups_outer_core
            #print(num_groups)
            lightning_groups_inner_core.append([bin_time,num_groups_inner_core, physical_geography])
            lightning_groups_outer_core.append([bin_time,num_groups_outer_core, physical_geography])
            lightning_groups_all.append([bin_time,num_groups_all, physical_geography])
        except Exception as e:
            print(f'No Lightning for bin {bin_time}: {e}')
            traceback.print_exc()

    lightning_groups_inner_core_df = pd.DataFrame(lightning_groups_inner_core, columns=["time", "groups", "geography"])
    lightning_groups_outer_core_df = pd.DataFrame(lightning_groups_outer_core, columns=["time", "groups", "geography"])
    lightning_groups_all_df = pd.DataFrame(lightning_groups_all, columns=["time", "groups", "geography"])
    return lightning_groups_inner_core_df, lightning_groups_outer_core_df, lightning_groups_all_df



def create_histogram(lightning_groups_inner_core_df,lightning_groups_outer_core_df,best_track_df,hurricane_name,hurricane_year):
    fig, axes = plt.subplots(1, 2, figsize=(16, 6), sharey=False)
    fig.suptitle(f"{hurricane_name} {hurricane_year}: GLM Groups \n (blue = water, orange = land)", fontsize=16)

    # Helper to draw one panel
    def plot_panel(ax, lightning_df, title):
        geo_colors = {
            "Ocean": "tab:blue",
            "Land": "tab:orange"
        }
        geo_colors = lightning_df["geography"].map(geo_colors)
        # Left axis: GLM group count
        ax.bar(
            lightning_df['time'],
            lightning_df['groups'],
            width=0.03,
            color= geo_colors, #'tab:blue',
            label='GLM Groups'
        )
        ax.set_title(title)
        ax.set_ylabel('Group Count')
        ax.tick_params(axis='x', labelrotation=90)

        # Right axis 1: Pressure
        ax_r1 = ax.twinx()
        ax_r1.plot(
            best_track_df['Timestamp'],
            best_track_df['Minimum Pressure'],
            color='tab:green',
            linewidth=1,
            label='Pressure (mb)'
        )
        ax_r1.set_ylim(800, 1100)
        ax_r1.set_ylabel('Pressure (mb)', color='tab:green')

        # Right axis 2: Wind speed
        ax_r2 = ax.twinx()
        ax_r2.plot(
            best_track_df['Timestamp'],
            best_track_df['Maximum Sustained Winds'],
            color='tab:red',
            linewidth=1,
            label='Sustained Wind (knots)'
        )
        ax_r2.set_ylim(0, 200)
        ax_r2.set_ylabel('Sustained Wind (knots)', color='tab:red')
        ax_r2.spines['right'].set_position(('outward', 60))

         # Right axis 3: RMW
        ax_r3 = ax.twinx()
        ax_r3.plot(
            best_track_df['Timestamp'],
            best_track_df['Radius of Maximum Winds'],
            color='tab:purple',
            linewidth=1,
            label='RMW (nautical miles)'
        )
        ax_r3.set_ylim(0, 200)
        ax_r3.set_ylabel('RMW (nautical miles)', color='tab:purple')
        ax_r3.spines['right'].set_position(('outward', 120))

        # Combined legend
        lines, labels = [], []
        for a in [ax, ax_r1, ax_r2, ax_r3]:
            l, lab = a.get_legend_handles_labels()
            lines.extend(l)
            labels.extend(lab)
        ax.legend(lines, labels, loc='best')

    # Left subplot: Inner core
    plot_panel(axes[0], lightning_groups_inner_core_df, "r <= 1.5RMW")

    # Right subplot: Outer core
    plot_panel(axes[1], lightning_groups_outer_core_df, "1.5RMW < r <= 5RMW")

    plt.tight_layout(rect=[0, 0, 1, 0.95])
    return fig

def plot_hurricane_path(best_track_df, hurricane):
    # Get interpolated lat long points
    interp_lat = best_track_df['Latitude'].values
    interp_lon = best_track_df['Longitude'].values

    # Create figure
    fig = plt.figure(figsize=(10, 6))
    ax = fig.add_subplot(1, 1, 1, projection=ccrs.PlateCarree())

    min_lat = min(interp_lat) - 10
    max_lat = max(interp_lat) + 10
    min_lon = min(interp_lon) - 10
    max_lon = max(interp_lon) + 10

    # Add background geography
    ax.set_extent([min_lon, max_lon, min_lat, max_lat], crs=ccrs.PlateCarree()) # set lat long bounds
    ax.coastlines() # add coastlines
    ax.add_feature(cfeature.LAND) # add land color
    ax.add_feature(cfeature.OCEAN) # add ocean color
    ax.gridlines(draw_labels=True)
    ax.set_title(f"Interpolated Path for {hurricane}")

    # Plot water points
    ax.scatter(
        interp_lon,
        interp_lat,
        s=5,
        color='blue',
        marker='o',
        transform=ccrs.PlateCarree(),
    )

    ax.legend()

    return fig

def calculate_hurricane_category(wind_speed_series):
    bins = [-1, 33, 63, 82, 95, 112, 136, float("inf")]
    labels = [
        "Tropical Depression",
        "Tropical Storm",
        "Category 1",
        "Category 2",
        "Category 3",
        "Category 4",
        "Category 5",
    ]
    return pd.cut(wind_speed_series, bins=bins, labels=labels)


def plot_hurricane_path_interactive(best_track_df, hurricane):
    best_track_df['Category'] = calculate_hurricane_category(best_track_df['Maximum Sustained Winds'])
    fig = px.scatter_mapbox(
        best_track_df,
        lat="Latitude",
        lon="Longitude",
        color = "Category",
        hover_data={
            "Timestamp": True,
            "Latitude": ':.4f',
            "Longitude": ':.4f',
            "Minimum Pressure": True,
            "Maximum Sustained Winds": True,
            "Radius of Maximum Winds": True
        },
        labels={
            "Minimum Pressure": "Minimum Pressure (mb)",
            "Maximum Sustained Winds": "Maximum Sustained Winds (knots)",
            "Radius of Maximum Winds": "Radius of Maximum Winds (nautical miles)"
        },
        zoom=3,
        height=800,
        width = 600
    )

    fig.update_layout(
        mapbox_style="open-street-map"
    )

    return fig


def plot_bin_lightning(final_df, bin_start, bin_end, center_lat, center_lon, box_size):
    '''
    Plot lightning groups in vicinity of hurricane center

    Args:
        final_df: Dataframe containing lightning group data within time bin
        bin_start: Start datetime of bin
        bin_end: End datetime of bin
        center_lat: Latitude of hurricane center to draw on plot
        center_lon: Longitude of hurricane center to draw on plot
        box_size: Size of box around hurricane center to show in plot

    Returns:
        None (just shows plot)
    '''
    fig, ax = plt.subplots(figsize=(8,8))
    plt.scatter(final_df['long'], final_df['lat'], s=2, label='Lightning Group')
    plt.scatter(center_lon, center_lat, color='black', label='Hurricane Center')
    plt.xlim(center_lon - box_size, center_lon + box_size)
    plt.ylim(center_lat - box_size, center_lat + box_size)
    plt.xlabel('Longitude (deg)')
    plt.ylabel('Latitude (deg)')
    cx.add_basemap(ax, crs="EPSG:4326", source=cx.providers.OpenStreetMap.Mapnik)
    plt.title(f'Lightning Groups Near Hurricane Ian Center, {bin_start}-{bin_end}')
    plt.legend()

    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)

    return buf
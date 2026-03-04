import pandas as pd
import imageio.v2 as imageio
import io
import random
import matplotlib.pyplot as plt


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

def load_hurricane_list():
    return pd.read_csv(
        "data/global/hurricane/atl_hurricane_list_20210101_20231231.csv"
    )

all_hurricanes = load_hurricane_list()
hurricane_names = sorted(all_hurricanes["name"].unique())

for hurricane_name in hurricane_names:

    hurricane_code, hurricane_year, glm_df, best_track_df = pull_hurricane_data(all_hurricanes, hurricane_name)

    # initialize bin times 
    bin_times = get_hurricane_bin_midpoint_times(hurricane_code, region="atl", time_interval=30)
    bin_starts = get_hurricane_bin_start_times(hurricane_code, region="atl", time_interval=30)
    bin_ends = get_hurricane_bin_end_times(hurricane_code, region="atl", time_interval=30)

    # Get Lightning group dataframe for each bin time
    lightning_groups_inner_core_df, lightning_groups_outer_core_df, lightning_groups_all_df = get_lightining_groups(bin_times, bin_starts, bin_ends, best_track_df, glm_df)

    fig = create_histogram(lightning_groups_inner_core_df,lightning_groups_outer_core_df,best_track_df,hurricane_name,hurricane_year)

    # Save the figure
    fig.savefig(f"plots/histograms/{hurricane_name}_{hurricane_year}_histogram.png",
                dpi=300,
                bbox_inches="tight")
    
    plt.close(fig)
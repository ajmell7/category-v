import numpy as np
import pandas as pd
import datetime as dt
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature

from geographiclib.geodesic import Geodesic


class HurricaneInterpolator:
    def __init__(self):
        self.hurricane_name = None

    def interpolate_path(self, hurricane_name, original_path_df, interval_minutes=30):
        """Interpolate hurricane path to get (lat, long) location every 30 minutes."""
        geod = Geodesic.WGS84
        original_path_df = original_path_df.reset_index(drop=True)
        interp_points = []
        self.hurricane_name = hurricane_name
        for row_i in range(len(original_path_df)-1):
            point1 = original_path_df.iloc[row_i]
            point2 = original_path_df.iloc[row_i+1]
            lat1 = point1["lat"]
            lon1 = point1["lon"]
            lat2 = point2["lat"]
            lon2 = point2["lon"]
            start_time = point1["time"]
            end_time = point2["time"]
            delta_minutes = int((point2["time"] - point1["time"]).total_seconds() / 60)
            n_steps = delta_minutes // interval_minutes

            line = geod.InverseLine(lat1, lon1, lat2, lon2)
            
            # add first point without interpolation
            if row_i == 0:
                interp_points.append([start_time, lat1, lon1])

            for point_i in range(1,n_steps):
                frac = (interval_minutes * point_i) / delta_minutes
                s = line.s13 * min(frac, 1.0)
                pos = line.Position(s)
                t = start_time + dt.timedelta(minutes=interval_minutes*point_i)
                interp_points.append([t, pos['lat2'], pos['lon2']])

            interp_points.append([end_time, lat2, lon2])

        interp_path_df = pd.DataFrame(interp_points,columns=["time", "lat", "lon"])
        return interp_path_df


    def plot_interpolated_path(self, orig_path_df, interp_path_df):
        """Plot interpolated hurricane path on a map."""
        # Get interpolated lat long points
        interp_lat = interp_path_df['lat'].values
        interp_lon = interp_path_df['lon'].values
        orig_lat = orig_path_df['lat'].values
        orig_lon = orig_path_df['lon'].values

        # Create figure
        fig = plt.figure(figsize=(10, 6))
        ax = fig.add_subplot(1, 1, 1, projection=ccrs.PlateCarree())

        # Add background geography
        ax.set_extent([-90, -60, 10, 35], crs=ccrs.PlateCarree()) # set lat long bounds
        ax.coastlines() # add coastlines
        ax.add_feature(cfeature.LAND) # add land color
        ax.add_feature(cfeature.OCEAN) # add ocean color
        ax.gridlines(draw_labels=True)
        ax.set_title("Interpolated Path for Hurricane " + self.hurricane_name)

        # Plot interpolated points on map
        ax.scatter(interp_lon, interp_lat, color='red', marker='o', transform=ccrs.PlateCarree())
        ax.scatter(orig_lon, orig_lat, color='blue', marker='x', edgecolor='black', transform=ccrs.PlateCarree())

        plt.show()


    def interpolate_wind_and_pressure(self, interpolated_path_df, wind_pressure_df):
        """Interpolate wind and pressure data to match interpolated path timestamps."""
        # Merge dataframes on time with interpolation
        full_hurdat_interp_df = pd.merge_asof(
            interpolated_path_df.sort_values('time'),
            wind_pressure_df.sort_values('time'),
            on='time',
            direction='nearest',
            tolerance=pd.Timedelta('6H')
        )
        full_hurdat_interp_df.to_csv("full_hurdat_interp_df.csv", index=False)
        return full_hurdat_interp_df
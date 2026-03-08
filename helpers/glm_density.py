"""
Helper functions for GLM data density analysis and visualization.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from datetime import datetime
import os
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from pyproj import Geod

def filter_glm_data_for_quality(glm_df, quality_flag=0):
    """
    Filter the GLM data for a specific quality flag.
    
    Args:
        glm_df: DataFrame with GLM data
        quality_flag: Quality flag value to filter for (default: 0)
    
    Returns:
        Filtered DataFrame
    """
    glm_df = glm_df[glm_df['Group Quality Flag'] == quality_flag]
    return glm_df


def find_max_min_coords(glm_df):
    """
    Find the max and min latitude and longitude from GLM data.
    
    Args:
        glm_df: DataFrame with GLM data
    
    Returns:
        Tuple of (max_latitude, min_latitude, max_longitude, min_longitude)
    """
    max_latitude = glm_df['Group Latitude'].max()
    min_latitude = glm_df['Group Latitude'].min()
    max_longitude = glm_df['Group Longitude'].max()
    min_longitude = glm_df['Group Longitude'].min()
    
    return max_latitude, min_latitude, max_longitude, min_longitude


def find_bin_area(min_latitude, max_latitude, min_longitude, max_longitude):
    """
    Calculate area by integrating over the lat/lon rectangle.
    """
    geod = Geod(ellps='WGS84')
    
    # Four corners of the rectangle
    lons = [min_longitude, max_longitude, max_longitude, min_longitude]
    lats = [min_latitude, min_latitude, max_latitude, max_latitude]
    
    # polygon_area_perimeter takes lons and lats as separate lists
    area_m2, _ = geod.polygon_area_perimeter(lons, lats)
    
    return abs(area_m2) / 1_000_000  # Convert m² to km²


def compute_density_grid(frame_data, min_latitude, max_latitude, min_longitude, max_longitude, cell_size=0.1):
    """
    Compute density grid by counting lightning groups in each cell.
    
    Args:
        frame_data: DataFrame with GLM data for a single bin time
        min_latitude: Minimum latitude for grid bounds
        max_latitude: Maximum latitude for grid bounds
        min_longitude: Minimum longitude for grid bounds
        max_longitude: Maximum longitude for grid bounds
        cell_size: Size of each cell in degrees (default: 0.1 for 0.1° x 0.1° cells)
    
    Returns:
        Tuple of (density_counts, lon_edges, lat_edges)
        - density_counts: 2D numpy array with counts per cell
        - lon_edges: Longitude bin edges
        - lat_edges: Latitude bin edges
    """
    if len(frame_data) == 0:
        # Return empty grid if no data
        lon_bins = np.arange(min_longitude, max_longitude + cell_size, cell_size)
        lat_bins = np.arange(min_latitude, max_latitude + cell_size, cell_size)
        return np.zeros((len(lat_bins) - 1, len(lon_bins) - 1)), lon_bins, lat_bins
    
    # Create bin edges
    lon_bins = np.arange(min_longitude, max_longitude + cell_size, cell_size)
    lat_bins = np.arange(min_latitude, max_latitude + cell_size, cell_size)
    
    # Compute 2D histogram (counts per cell)
    counts, x_edges, y_edges = np.histogram2d(
        frame_data['Group Longitude'].values,
        frame_data['Group Latitude'].values,
        bins=[lon_bins, lat_bins]
    )
    
    # Transpose to get (lat, lon) orientation for plotting
    density_counts = counts.T
    
    return density_counts, x_edges, y_edges


def load_besttrack_data(besttrack_path):
    """
    Load besttrack data and create a mapping from timestamp to (latitude, longitude).
    
    Args:
        besttrack_path: Path to besttrack CSV file
    
    Returns:
        Dictionary mapping timestamp to (lat, lon) tuple, or None if file doesn't exist
    """
    if not besttrack_path or not os.path.exists(besttrack_path):
        return None
    
    besttrack_df = pd.read_csv(besttrack_path, parse_dates=['Timestamp'])
    
    # Create a dictionary mapping timestamp to (lat, lon)
    besttrack_data = {}
    for _, row in besttrack_df.iterrows():
        besttrack_data[row['Timestamp']] = (row['Latitude'], row['Longitude'])

    return besttrack_data


def get_hurricane_center(bin_time, besttrack_data):
    """
    Get hurricane center (lat, lon) for a given bin time from besttrack data.
    
    Args:
        bin_time: Bin time to look up
        besttrack_data: Dictionary mapping timestamp to (lat, lon), or None
    
    Returns:
        Tuple of (latitude, longitude) if found, None otherwise
    """
    if besttrack_data is None:
        return None
    
    # Try exact match first
    if bin_time in besttrack_data:
        return besttrack_data[bin_time]
    
    # Try to find closest timestamp
    closest_time = min(besttrack_data.keys(), key=lambda t: abs((t - bin_time).total_seconds()))
    time_diff = abs((closest_time - bin_time).total_seconds())
    
    # Only use if within 30 minutes
    if time_diff <= 1800:
        return besttrack_data[closest_time]
    
    return None


def calculate_frame_bounds(bin_time, besttrack_data, global_bounds, box_size):
    """
    Calculate the bounds for a frame based on hurricane center or global bounds.
    
    Args:
        bin_time: Bin time for this frame
        besttrack_data: Dictionary mapping timestamp to (lat, lon), or None
        global_bounds: Tuple of (min_lat, max_lat, min_lon, max_lon)
        box_size: Size of box around hurricane center in degrees
    
    Returns:
        Tuple of (min_lat, max_lat, min_lon, max_lon)
    """
    min_lat, max_lat, min_lon, max_lon = global_bounds
    
    if besttrack_data:
        center = get_hurricane_center(bin_time, besttrack_data)
        if center:
            center_lat, center_lon = center
            return (
                center_lat - box_size,
                center_lat + box_size,
                center_lon - box_size,
                center_lon + box_size
            )
    
    # Fall back to global bounds
    return (min_lat, max_lat, min_lon, max_lon)


def precompute_density_grids(glm_df, besttrack_data, global_bounds, box_size, cell_size):
    """
    Pre-compute density grids for all bin times.
    
    Args:
        glm_df: Filtered GLM DataFrame
        besttrack_data: Dictionary mapping timestamp to (lat, lon), or None
        global_bounds: Tuple of (min_lat, max_lat, min_lon, max_lon)
        box_size: Size of box around hurricane center in degrees
        cell_size: Size of each cell in degrees
    
    Returns:
        Tuple of (density_grids dict, max_density value)
        density_grids maps bin_time to (density_counts, min_lat, max_lat, min_lon, max_lon)
    """
    time_groups = glm_df.groupby('Bin Time')
    unique_times = sorted(glm_df['Bin Time'].unique())
    
    print("Pre-computing density grids...")
    density_grids = {}
    max_density = 0
    
    for current_time in unique_times:
        frame_data = time_groups.get_group(current_time)
        
        # Calculate bounds for this frame
        frame_min_lat, frame_max_lat, frame_min_lon, frame_max_lon = calculate_frame_bounds(
            current_time, besttrack_data, global_bounds, box_size
        )
        
        # Compute density grid
        density_counts, _, _ = compute_density_grid(
            frame_data, frame_min_lat, frame_max_lat, frame_min_lon, frame_max_lon, cell_size
        )
        
        # Store grid and bounds
        density_grids[current_time] = (density_counts, frame_min_lat, frame_max_lat, frame_min_lon, frame_max_lon)
        max_density = max(max_density, density_counts.max())
    
    return density_grids, max_density


def setup_map_plot(extent_bounds):
    """
    Set up a cartopy map plot with standard features.
    
    Args:
        extent_bounds: Tuple of (min_lon, max_lon, min_lat, max_lat)
    
    Returns:
        Tuple of (figure, axis)
    """
    fig = plt.figure(figsize=(10, 8))
    ax = plt.axes(projection=ccrs.PlateCarree())
    
    # Add map features
    ax.add_feature(cfeature.COASTLINE, linewidth=0.5)
    ax.add_feature(cfeature.BORDERS, linewidth=0.3, linestyle='--')
    ax.add_feature(cfeature.LAND, facecolor='lightgray', alpha=0.5)
    ax.add_feature(cfeature.OCEAN, facecolor='lightblue', alpha=0.3)
    
    # Set extent
    min_lon, max_lon, min_lat, max_lat = extent_bounds
    ax.set_extent([min_lon, max_lon, min_lat, max_lat], crs=ccrs.PlateCarree())
    
    ax.set_xlabel('Longitude')
    ax.set_ylabel('Latitude')
    
    return fig, ax


def plot_density_frame(ax, density_counts, lon_bins, lat_bins, max_log, cell_size, quality_flag, bin_time, besttrack_data):
    """
    Plot a single density frame on the given axis.
    
    Args:
        ax: Matplotlib axis with cartopy projection
        density_counts: 2D array of density counts
        lon_bins: Longitude bin edges
        lat_bins: Latitude bin edges
        max_log: Maximum log value for color scale
        cell_size: Size of each cell in degrees
        quality_flag: Quality flag value
        bin_time: Current bin time
        besttrack_data: Dictionary mapping timestamp to (lat, lon), or None
    
    Returns:
        Tuple of (pcolormesh object, marker object or None)
    """
    # Create grid
    lon_grid, lat_grid = np.meshgrid(lon_bins, lat_bins)
    
    # Apply log10 scale and mask zeros
    density_log = np.log10(density_counts + 1)
    density_log_masked = np.ma.masked_where(density_counts == 0, density_log)
    
    # Plot density
    im = ax.pcolormesh(
        lon_grid, lat_grid, density_log_masked,
        cmap='viridis',
        alpha=0.7,
        transform=ccrs.PlateCarree(),
        shading='flat',
        vmin=0,
        vmax=max_log
    )
    
    # Get hurricane center and add marker if available
    center = get_hurricane_center(bin_time, besttrack_data)
    marker = None
    if center:
        center_lat, center_lon = center
        # Plot hurricane center marker (black X)
        marker_line = ax.plot(
            center_lon, center_lat,
            marker='x',
            markersize=6,
            markeredgecolor='black',
            markeredgewidth=1,
            markerfacecolor='none',  # No fill
            linestyle='None',  # No line connecting points
            transform=ccrs.PlateCarree(),
            zorder=10  # Ensure marker appears on top
        )
        marker = marker_line[0]  # plot() returns a list, get the first element
        title = (f'GLM Lightning Density (Quality Flag = {quality_flag})\n'
                f'Time: {bin_time}\n'
                f'Hurricane Center: ({center_lat:.2f}°, {center_lon:.2f}°)\n'
                f'Cell Size: {cell_size}° x {cell_size}°')
    else:
        title = (f'GLM Lightning Density (Quality Flag = {quality_flag})\n'
                f'Time: {bin_time}\n'
                f'Cell Size: {cell_size}° x {cell_size}°')
    
    ax.set_title(title)
    
    return im, marker


def plot_glm_density_gif(glm_data_path, besttrack_path=None, quality_flag=0, save_path=None, interval=100, fps=10, cell_size=0.1, box_size=10):
    """
    Read GLM data from CSV and create an animated GIF of lightning density plots using Bin Time as frames.
    
    Args:
        glm_data_path: Path to GLM data CSV file
        besttrack_path: Path to besttrack CSV file (optional). If provided, centers view on hurricane.
        quality_flag: Quality flag value to filter for (default: 0)
        save_path: Path to save the GIF (default: None, uses glm_data_path directory)
        interval: Time between frames in milliseconds (default: 100)
        fps: Frames per second for the GIF (default: 10)
        cell_size: Size of each cell in degrees (default: 0.1 for 0.1° x 0.1° cells)
        box_size: Size of box around hurricane center in degrees (default: 10 for ±10°)
    
    Returns:
        Path to saved GIF file
    """
    # Step 1: Load and filter GLM data
    print(f"Reading GLM data from {glm_data_path}...")
    glm_df = pd.read_csv(glm_data_path, parse_dates=['Bin Time'])
    glm_df = filter_glm_data_for_quality(glm_df, quality_flag)
    
    if len(glm_df) == 0:
        print(f"No GLM data found with quality flag {quality_flag}")
        return None
    
    # Step 2: Load besttrack data if provided
    besttrack_data = load_besttrack_data(besttrack_path)
    
    # Step 3: Calculate global bounds
    max_latitude, min_latitude, max_longitude, min_longitude = find_max_min_coords(glm_df)
    global_bounds = (min_latitude, max_latitude, min_longitude, max_longitude)
    
    # Step 4: Get unique bin times
    unique_times = sorted(glm_df['Bin Time'].unique())
    print(f"Creating density GIF with {len(unique_times)} frames...")
    
    # Step 5: Pre-compute all density grids
    density_grids, max_density = precompute_density_grids(
        glm_df, besttrack_data, global_bounds, box_size, cell_size
    )
    
    # Step 6: Calculate max log value for consistent color scale
    max_log = np.log10(max_density + 1) if max_density > 0 else 1
    print(f"Maximum density across all frames: {max_density} (log₁₀: {max_log:.2f})")
    
    # Step 7: Set up the plot with first frame
    first_time = unique_times[0]
    first_density, first_min_lat, first_max_lat, first_min_lon, first_max_lon = density_grids[first_time]
    first_extent = (first_min_lon, first_max_lon, first_min_lat, first_max_lat)
    
    fig, ax = setup_map_plot(first_extent)
    
    # Create initial density plot for first frame
    first_lon_bins = np.arange(first_min_lon, first_max_lon + cell_size, cell_size)
    first_lat_bins = np.arange(first_min_lat, first_max_lat + cell_size, cell_size)
    first_im, first_marker = plot_density_frame(
        ax, first_density, first_lon_bins, first_lat_bins, max_log,
        cell_size, quality_flag, first_time, besttrack_data
    )
    
    # Create colorbar
    cbar = plt.colorbar(first_im, ax=ax, label='Lightning Groups per Cell (log₁₀ scale)')
    
    # Step 8: Create animation function
    # Store references to current pcolormesh and marker for removal
    current_pcolormesh = [first_im]
    current_marker = [first_marker]
    
    def animate_frame(frame_index):
        """Update the plot for a single animation frame."""
        # Remove previous pcolormesh
        if current_pcolormesh[0] is not None:
            current_pcolormesh[0].remove()
        
        # Remove previous marker (if it exists)
        if current_marker[0] is not None:
            current_marker[0].remove()
        
        # Get data for this frame
        current_time = unique_times[frame_index]
        density_counts, frame_min_lat, frame_max_lat, frame_min_lon, frame_max_lon = density_grids[current_time]
        
        # Update extent
        ax.set_extent([frame_min_lon, frame_max_lon, frame_min_lat, frame_max_lat], 
                      crs=ccrs.PlateCarree())
        
        # Create bin edges for this frame
        lon_bins = np.arange(frame_min_lon, frame_max_lon + cell_size, cell_size)
        lat_bins = np.arange(frame_min_lat, frame_max_lat + cell_size, cell_size)
        
        # Plot this frame
        im, marker = plot_density_frame(
            ax, density_counts, lon_bins, lat_bins, max_log,
            cell_size, quality_flag, current_time, besttrack_data
        )
        
        # Store references for next frame
        current_pcolormesh[0] = im
        current_marker[0] = marker
    
    # Step 9: Create and save animation
    anim = animation.FuncAnimation(
        fig, 
        animate_frame, 
        frames=len(unique_times),
        interval=interval,
        repeat=True
    )
    
    # Set save path if not provided
    if save_path is None:
        base_dir = os.path.dirname(glm_data_path)
        save_path = os.path.join(base_dir, 'glm_density_animation.gif')
    
    # Save as GIF
    print(f"Saving density GIF to {save_path}...")
    anim.save(save_path, writer='pillow', fps=fps)
    print(f"Density GIF saved to {save_path}")
    
    plt.close(fig)
    
    return save_path

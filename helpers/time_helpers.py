'''
Helper functions for working with dates.
'''

from datetime import datetime, timedelta

def get_bins_midpoint_times(start_datetime, end_datetime, time_interval):
    """
    Create evenly-spaced datetime bins for full length of a hurricane

    Args:
        start_datetime: Start datetime of hurricane
        end_datetime: End datetime of hurricane
        time_interval: Duration in minutes of each bin
    
    Returns:
        List of bin midpoint datetimes between start and end datetimes
    """
    #list of bin midpoint times (to fill and return)
    bin_times = []

    #We want central times of bins (i.e., 12:15 AM, 12:45 AM, etc. for
    #30-minute bins). This expression finds the first one after start_datetime
    first_bin = start_datetime + timedelta(minutes = ((((time_interval/2) - start_datetime.minute) % time_interval) % time_interval))

    
    #Add times every time_interval minutes until reaching end_datetime
    curr_time = first_bin
    while curr_time < end_datetime:
        bin_times.append(curr_time)
        curr_time += timedelta(minutes = time_interval)

    return bin_times

def get_bins_start_times(start_datetime, end_datetime, time_interval):
    """
    Create start times for evenly-spaced datetime bins for full length of a hurricane.

    Args:
        start_datetime: Start datetime of hurricane
        end_datetime: End datetime of hurricane
        time_interval: Duration in minutes of each bin
    
    Returns:
        List of bin start datetimes (midpoint - time_interval/2)
    """
    midpoint_times = get_bins_midpoint_times(start_datetime, end_datetime, time_interval)
    return [midpoint - timedelta(minutes=time_interval/2) for midpoint in midpoint_times]

def get_bins_end_times(start_datetime, end_datetime, time_interval):
    """
    Create end times for evenly-spaced datetime bins for full length of a hurricane.

    Args:
        start_datetime: Start datetime of hurricane
        end_datetime: End datetime of hurricane
        time_interval: Duration in minutes of each bin
    
    Returns:
        List of bin end datetimes (midpoint + time_interval/2)
    """
    midpoint_times = get_bins_midpoint_times(start_datetime, end_datetime, time_interval)
    return [midpoint + timedelta(minutes=time_interval/2) for midpoint in midpoint_times]

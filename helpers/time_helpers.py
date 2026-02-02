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

def get_list_of_hours_between_dates(start_date, start_hour, end_date, end_hour):
    """
    Get a list of hours between two dates.

    Args:
        start_date: Start date (YYYY-MM-DD)
        start_hour: Start hour (HH)
        end_date: End date (YYYY-MM-DD)
        end_hour: End hour (HH)
    
    Returns:
        List of hours between the start and end dates
    """

    # Convert the start and end times to datetime objects
    start_datetime = datetime.strptime(f"{start_date} {start_hour}", '%Y-%m-%d %H')
    end_datetime = datetime.strptime(f"{end_date} {end_hour}", '%Y-%m-%d %H')

    # Create a list of hours between the start and end times
    # Format: (YYYY, DDD, HH) where DDD is zero-padded day of year
    hours = []
    current_datetime = start_datetime
    while current_datetime <= end_datetime:
        year = str(current_datetime.year)
        day_of_year = str(current_datetime.timetuple().tm_yday).zfill(3)  # Zero-pad to 3 digits
        hour = str(current_datetime.hour).zfill(2)  # Zero-pad to 2 digits
        hours.append((year, day_of_year, hour))
        current_datetime += timedelta(hours=1)
    return hours
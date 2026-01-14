'''
Helper functions for working with dates.
'''

from datetime import datetime, timedelta

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
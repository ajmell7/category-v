import hurdat2parser as hd2
import pandas as pd

class HurdatDataManipulator:
    data = None

    def _get_filtered_tcs(self, region):
        """
        Get filtered tropical cyclones for a region within the year range (2021-2023).
        
        Args:
            region: Region must be either "atl" (Atlantic) or "pac" (Pacific)
        
        Returns:
            List of filtered TropicalCyclone objects
        """
        self.data = hd2.Hurdat2(basin=region)
        filtered_tcs = [tc for tc in self.data.tc.values() if 2021 <= tc.year <= 2023]
        return filtered_tcs

    def create_dataframe(self, region):
        filtered_tcs = self._get_filtered_tcs(region)
        results_atl = []
        for tc in filtered_tcs:
            # Filter only hurricanes (HU reached at any point)
            if "HU" in tc.statuses_reached:
                for e in tc.tc_entries:
                    results_atl.append({
                        "storm_id": tc.atcfid,
                        "name": tc.name,
                        "date": e.date,
                        "year": tc.year,
                        "year": e.date.year,
                        "month": e.date.month,
                        "day": e.date.day,
                        "hour": e.date.hour,
                        "lat": e.lat,
                        "lon": e.lon,
                        "wind": e.wind,          # max sustained wind (kt)
                        "pressure": e.mslp      # min pressure (mb)
                    })
                        
        return pd.DataFrame(results_atl)

    def get_all_hurricanes(self, region):
        """
        Get all hurricanes for a given region (2021-2023).
        
        Args:
            region: Region must be either "atl" (Atlantic) or "pac" (Pacific)
        
        Returns:
            List of tuples: [(name, start_time, end_time), ...]
        """
        filtered_tcs = self._get_filtered_tcs(region)
        hurricanes = []
        for tc in filtered_tcs:
            hurricanes.append((tc.name, tc.start_date, tc.end_date))
        return hurricanes

    def get_hurricane_by_name(self, region, name):
        """
        Get hurricane information by name (2021-2023).
        
        Args:
            region: Region must be either "atl" (Atlantic) or "pac" (Pacific)
            name: Hurricane name (ex. "IAN")
        
        Returns:
            Tuple: (name, start_time, end_time) or None if not found
        """
        filtered_tcs = self._get_filtered_tcs(region)
        for tc in filtered_tcs:
            if tc.name == name:
                return (tc.name, tc.start_date, tc.end_date)
        return None

    def get_hurricane_path(self, name, region):
        """
        Get the path data (lat, lon, time) for a specific hurricane (2021-2023).
        
        Args:
            name: Hurricane name (ex. "IAN")
            region: Region must be either "atl" (Atlantic) or "pac" (Pacific)
        
        Returns:
            pandas.DataFrame with columns: lat, lon, time (date)
            Returns None if hurricane not found
        """
        filtered_tcs = self._get_filtered_tcs(region)
        for tc in filtered_tcs:
            if tc.name == name:
                path_data = []
                for entry in tc.tc_entries:
                    path_data.append({
                        "lat": entry.lat,
                        "lon": entry.lon,
                        "time": entry.date
                    })
                return pd.DataFrame(path_data)
        return None
    
    def get_hurricane_wind_and_pressure(self, name, region):
        """
        Get the wind and pressure data (wind, pressure) for a specific hurricane (2021-2023).
        
        Args:
            name: Hurricane name (ex. "IAN")
            region: Region must be either "atl" (Atlantic) or "pac" (Pacific)
        
        Returns:
            pandas.DataFrame with columns: wind, pressure, time (date)
            Returns None if hurricane not found
        """
        filtered_tcs = self._get_filtered_tcs(region)
        for tc in filtered_tcs:
            if tc.name == name:
                path_data = []
                for entry in tc.tc_entries:
                    path_data.append({
                        "wind": entry.wind,
                        "pressure": entry.mslp,
                        "time": entry.date
                    })
                return pd.DataFrame(path_data)
        return None
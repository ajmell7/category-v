# pip install hurdat2parser
import hurdat2parser as hd2
import pandas as pd

class HurdatDataManipulator:
    data = None

    # region must be either "atl" or "pac"
    def create_dataframe(self, region):
        self.data = hd2.Hurdat2(basin=region)
        results_atl = []
        for tc in self.data.tc.values():

            # Filter by year
            if 2021 <= tc.year <= 2023:

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
    

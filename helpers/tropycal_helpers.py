import tropycal.tracks as tracks
import pandas as pd


def get_storm_list():
    basin = tracks.TrackDataset(basin='both')

    season1 = basin.get_season(2021)
    season2 = basin.get_season(2022)
    season3 = basin.get_season(2023)

    storms_2021 = season1.summary()["name"]
    storms_2022 = season2.summary()["name"]
    storms_2023 = season3.summary()["name"]

    # Create DataFrame with year and storm name columns
    df = pd.concat([
        pd.DataFrame({'year': 2021, 'name': storms_2021}),
        pd.DataFrame({'year': 2022, 'name': storms_2022}),
        pd.DataFrame({'year': 2023, 'name': storms_2023})
    ], ignore_index=True)
    
    return df
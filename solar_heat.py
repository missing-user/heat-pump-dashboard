from datetime import datetime
import pandas as pd
import requests
import io

from joblib import Memory
memory = Memory("cache", verbose=0)

@memory.cache
def fetch_api(lat, lon, direction, start_year, end_year):    
    # API Endpoint
    endpoint = "https://re.jrc.ec.europa.eu/api/v5_2/seriescalc"

    # Parameters
    params = {
        "lat": lat,
        "lon": lon,
        "startyear": start_year,
        "endyear": end_year,
        "components": "0",
        "outputformat": "csv",
        "angle": 90, #inclination angle (tilt)
        "aspect": {"west":90, "east":-90, "south":0}[direction] #azimuth (0 south) (90 west) (-90 east)
    }
    print("Fetching from", endpoint, params)
    response = requests.get(endpoint, params=params)
    return response

def fetch_all(lat, lon, start: datetime, end: datetime) -> pd.Series:
    """
    Get the radiation data from the PVGIS API

    Args:
        lat:
        lon: 
        start: Start datetime
        end: End datetime

    Returns:
        Pandas Series with the radiation data split into components
    """
    # Limit the years to 2020
    start_year = max(2010, min(start.year, 2020))
    end_year = max(2010,min(end.year, 2020))

    if start_year >= end_year:
        start_year = end_year - 1

    df = pd.date_range(start=start, end=end, freq="1h").to_frame(index=True)
            
    for direction in ["south", "east", "west"]:
        response = fetch_api(lat, lon, direction, start_year, end_year)

        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            data = pd.read_csv(io.StringIO(response.content.decode('utf-8')), skiprows=8, skipfooter=11, engine='python')

            data['time'] = pd.to_datetime(data['time'], format='%Y%m%d:%H%M')
            
            for year in df.index.year.unique():
                el_year = data["time"].dt.year[0]
                # Why 10 minutes? IDK. But the timestamps are 00:10:00, 01:10:00, ...
                data["time"] -= pd.Timedelta(days=(el_year - year)*365, minutes=10)

                #data['time'] = pd.to_datetime(data['time'], format='%Y%m%d:%H%M')
                data = data[(data['time'] >= start) & (data['time'] <= end)]
                data.set_index("time", inplace=True)

                #data["G(i)"] = data["Gd(i)"] + data["Gb(i)"] + data["Gr(i)"]
                # Convert W/m2 to kW/m2
                df[f"p_solar {direction} [kW/m2]"] = 1e-3 * data["G(i)"] * 0.9 * 0.6 * 0.9 * 0.7 # Reduction factors from larissas presentation
        else:
            # Handle the case when the request fails
            print(f"Failed to retrieve data. Status code: {response.status_code} {response.reason}")
            return pd.Series()

    return df.drop(columns=0)

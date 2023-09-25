from datetime import datetime
import pandas as pd
import requests
import io

from joblib import Memory
memory = Memory("cache", verbose=0)

@memory.cache
def fetch_api(lat, lon, start_year, end_year):    
    # API Endpoint
    endpoint = "https://re.jrc.ec.europa.eu/api/v5_2/seriescalc"

    # Parameters
    params = {
        "lat": lat,
        "lon": lon,
        "startyear": start_year,
        "endyear": end_year,
        "components": "1",
        "outputformat": "csv"
    }

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


    response = fetch_api(lat, lon, start_year, end_year)

    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        data = pd.read_csv(io.StringIO(response.content.decode('utf-8')), skiprows=8, skipfooter=11, engine='python')

        data['time'] = pd.to_datetime(data['time'], format='%Y%m%d:%H%M')
        
        df = pd.date_range(start=start, end=end, freq="1h", tz="UTC").to_frame(index=False, name="time")
        for year in df["time"].dt.year.unique():
          el_year = data["time"].dt.year[0]
          # Why 10 minutes? IDK. But the timestamps are 00:10:00, 01:10:00, ...
          data["time"] -= pd.Timedelta(days=(el_year - year)*365, minutes=10)
          
          df.update(data.set_index("time"))

        #data['time'] = pd.to_datetime(data['time'], format='%Y%m%d:%H%M')
        data = data[(data['time'] >= start) & (data['time'] <= end)]

        return data.set_index("time")

    else:
        # Handle the case when the request fails
        print(f"Failed to retrieve data. Status code: {response.status_code} {response.reason}")
        return pd.Series()
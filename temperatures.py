# Import Meteostat library and dependencies
from datetime import datetime
from meteostat import Point, Hourly
import requests

import pandas as pd

from joblib import Memory
memory = Memory("cache", verbose=0)

@memory.cache
def geopos_from_zipcode(country_code, zip_code):
  API_KEY = os.environ.get("OPENWEATHER_API_KEY")
  URL = f"https://api.openweathermap.org/geo/1.0/zip?zip={zip_code},{country_code}&appid={API_KEY}"
  response =  requests.get(URL)
  json = response.json()
  if "lat" in json and "lon" in json:
    return json["lat"], json["lon"]
  return None, None

def load_TRY(selection:str):
  """the selection parameter should be one of : ["Wint", "Jahr", "Somm"]"""
  if selection is not None:
    if selection not in ["Wint", "Jahr", "Somm"]:
      raise ValueError("TRY_dataset must be one of ['Wint', 'Jahr', 'Somm']")
   
    filename = f"data/weather/DWD/TRY_488641091042/TRY2045_488641091042_{selection}.dat"
    trydf =  pd.read_csv(filename, delim_whitespace=True, skiprows=34).dropna()
    trydf["year"] = 2045
    trydf["Date"] = pd.to_datetime(dict(year=trydf["year"], month=trydf["MM"], day=trydf["DD"], hour=trydf["HH"]))
    trydf = trydf.rename(columns={"t":"temp [°C]"})
    trydf = trydf.set_index("Date")
    return trydf
  return None

@memory.cache
def fetch_all(country_code, zip_code, start:datetime|str, end:datetime|str):
  
  if not isinstance(start, datetime):
    start = datetime.fromisoformat(start)
  if not isinstance(end, datetime):
    end = datetime.fromisoformat(end)

  lat, lon = geopos_from_zipcode(country_code, zip_code)
  if lat is None or lon is None:
    return pd.DataFrame(columns=["temp [°C]"])
  
  location = Point(lat, lon, 500) # default altitude 500
  data = Hourly(location, start, end)
  return data.fetch().rename(columns={'temp':'temp [°C]'},inplace=False)


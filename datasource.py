import pandas as pd
from datetime import datetime

import temperatures
import co2intensity
import solar_heat

import requests
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

def fetch_all(country_code, zip_code, start, end, TRY_dataset=None):
  tmpdf = co2intensity.load_all()
  
  lat, lon = geopos_from_zipcode(country_code, zip_code)
  
  if isinstance(TRY_dataset, str):
    # TODO: All the years of other data should be shifted to 2045
    df = temperatures.load_TRY(TRY_dataset).rename(columns={"T":"temp [°C]", "G":"solar [W/m2]"})
    delta = df.index[0] - pd.to_datetime(start)
    delta = pd.Timedelta(delta.year, 1, 1)
  else: 
    df = temperatures.fetch_all(lat, lon, start, end)
    df_sol = solar_heat.fetch_all(lat, lon, start, end)
    df["solar [W/m2]"] = df_sol["Gd(i)"]
  df = df.join(tmpdf, how="inner")
  
  return df

if __name__ == "__main__":
  print(fetch_all("DE", 81829, "2020-01-01", "2022-01-02"))
  print(fetch_all("DE", 81829, "2020-01-01", "2022-01-02", "Somm"))
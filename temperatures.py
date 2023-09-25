# Import Meteostat library and dependencies
from datetime import datetime
from meteostat import Point, Hourly
import requests

import pandas as pd

from joblib import Memory
memory = Memory("cache", verbose=0)

@memory.cache
def fetch_all(lat, lon, start:datetime|str, end:datetime|str):
  if not isinstance(start, datetime):
    start = datetime.fromisoformat(start)
  if not isinstance(end, datetime):
    end = datetime.fromisoformat(end)

  if lat is None or lon is None:
    return pd.DataFrame(columns=["T_outside [°C]"])
  
  location = Point(lat, lon, 500) # default altitude 500
  data = Hourly(location, start, end)
  return data.fetch().rename(columns={'temp':'T_outside [°C]'},inplace=False)


# Import Meteostat library and dependencies
from datetime import datetime
from meteostat import Point, Hourly
import requests

import pandas as pd

from joblib import Memory

memory = Memory("cache", verbose=0)


@memory.cache
def fetch_all(lat, lon, start: datetime | str, end: datetime | str):
    if isinstance(start, str):
        start = datetime.fromisoformat(start)

    if isinstance(end, str):
        end = datetime.fromisoformat(end)

    location = Point(lat, lon, 500)  # default altitude 500
    data = Hourly(location, start, end)
    return data.fetch().rename(columns={"temp": "T_outside [°C]"})[["T_outside [°C]"]]

import pandas as pd
from datetime import datetime

import temperatures
import co2intensity

def fetch_all(country_code, zip_code, start, end, TRY_dataset=None):
  tmpdf = co2intensity.load_all()
  
  if isinstance(TRY_dataset,str):
    # TODO: All the years of other data should be shifted to 2045
    df = temperatures.load_TRY(TRY_dataset)
    delta = df.index[0] - pd.to_datetime(start)
    delta = datetime.datetime(delta.year, 1, 1)
  else: 
    df = temperatures.fetch_all(country_code, zip_code, start, end)
  df = df.join(tmpdf, how="inner")
  
  return df

if __name__ == "__main__":
  print(fetch_all("DE", 81829, "2020-01-01", "2022-01-02"))
  print(fetch_all("DE", 81829, "2020-01-01", "2022-01-02", "Somm"))
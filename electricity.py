import pandas as pd
import glob


def list_readable_electricity_profiles():
  return [elm.replace("data/heatingload/electric/synPRO_el_","") for elm in list_electricity_profiles()]

def list_electricity_profiles():
  return glob.glob("data/heatingload/electric/synPRO_el_*.dat")

def load_el_profile(df:pd.DataFrame, path):
  df2 = pd.read_csv(path, comment="#", sep=";").rename(columns={"P_el":"P_el appliances [W]"})
  df2["Date"] = pd.to_datetime(df2["unixtimestamp"])
  df2.set_index("Date")
  print(df2)
  #df.join(df2,how="left")
  return df

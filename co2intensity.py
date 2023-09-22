import pandas as pd

def load_generation_history(filename):
  power_df = pd.read_csv(filename, sep=";", thousands=",", decimal=".")
  hour_deltas = pd.to_datetime(power_df["Start"]).dt.hour.apply(lambda x: pd.Timedelta(hours=x))
  power_df["Date"] = pd.to_datetime(power_df["Date"]) + hour_deltas
  power_df = power_df.drop(columns=["Start", "End"])

  return power_df

def add_intensity_column(power_df, intensity_df):
  intensity_lookup = intensity_df.set_index("Emissions [g CO2eq/kWh]")
  for energy_type in power_df.columns:
    if (intensity_df["Emissions [g CO2eq/kWh]"] == energy_type).any():  
      intensity_name = energy_type.replace("[MWh] Calculated resolutions", "[g CO2eq/kWh]")
      power_df[intensity_name] = power_df[energy_type]*1e3 * intensity_lookup.loc[energy_type, "Med"]
    else:
      print(energy_type)

  power_df["CO2 sum"] = sum([power_df[col] for col in power_df.columns if "[g CO2eq/kWh]" in col])
  power_df["kWh sum"] = sum([power_df[col]*1e3 for col in power_df.columns if "[MWh] Calculated resolutions" in col])
  power_df["Intensity [g CO2eq/kWh]"]=power_df["CO2 sum"] / power_df["kWh sum"]
  return power_df.set_index("Date")

def load_all(generation_path="data/co2intensity/Actual_generation_201801010000_202301012359_Hour.csv",
             intensity_path="data/co2intensity/co2intensities.csv"):
  intensity_df = pd.read_csv(intensity_path, sep=";")
  power_df = load_generation_history(generation_path)
  return add_intensity_column(power_df, intensity_df)

if __name__ == "__main__":
  import plotly.express as px

  power_df = load_all()
  # power_df["Intensity"] is the column of interest

  px.line(power_df, y="Intensity").show()
  px.area(power_df, y=[col for col in power_df.columns if "[g CO2eq/kWh]" in col]).show()
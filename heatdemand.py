import pandas as pd

tab_heat_demand = pd.read_csv("data/heatingload/room_heating/spezifische Heizlast.csv",sep= ";" )

def heat_demand(df, b_type, b_age, t_design, A):
  q_dot_H_design = tab_heat_demand.loc[tab_heat_demand["building_type"]== b_type, b_age].iloc[0] * 1e-3 # kW/m2
  t_lim = tab_heat_demand.loc[tab_heat_demand["building_type"]== "Heizgrenztemperatur [°C]", b_age].iloc[0]
  m = -q_dot_H_design/(abs(t_design)+t_lim)
  c = q_dot_H_design - abs(t_design) * (q_dot_H_design/(abs(t_design)+t_lim))
  t_amb = df["temp [°C]"]
  df['q_dot_H [kW/m2]'] = m*t_amb+c
  df["q_dot_H [kW/m2]"].clip(0,q_dot_H_design,inplace=True)
  df["Q_dot_H [kW]"]=df['q_dot_H [kW/m2]'] * A
  return df

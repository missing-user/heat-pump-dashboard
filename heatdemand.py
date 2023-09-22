import pandas as pd

tab_heat_demand = pd.read_csv("data/heatingload/room_heating/spezifische Heizlast.csv",sep= ";" )

def heat_demand(df, b_type, b_age, t_design, A):
  q_H_design = tab_heat_demand.loc[tab_heat_demand["building_type"]== b_type, b_age].iloc[0]
  t_lim = tab_heat_demand.loc[tab_heat_demand["building_type"]== "Heizgrenztemperatur", b_age].iloc[0]
  m = -q_H_design/(abs(t_design)+t_lim)
  c = q_H_design - abs(t_design) * (q_H_design/(abs(t_design)+t_lim))
  t_amb = df["temp"]
  df['q_H'] = m*t_amb+c
  df["q_H"].clip(0,q_H_design,inplace=True) # W/m^2
  df["Q_H"]=df['q_H']*A*.001 # kW
  return df

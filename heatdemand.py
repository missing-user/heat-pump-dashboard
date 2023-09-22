import pandas as pd
import numpy as np

tab_heat_demand = pd.read_csv("data/heatingload/room_heating/spezifische Heizlast.csv",sep= ";" )

def heat_demand(df, b_type, b_age, t_design, A):
  q_H_design = tab_heat_demand.loc[tab_heat_demand["building_type"]== b_type, b_age].iloc[0]
  t_lim = tab_heat_demand.loc[tab_heat_demand["building_type"]== "Heizgrenztemperatur", b_age].iloc[0]
  m = -q_H_design/(abs(t_design)+t_lim)
  c = q_H_design - abs(t_design) * (q_H_design/(abs(t_design)+t_lim))
  t_amb = df["temp"]
  q_H = m*t_amb+c
  df["q_H"]=np.min(q_H_design,np.max(0,q_H))
  df["Q_H"]=q_H*A
  return df
print(heat_demand(0,"single_family_house", "1969-73",0))

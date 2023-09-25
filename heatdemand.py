import pandas as pd
import numpy as np

tab_heat_demand = pd.read_csv("data/heatingload/room_heating/spezifische Heizlast.csv",sep= ";" )

def heat_pump_size(b_type, b_age, A):
  q_dot_H_design = tab_heat_demand.loc[tab_heat_demand["building_type"]== b_type, b_age].iloc[0] * 1e-3 #W to kW
  Q_dot_H_design = q_dot_H_design * A
  return Q_dot_H_design

def heat_demand(df, b_type, b_age, t_design, A):
  Q_dot_H_design = heat_pump_size(b_type, b_age, A)
  q_dot_H_design = Q_dot_H_design/A
  t_lim = tab_heat_demand.loc[tab_heat_demand["building_type"]== "Heizgrenztemperatur", b_age].iloc[0]
  m = -q_dot_H_design/(abs(t_design)+t_lim)
  c = q_dot_H_design - abs(t_design) * (q_dot_H_design/(abs(t_design)+t_lim))
  t_amb = df["temp [°C]"]
  df['q_dot_H [kW/m2]'] = m*t_amb+c
  df["q_dot_H [kW/m2]"].clip(0,q_dot_H_design,inplace=True)
  df["Q_dot_H [kW]"]=df['q_dot_H [kW/m2]'] * A
  return df


def get_heatpump_Q_dot(t_current, t_target, Q_dot_H_design):
   if t_current <= t_target:
      return Q_dot_H_design
   return 0.0


def simulate_np(P_el_appliances:np.ndarray, temp:np.ndarray, 
                Q_dot_H_design:float, t_target:float, 
                UA:float, C:float):
  timestep = 3600 # h

  Q_dot_loss = np.zeros_like(temp)
  Q_dot_H = np.zeros_like(temp)
  Q_H = np.zeros_like(temp)
  Q_H[0] = t_target

  for i in range(len(temp)-1):
      T_inside = Q_H[i]/C
      T_outside = temp[i]
      Q_dot = Q_dot_loss[i] = (T_outside - T_inside)*UA
      Q_dot += P_el_appliances[i]*1e-3 # appliances
      Q_dot_H[i] = get_heatpump_Q_dot(T_inside, t_target, max(0,min(-Q_dot, Q_dot_H_design)))

      Q_dot += Q_dot_H[i] # heat pump
      Q_H[i+1] = Q_H[i] + Q_dot*timestep
  return Q_H, Q_dot_loss, Q_dot_H

def simulate(df, b_type, b_age, A, t_target=20.0):
  Q_dot_H_design = heat_pump_size(b_type, b_age, A)

  UA = 582e-3   # kW/K
  C = 328000    # kJ/K

  Q_H, Q_dot_loss, Q_dot_H = simulate_np(df["P_el appliances [W]"].to_numpy(), 
                                         df["temp [°C]"].to_numpy(), 
                                         Q_dot_H_design, t_target, UA, C)
  df["Q_H [kJ]"] = Q_H
  df["Q_dot_loss [kW]"] = Q_dot_loss
  df["Q_dot_H [kW]"] = Q_dot_H


  df["T_house [°C]"] = df["Q_H [kJ]"]/C # kJ to °C
  return df

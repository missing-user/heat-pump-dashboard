import pandas as pd

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
   return 0

def simulate(df, b_type, b_age, A, t_target=20):
  Q_dot_H_design = heat_pump_size(b_type, b_age, A)
  
  UA = 582e-3   # kW/K
  C = 328000    # kJ/K
  timestep = 3600 # h

  df["Q_H [kJ]"] = t_target * C # 15°C to kJ
  df["Q_dot_loss [kW]"] = 0.0
  df["Q_dot_H [kW]"] = 0.0
  for i in range(len(df)-1):
      T_inside = df["Q_H [kJ]"].iloc[i]/C
      T_outside = df["temp [°C]"].iloc[i]
      df["Q_dot_loss [kW]"].iloc[i] = Q_dot = (T_outside - T_inside)*UA # kW
      #Q_dot += 100 # 100W heating for each habitant
      Q_dot += df["P_el appliances [W]"].iloc[i]*1e-3 # appliances

      df["Q_dot_H [kW]"].iloc[i] = get_heatpump_Q_dot(T_inside, t_target, max(0,min(-Q_dot, Q_dot_H_design)))
      Q_dot += df["Q_dot_H [kW]"].iloc[i] # heat pump

      df["Q_H [kJ]"].iloc[i+1] = df["Q_H [kJ]"].iloc[i] + Q_dot*timestep

  df["T_house [°C]"] = df["Q_H [kJ]"]/C # kJ to °C
  return df
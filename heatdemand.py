import pandas as pd
import numpy as np

tab_heat_demand = pd.read_csv("data/heatingload/room_heating/spezifische Heizlast.csv",sep= ";" )
uwerte = pd.read_csv("data/heatingload/room_heating/Uwerte.csv",sep=";").set_index("building_year")
gwerte = pd.read_csv("data/heatingload/room_heating/Gwerte.csv").set_index("Gebaeude Alter")
cwerte = pd.read_csv("data/heatingload/room_heating/Cwerte.csv").set_index("Gebaeude Alter")

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
  t_amb = df["T_outside [°C]"]
  df['q_dot_H [kW/m2]'] = m*t_amb+c
  df["q_dot_H [kW/m2]"].clip(0,q_dot_H_design,inplace=True)
  df["Q_dot_H [kW]"]=df['q_dot_H [kW/m2]'] * A
  return df


def get_heatpump_Q_dot(t_current, t_target, Q_dot_H_design):
   if t_current <= t_target:
      return Q_dot_H_design
   return 0.0


def simulate_np(P_internal:np.ndarray, T_outside_series:np.ndarray,
                ventilation:np.ndarray, intensity_series:np.ndarray,
                Q_dot_H_design:float, t_target:float, 
                UA:float, C:float):
  timestep = 3600.0 # h

  Q_dot_loss = np.zeros_like(T_outside_series)
  Q_dot_ventilation = np.zeros_like(T_outside_series)
  Q_dot_H = np.zeros_like(T_outside_series)
  Q_H = np.zeros_like(T_outside_series)
  Q_H[0] = t_target*C # initial temperature

  for i in range(len(T_outside_series)-1):
      T_inside = Q_H[i]/C
      T_outside = T_outside_series[i]
      
      Q_dot = Q_dot_loss[i] = (T_outside - T_inside)*UA
      
      Q_dot_ventilation[i] = (T_outside - T_inside)*ventilation[i]
      Q_dot += Q_dot_ventilation[i] # ventilation (already has a negative sign)
      
      Q_dot += P_internal[i] # appliances

      if T_inside <= t_target:
        if intensity_series[i] < 500:
          pass  #TODO: dynamic threshold for optimal CO2 usage
        Q_dot_H[i] = max(0,min(-Q_dot, Q_dot_H_design))

      Q_dot += Q_dot_H[i] # heat pump
      Q_H[i+1] = Q_H[i] + Q_dot*timestep
  return Q_H, Q_dot_loss, Q_dot_ventilation, Q_dot_H

def ventilation(b_type, volume):
  c_spec_air = 1.006 # kJ/kgK
  air_density = 1.2 # kg/m3
  c_air = c_spec_air * air_density # kJ/m3K

  return 0.5 * volume * c_air / 3600.0 # kJ/sK

def calc_U(b_age, A_windows, A, n_floors, h_floor=3):
    basement = A/n_floors
    roof= A/n_floors
    A_outsidewall = np.square(A/n_floors)*h_floor*n_floors*4

    if(b_age=="KfW 70" or b_age=="KfW 40"):
        U = (A_outsidewall + basement + roof) * uwerte.loc[b_age, "overall [W/m2K]"]  # W/K
    else:
        U = (((A_outsidewall-A_windows) * uwerte.loc[b_age,"outside wall [W/m2K]"])+
             (roof * uwerte.loc[b_age,"roof [W/m2K]"])+
             (basement* uwerte.loc[b_age,"basement [W/m2K]"])+
             (A_windows* uwerte.loc[b_age,"windows [W/m2K]"])) #W/K

    return U

def simulate(df, b_type, b_age, A, A_windows, n_floors=2, t_target=20.0, assumptions=[]):
  Q_dot_H_design = heat_pump_size(b_type, b_age, A)
  U = calc_U(b_age, A_windows, A, n_floors)
  specific_heat_capa = cwerte.loc[b_age, "Heatcapacity [kJ/m3K]"]

  volume = A * 3.0 # m3
  #specific_heat_capa = 546.66 # Ullis Wert kJ/m3K
  C = volume*specific_heat_capa    # kJ/K

  # Heat transfer coefficient through walls etc.
  UA = A*U # UA = 582e-3   # kW/K
  
  if "Ventilation heat losses" in assumptions:
    ventilation_series = np.full_like(df["T_outside [°C]"], ventilation(b_type, volume))
  else:
    ventilation_series = np.zeros_like(df["T_outside [°C]"])

  df["P_solar [kW]"] = float(A_windows)/4 *(df["p_solar south [kW/m2]"]+df["p_solar east [kW/m2]"]+df["p_solar west [kW/m2]"])
  df["Q_dot_solar [kW]"] = df["P_solar [kW]"] * gwerte.loc[b_age, "G-Wert [-]"] # Less heat passes through newer windows
  
  # Simulate closing the blinds when it is hot outside
  if "Close window blinds in summer" in assumptions:
    df.loc[df["T_outside [°C]"] > t_target,"Q_dot_solar [kW]"] *= 0.1

  P_internal = (df["P_el appliances [kW]"] + df["Q_dot_solar [kW]"]).to_numpy()

  Q_H, Q_dot_loss, Q_dot_vent, Q_dot_H = simulate_np(P_internal, 
                                         df["T_outside [°C]"].to_numpy(),
                                         ventilation_series, 
                                         Q_dot_H_design, t_target, UA, C)
  df["Q_H [kJ]"] = Q_H
  df["Q_dot_loss [kW]"] = Q_dot_loss
  df["Q_dot_ventilation [kW]"] = Q_dot_vent
  df["Q_dot_H [kW]"] = Q_dot_H

  df["T_house [°C]"] = df["Q_H [kJ]"]/C # kJ to °C
  return df

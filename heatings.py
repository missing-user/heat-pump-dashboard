import numpy as np

def compute_cop(df,model, t_vl=35.):
    df.loc[:, 'COP heatpump'] = np.nan
    if model == 'Carnot':
        df = cop_carnot(df, t_vl)
    elif model == 'soph':
        df.loc[:, 'COP heatpump'] = 1
    return df

def cop_carnot(df, t_vl, degradation_coeff=.5):
    df.loc[:, 'COP heatpump'] = degradation_coeff * (273.15 + t_vl) / (t_vl - df.loc[:, 'T_outside [°C]'])
    return df

def compute_P_electrical(df):
    df.loc[:, 'P_el heat pump [kW]'] = df.loc[:, 'Q_dot_H [kW]'] / df.loc[:, 'COP heatpump']
    df.loc[df['Q_dot_H [kW]'] == 0, 'COP heatpump'] = np.nan
    df["heat pump emissions [kg CO2eq]"] = df["P_el heat pump [kW]"] * df["Intensity [g CO2eq/kWh]"] * 1e-3
    return df

def gas_heating(df):
    # constants for gas heating
    intensity = 200.8 # [g CO2/kWh] primary energy
    eta = .95

    # compute power demand and emissions
    df.loc[:, 'Gas heating emissions [kg CO2eq]'] = df.loc[:,'Q_dot_H [kW]'] / eta * intensity * 1e-3
    return df

def oil_heating(df):
    # constants for oil heating
    intensity = 266.5 # [g CO2/kWh] primary energy
    eta = .95

    # compute power demand and emissions
    df.loc[:, 'Oil heating emissions [kg CO2eq]'] = df.loc[:,'Q_dot_H [kW]'] / eta * intensity * 1e-3
    return df

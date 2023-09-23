import numpy as np

def compute_cop(df,model):
    df.loc[:, 'COP heatpump'] = np.nan
    if model == 'Carnot':
        df = cop_carnot(df)
    elif model == 'soph':
        df.loc[:, 'COP heatpump'] = 1
    return df

def cop_carnot(df, t_vl=35., degradation_coeff=.5):
    df.loc[:, 'COP heatpump'] = degradation_coeff * (273.15 + t_vl) / (t_vl - df.loc[:, 'temp [°C]'])
    return df

def compute_P_electrical(df):
    df.loc[:, 'P_el heat pump [kW]'] = df.loc[:, 'Q_dot_H [kW]'] / df.loc[:, 'COP heatpump']
    df.loc[df['Q_dot_H [kW]'] == 0, 'COP heatpump'] = np.nan
    return df


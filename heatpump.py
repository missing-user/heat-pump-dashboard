import numpy as np

def compute_cop(df,model):
    df.loc[:, 'COP'] = np.nan
    if model == 'Carnot':
        df = cop_carnot(df)
    elif model == 'soph':
        df.loc[:, 'COP'] = 1
    return df

def cop_carnot(df, t_vl=35., degradation_coeff=.5):
    df.loc[:, 'COP'] = degradation_coeff * (273.15 + t_vl) / (t_vl - df.loc[:, 'temp'])
    return df

def compute_P_electrical(df):
    df.loc[:, 'P_el'] = df.loc[:, 'Q_H'] / df.loc[:, 'COP']
    df.loc[df['Q_H'] == 0, 'COP'] = np.nan
    return df


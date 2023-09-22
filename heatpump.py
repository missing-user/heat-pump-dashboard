import pandas as pd
import numpy as np
def cop_carnot(df, t_vl=35., degradation_coeff=.5):
    df.loc[:, 'COP'] = degradation_coeff * (273.15 + t_vl) / (t_vl - df.loc[:, 'temp'])
    return df

def compute_P_electrical(df):
    df.loc[:, 'P_el'] = df.loc[:, 'Q_htg_avg'] / df.loc[:, 'COP']
    df.loc[df['Q_htg_avg'] == 0, 'COP'] = np.nan
    return df


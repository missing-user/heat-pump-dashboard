import numpy as np
import pandas as pd

def gas_heating(df):
    # constants for gas heating
    intensity = 200.8 # [g CO2/kWh] primary energy
    cop = .95

    # compute power demand and emissions
    df.loc[:, 'Gas demand [kWh]'] = df.loc[:,'Q_H'] / cop
    df.loc[:,'Gas heating emissions [g CO2eq'] = df.loc[:, 'Gas demand [kWh]'] * intensity
    return df

def oil_heating(df):
    # constants for oil heating
    intensity = 266.5 # [g CO2/kWh] primary energy
    cop = .85

    # compute power demand and emissions
    df.loc[:, 'Oil demand [kWh]'] = df.loc[:,'Q_H'] / cop
    df.loc[:, 'Oil heating emissions [g CO2eq'] = df.loc[:, 'Gas demand [kWh]'] * intensity
    return df

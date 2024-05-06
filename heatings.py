import numpy as np
import pandas as pd
import hplib as hpl
import hplib_database as hpd
import time
from scipy.interpolate import interp1d

t_vorlauf_conventional = pd.read_csv(
    "data/heatingload/room_heating/t_vorlauf_conventional.csv"
)
t_vorlauf_floor = pd.read_csv(
    "data/heatingload/room_heating/t_vorlauf_floorheating.csv"
)


def compute_cop(df, model, t_vl=35.0):
    df.loc[:, "COP heatpump"] = np.nan
    if model == "Carnot":
        df = cop_carnot(df, t_vl)
        # df = compute_P_electrical(df)
    elif model == "soph":
        df.loc[:, "COP heatpump"] = 1
        # df = compute_P_electrical(df)
    else:
        df = simulate_hp(df)
    return df


def cop_carnot(df, degradation_coeff=0.5):
    result_df = pd.DataFrame()
    result_df["COP heatpump"] = (
        degradation_coeff
        * (273.15 + df.loc[:, "T_vorlauf [°C]"])
        / (df.loc[:, "T_vorlauf [°C]"] - df.loc[:, "T_outside [°C]"])
    )
    return result_df


def compute_P_electrical(df):
    df.loc[:, "P_el heat pump [kW]"] = (
        df.loc[:, "Q_dot_H [kW]"] / df.loc[:, "COP heatpump"]
    )
    df.loc[df["Q_dot_H [kW]"] == 0, "COP heatpump"] = np.nan
    df["heat pump emissions [kg CO2eq]"] = (
        df["P_el heat pump [kW]"] * df["Intensity [g CO2eq/kWh]"] * 1e-3
    )
    return df


def gas_heating(df):
    # constants for gas heating
    intensity = 200.8  # [g CO2/kWh] primary energy
    eta = 0.95

    # compute power demand and emissions
    df.loc[:, "Gas heating emissions [kg CO2eq]"] = (
        df.loc[:, "Q_dot_demand [kW]"] / eta * intensity * 1e-3
    )
    return df


def oil_heating(df):
    # constants for oil heating
    intensity = 266.5  # [g CO2/kWh] primary energy
    eta = 0.95

    # compute power demand and emissions
    df.loc[:, "Oil heating emissions [kg CO2eq]"] = (
        df.loc[:, "Q_dot_demand [kW]"] / eta * intensity * 1e-3
    )
    return df


def pellet_heating(df):
    # constants for oil heating
    intensity = 36  # [g CO2/kWh] primary energy
    eta = 0.95

    # compute power demand and emissions
    df.loc[:, "Pellet heating emissions [kg CO2eq]"] = (
        df.loc[:, "Q_dot_demand [kW]"] / eta * intensity * 1e-3
    )
    return df


def simulate_hp_inverse(df, model="Bosch Compress 3000 AWS-8 B"):
    # Create heat pump object with parameters
    parameters = hpl.get_parameters(model=model)
    heatpump = hpl.HeatPump(parameters)

    # generate lookup table for heatpump library
    t_amb_min = df["t_outside [°C]"].min()
    t_amb_max = df["t_outside [°C]"].max()
    t_amb = np.arange(t_amb_min, t_amb_max + 1.0)
    t_amb = np.unique(df["T_outside [°C]"].values)
    t_amb.sort()
    t_in_secondary = np.arange(25, 85)
    t_in_secondary_length = len(t_in_secondary)
    t_ambs = []
    t_secondarys = []
    for t in t_amb:
        t_ambs.extend([t] * t_in_secondary_length)
        t_secondarys.extend(t_in_secondary)
    df_lookup = pd.DataFrame({"T_amb": t_ambs, "T_in_secondary [°C]": t_secondarys})

    # calculate/simulate with values from lookuptable
    start = time.time()
    results = heatpump.simulate(
        t_in_primary=df_lookup["T_amb"].values,
        t_in_secondary=df_lookup["T_in_secondary [°C]"].values,
        t_amb=df_lookup["T_amb"].values,
        mode=1,
    )
    # TODO:
    #  pick best t_vl/P_el/Q_h
    #  add values to DataFrame
    results_lookup = pd.DataFrame(results)
    end = time.time()
    calc_time = end - start
    results_lookup.loc[:, "COP Carnot"] = (
        0.4
        * (273.15 + results_lookup["T_out"])
        / (results_lookup["T_out"] - results_lookup["T_in"])
    )
    results_lookup.loc[:, "P_th"] = results_lookup.loc[:, "P_th"] * 1e-3
    results_lookup.loc[:, "P_el"] = results_lookup.loc[:, "P_el"] * 1e-3

    for iter, row in df[["Q_dot_H [kW]", "T_outside [°C]"]].iterrows():
        temp_df = results_lookup[results_lookup["T_amb"] == row["T_outside [°C]"]]
        interpolation_function = interp1d(
            temp_df["P_th"].values, temp_df["COP"].values, kind="linear"
        )
        new_COP = interpolation_function(row["Q_dot_H [kW]"])
        pass

    df.loc[:, "P_el heat pump [kW]"] = np.nan
    df.loc[:, "Q_dot_heatpump [kW]"] = np.nan
    df.loc[:, "COP heatpump"] = np.nan
    return df


def simulate_hp(df, model, system, age):
    # Create heat pump object with parameters
    parameters = hpl.get_parameters(model=model)
    heatpump = hpl.HeatPump(parameters)

    if system == "Floor heating":
        # pick floor heating vorlauf temperatures
        t_vorlauf = t_vorlauf_floor
    else:
        t_vorlauf = t_vorlauf_conventional[
            t_vorlauf_conventional["building_year"] == age
        ]

    vorlauf_interpfunc = interp1d(
        t_vorlauf["t_amb [°C]"], t_vorlauf["t_vl [°C]"], kind="linear"
    )

    df["T_vorlauf [°C]"] = vorlauf_interpfunc(df["T_outside [°C]"])
    df["T_in_secondary [°C]"] = df["T_vorlauf [°C]"] - 5.0

    if model != "Carnot":
        results = heatpump.simulate(
            t_in_primary=df["T_outside [°C]"].values,
            t_in_secondary=df["T_in_secondary [°C]"].values,
            t_amb=df["T_outside [°C]"].values,
            mode=1,
        )
        results_df = pd.DataFrame(results)
        df.loc[:, "COP heatpump"] = results_df["COP"].values
        df.loc[:, "P_el heat pump [kW]"] = results_df["P_el"].values * 1e-3
        df.loc[:, "Q_dot_supplied [kW]"] = results_df["P_th"].values * 1e-3
    else:
        results_df = cop_carnot(df, degradation_coeff=0.4)
        df["COP heatpump"] = results_df["COP heatpump"]
        df["P_el heat pump [kW]"] = 3
        df["Q_dot_supplied [kW]"] = 9

    return df


if __name__ == "__main__":
    simulate_hp(pd.read_csv("test_data.csv"), model="Bosch Compress 3000 AWS-8 B")

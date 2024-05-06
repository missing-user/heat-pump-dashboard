import pandas as pd
import glob
import datetime


def list_readable_electricity_profiles():
    return [
        elm.replace("data/heatingload/electric/synPRO_el_", "")[:-4]
        for elm in list_electricity_profiles()
    ]


def list_electricity_profiles():
    return glob.glob("data/heatingload/electric/synPRO_el_*.dat")


name_to_file = {
    path.replace("data/heatingload/electric/synPRO_el_", "")[:-4]: path
    for path in glob.glob("data/heatingload/electric/synPRO_el_*.dat")
}


def load_el_profile(df: pd.DataFrame, path):
    df_el = (
        pd.read_csv(path, comment="#", sep=";")
        .rename(columns={"P_el": "P_el appliances [kW]"})
        .drop(columns=["YYYYMMDD", "hhmmss"])
    )
    df_el["unixtimestamp"] = pd.to_datetime(
        df_el["unixtimestamp"], unit="s"
    ) + datetime.timedelta(hours=1)
    df_el["P_el appliances [kW]"] *= 1e-3

    df["P_el appliances [kW]"] = 0.0

    for year in df.index.year.unique():
        el_year = df_el["unixtimestamp"].dt.year[0]
        df_el["unixtimestamp"] -= pd.Timedelta(days=(el_year - year) * 365)

        df.update(df_el.set_index("unixtimestamp"))

    df["P_el appliances [kW]"] *= 0.95  # larissas presentation
    return df

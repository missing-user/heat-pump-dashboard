import pandas as pd
import numpy as np
import heatings
import scipy

tab_heat_demand = pd.read_csv(
    "data/heatingload/room_heating/spezifische Heizlast.csv", sep=";"
)
uwerte = pd.read_csv("data/heatingload/room_heating/Uwerte.csv").set_index(
    "building_year"
)
gwerte = pd.read_csv("data/heatingload/room_heating/Gwerte.csv").set_index(
    "building_year"
)
cwerte = pd.read_csv("data/heatingload/room_heating/Cwerte.csv").set_index(
    "building_year"
)


def heat_pump_size(b_type, b_age, A):
    q_dot_H_design = (
        tab_heat_demand.loc[tab_heat_demand["building_type"] == b_type, b_age].iloc[0]
        * 1e-3
    )  # W to kW
    Q_dot_H_design = q_dot_H_design * A
    return Q_dot_H_design


def get_heatpump_Q_dot(t_current, t_target, Q_dot_H_design):
    if t_current <= t_target:
        return Q_dot_H_design
    return 0.0


def simulate_np(
    P_internal: np.ndarray,
    T_outside_series: np.ndarray,
    ventilation: np.ndarray,
    intensity_series: np.ndarray,
    Q_dot_supplied: np.ndarray,
    t_target: float,
    t_range: float,
    UA: float,
    C: float,
    controller: str,
):
    timestep = 3600.0  # h

    Q_dot_loss = np.zeros_like(T_outside_series)
    Q_dot_ventilation = np.zeros_like(T_outside_series)
    Q_dot_transferred = np.zeros_like(T_outside_series)
    Q_dot_demand = np.zeros_like(T_outside_series)
    Q_dot_ideal = np.zeros_like(T_outside_series)
    T_inside_ideal = np.zeros_like(T_outside_series)
    Q_H = np.zeros_like(T_outside_series)
    Q_H_idealized = np.zeros_like(T_outside_series)

    Q_H[0] = t_target * C  # initial temperature
    Q_H_idealized[0] = t_target * C
    heating = False

    uncertainty = controller == r"CO2-aware controller with 10% forecast uncertainty"
    T_outside_forecast = T_outside_series * np.random.uniform(
        0.9, 1.1, len(T_outside_series)
    )

    for i in range(len(T_outside_series) - 1):
        T_inside = Q_H[i] / C
        T_inside_ideal[i] = Q_H_idealized[i] / C
        T_outside = T_outside_series[i]

        Q_dot = Q_dot_loss[i] = (T_outside - T_inside) * UA  # losses through wall&roof
        Q_dot_ventilation[i] = (T_outside - T_inside) * ventilation[
            i
        ]  # ventilation losses
        Q_dot += Q_dot_ventilation[i]  # ventilation (already has a negative sign)
        Q_dot += P_internal[i]  # appliances & humans
        Q_dot_transferred[i] = Q_dot

        # heat demand calculation
        Q_dot_ideal[i] = (T_outside - T_inside_ideal[i]) * (
            UA + ventilation[i]
        ) + P_internal[i]
        Q_dot_demand[i] = -Q_dot_ideal[
            i
        ]  # Wärmebedarf nach DIN ISO leck mich (idealisiert)
        Q_dot_demand[i] = max(0, Q_dot_demand[i])  # filter out heat inflow
        if T_inside_ideal[i] < t_target:
            Q_dot_ideal[i] = max(0, Q_dot_ideal[i])
        else:
            Q_dot_demand[i] = 0.0

        # co2 controller #   #   #   #   #   #   #   #   #   #   #
        if (
            controller == "CO2-aware controller"
            or controller == r"CO2-aware controller with 10% forecast uncertainty"
        ):
            # Required heat for the coming time period
            predicted_heat_demand = C * (t_target - T_inside) / 3600.0
            max_heat = C * (t_range) / 3600.0
            min_heat = C * (-t_range) / 3600.0

            # How long to choose the optimization period?
            for t in range(3 * 24):  # Max optimization range 4 days
                future_t = i + t
                if future_t >= len(T_outside_forecast):
                    break

                heat_loss_now = (t_target - T_outside_forecast[future_t]) * (
                    UA + ventilation[future_t]
                ) - P_internal[future_t]

                period = t
                if (
                    predicted_heat_demand + heat_loss_now < min_heat
                    or predicted_heat_demand + heat_loss_now > max_heat
                ):
                    break
                predicted_heat_demand += heat_loss_now

            period = max(1, period)  # at least 1 hour
            future_t = i + period

            # Find the best time to heat

            if uncertainty:
                intensity_prediction = intensity_series[i:future_t] * np.random.uniform(
                    0.9, 1.1, period
                )
                Q_dot_prediction = Q_dot_supplied[i:future_t] * np.random.uniform(
                    0.9, 1.1, period
                )
            else:
                intensity_prediction = intensity_series[i:future_t]
                Q_dot_prediction = Q_dot_supplied[i:future_t]
            best_times = np.argsort(intensity_prediction)
            predicted_Q_heating = np.cumsum(Q_dot_prediction[best_times])

            # If the predicted heat demand is higher than the predicted heat supply, heat
            now_idx = np.where(best_times == 0)[0][0]
            if predicted_Q_heating[now_idx] >= predicted_heat_demand:
                Q_dot_supplied[i] = 0.0
        # simple controller #   #   #   #   #   #   #   #   #   #   #
        else:
            if T_inside > t_target + t_range or not heating:
                heating = False
            if T_inside < t_target - t_range or heating:
                heating = True
            if not heating:
                Q_dot_supplied[i] = 0.0

        Q_dot += Q_dot_supplied[i]

        # explicit euler integration
        Q_H_idealized[i + 1] = Q_H_idealized[i] + Q_dot_ideal[i] * timestep
        Q_H[i + 1] = Q_H[i] + Q_dot * timestep
    return (
        Q_H,
        Q_dot_loss,
        Q_dot_ventilation,
        Q_dot_supplied,
        Q_dot_transferred,
        Q_dot_demand,
        Q_dot_ideal,
        T_inside_ideal,
    )


def ventilation(b_type, volume):
    c_spec_air = 1.006  # kJ/kgK
    air_density = 1.2  # kg/m3
    c_air = c_spec_air * air_density  # kJ/m3K

    return 0.5 * volume * c_air / 3600.0  # kJ/sK


def calc_U(b_type, b_age, A_windows, A, n_floors, h_floor=3.0):
    A_basement = A / n_floors
    A_roof = A / n_floors
    A_outsidewall = np.sqrt(A / n_floors) * h_floor * n_floors * 4

    if b_type == "tarreced_house":
        A_outsidewall *= 0.5
    elif b_type == "terraced_house (end)":
        A_outsidewall *= 0.75  # 3 walls exposed, 1 wall shared
    elif (
        b_type == "appartment_building < 8 AP" or b_type == "appartment_building > 8 AP"
    ):
        A_outsidewall *= 0.5  # 2 walls exposed, 2 walls shared
        if b_type == "appartment_building < 8 AP":
            A_roof *= 0.5
            A_basement *= 0.5
        else:
            A_roof *= 0.2
            A_basement *= 0.2
    A_outsidewall = max(
        A_outsidewall, A_windows
    )  # We cannot have more windows than wall surface

    if b_age == "KfW 70" or b_age == "KfW 40":
        UA = (A_outsidewall + A_basement + A_roof) * uwerte.loc[
            b_age, "overall [kW/m2K]"
        ]  # W/K
    else:
        UA = (
            ((A_outsidewall - A_windows) * uwerte.loc[b_age, "outside wall [kW/m2K]"])
            + (A_roof * uwerte.loc[b_age, "roof [kW/m2K]"])
            + (A_basement * uwerte.loc[b_age, "basement [kW/m2K]"])
            + (A_windows * uwerte.loc[b_age, "windows [kW/m2K]"])
        )  # W/K

    UA *= 1e-3
    return UA


def simulate(
    df,
    hp_type,
    b_type,
    b_age,
    A,
    A_windows,
    n_floors=2,
    t_target=20.0,
    t_range=1.0,
    assumptions=[],
):
    UA = calc_U(b_type, b_age, A_windows, A, n_floors)
    specific_heat_capa = cwerte.loc[b_age, "Heatcapacity [kJ/m3K]"]

    volume = A * 3.0  # m3
    # specific_heat_capa = 546.66 # Ullis Wert kJ/m3K
    C = volume * specific_heat_capa  # kJ/K

    if "Ventilation heat losses" in assumptions:
        ventilation_series = np.full_like(
            df["T_outside [°C]"], ventilation(b_type, volume)
        )
    else:
        ventilation_series = np.zeros_like(df["T_outside [°C]"])

    controller = "default"
    if "CO2-aware controller" in assumptions:
        controller = "CO2-aware controller"
        if r"10% forecast uncertainty" in assumptions:
            controller += r" with 10% forecast uncertainty"

    heating_system = "conventional"
    if "Floor heating" in assumptions:
        heating_system = "Floor heating"

    df["P_solar [kW]"] = (
        float(A_windows)
        / 4
        * (
            df["p_solar south [kW/m2]"]
            + df["p_solar east [kW/m2]"]
            + df["p_solar west [kW/m2]"]
        )
    )
    df["Q_dot_solar [kW]"] = (
        df["P_solar [kW]"] * gwerte.loc[b_age, "G-Wert [-]"]
    )  # Less heat passes through newer windows

    # Simulate closing the blinds when it is hot outside
    if "Close window blinds in summer" in assumptions:
        df.loc[df["T_outside [°C]"] > t_target, "Q_dot_solar [kW]"] *= 0.1

    P_internal = (df["P_el appliances [kW]"] + df["Q_dot_solar [kW]"]).to_numpy()
    df = heatings.simulate_hp(df, model=hp_type, system=heating_system, age=b_age)

    df["Intensity per heat [g CO2eq/kWh]"] = (
        df["Intensity [g CO2eq/kWh]"] / df["COP heatpump"]
    )

    (
        Q_H,
        Q_dot_loss,
        Q_dot_vent,
        Q_dot_supplied,
        Q_dot_transferred,
        Q_dot_demand,
        Q_dot_idealized,
        T_inside_ideal,
    ) = simulate_np(
        P_internal,
        df["T_outside [°C]"].to_numpy(),
        ventilation_series,
        df["Intensity per heat [g CO2eq/kWh]"].to_numpy(),
        df["Q_dot_supplied [kW]"].to_numpy(),
        t_target,
        t_range,
        UA,
        C,
        controller,
    )
    df["Q_H [kJ]"] = Q_H
    df["Q_dot_loss [kW]"] = Q_dot_loss
    df["Q_dot_ventilation [kW]"] = Q_dot_vent
    df["Q_dot_supplied [kW]"] = Q_dot_supplied
    df["Q_dot_transferred [kW]"] = Q_dot_transferred
    df["Q_dot_demand [kW]"] = Q_dot_demand
    df["Q_dot_idealized [kW]"] = Q_dot_idealized
    df["T_inside_ideal [°C]"] = T_inside_ideal

    df.loc[df.loc[:, "Q_dot_supplied [kW]"] == 0, "COP heatpump"] = np.nan
    df.loc[df.loc[:, "Q_dot_supplied [kW]"] == 0, "P_el heat pump [kW]"] = 0.0
    df["heat pump emissions [kg CO2eq]"] = (
        df["P_el heat pump [kW]"] * df["Intensity [g CO2eq/kWh]"] * 1e-3
    )

    df["T_house [°C]"] = df["Q_H [kJ]"] / C  # kJ to °C
    return df

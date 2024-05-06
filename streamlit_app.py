import streamlit as st
import datetime

import pandas as pd
import datasource
import streamlit as st
import heatings
import electricity as el
import heatdemand as hd
import hplib as hpl
import re
import plotly.express as px
import summaries
import numpy as np

# Inputs
st.set_page_config(layout="wide")
st.title("Heat Pump Simulation")
st.sidebar.title("User Inputs")

zip_code = st.sidebar.number_input("Zip Code", value=80333, step=1)
simulation_year = st.sidebar.selectbox(
    "Simulation Year", list(range(2015, datetime.datetime.now().year)), index=6
)
building_type = st.sidebar.selectbox(
    "Building Type", hd.tab_heat_demand["building_type"].values.tolist(), index=0
)
building_year = st.sidebar.selectbox(
    "Building Year", hd.tab_heat_demand.columns[1:], index=1
)
residents = st.sidebar.selectbox("Residents", el.name_to_file.keys(), index=0)
living_area = st.sidebar.number_input("Living Area", min_value=1, value=120)
floor_count = st.sidebar.number_input("Floor Count", min_value=1, value=2)

st.sidebar.divider()
heating_power_override = None
if st.sidebar.checkbox("Override Heating Power"):
    heating_power_override = st.sidebar.number_input(
        "Heating power [kWh] (override)",
        min_value=1,
        help="Override the calculated heating power based on known power consumption from previous years. For gas and oil heating, multiply with the conversion factor 10 kWh/m³.",
    )

requested_hp_power = hd.heat_pump_size(
    b_type=building_type, b_age=building_year, A=living_area
)

# Advanced Settings
adv_sidebar = st.sidebar.expander("Advanced Settings")
with adv_sidebar:
    # Fetch data
    hp_lib_df = pd.read_csv(hpl.cwd() + r"/data/hplib_database.csv", delimiter=",")
    hp_lib_df = hp_lib_df.loc[hp_lib_df["Type"] == "Outdoor Air/Water", :]
    hp_options = hp_lib_df.loc[
        (hp_lib_df["Rated Power low T [kW]"] > requested_hp_power * 0.8)
        & (hp_lib_df["Rated Power low T [kW]"] < requested_hp_power * 1.1),
        "Titel",
    ].values

    # Function to update date range based on simulation year
    date_range = st.date_input(
        "Date Range for Simulation",
        [datetime.date(simulation_year, 1, 1), datetime.date(simulation_year, 12, 31)],
        min_value=datetime.date(2015, 1, 1),
    )
    window_area = st.number_input(
        "Window Area (m²)",
        min_value=0.0,
        value=living_area * 0.2,
        max_value=float(living_area),
        step=0.1,
    )
    target_temp = st.slider(
        "Target Temperature (°C)", min_value=15, max_value=25, value=20
    )
    comfort_temp_range = st.slider(
        "Comfort Temperature Range (±°C)", min_value=0.0, max_value=5.0, value=1.0
    )
    heatpump_model = st.selectbox("Heat Pump Model", hp_options, index=0)
    model_assumptions = st.multiselect(
        "Model Assumptions",
        [
            "Close window blinds in summer",
            "Ventilation heat losses",
            "Time-dependent electricity mix",
            "CO2-aware controller",
            r"10% forecast uncertainty",
            "Floor heating",
        ],
        [
            "Close window blinds in summer",
            "Ventilation heat losses",
            "Time-dependent electricity mix",
            "CO2-aware controller",
            "Floor heating",
        ],
    )


# Data processing
df = datasource.fetch_all(
    "DE",
    zip_code,
    datetime.datetime.fromisoformat(date_range[0].isoformat()),
    datetime.datetime.fromisoformat(date_range[1].isoformat()),
)

# Electricity modification
with adv_sidebar:
    electricity_source = st.selectbox(
        "Modify Electricity Mix", df.filter(regex="[%]").columns, index=0
    )
    electricity_weight = st.slider(
        "Electricity Weighted",
        min_value=0.0,
        max_value=100.0,
        value=df[electricity_source].mean(),
    )

mean_weight = df[electricity_source].mean()
scaling = electricity_weight / mean_weight
df_copy = df.copy()
df_copy[electricity_source] = df_copy[electricity_source] * scaling
total_percentage_to_distribute = 100 - df_copy[electricity_source]

remaining_df = df_copy.filter(regex="[%]").drop(columns=electricity_source)
scaling_factor = total_percentage_to_distribute / (remaining_df.sum(axis=1))
for col in remaining_df.columns:
    remaining_df[col] = remaining_df[col] * scaling_factor
    df_copy.loc[:, col] = remaining_df.loc[:, col].clip(lower=0, upper=100)
df_copy[electricity_source] = df_copy[electricity_source].clip(lower=0, upper=100)

intensity_df = pd.read_csv("data/co2intensity/co2intensities.csv", sep=";")
intensity_lookup = intensity_df.set_index("Emissions [g CO2eq/kWh]")
df_copy["Intensity [g CO2eq/kWh]"] = 0
for energy_type in df_copy.columns:
    if (
        intensity_df["Emissions [g CO2eq/kWh]"]
        == energy_type.replace("[%]", "[MWh] Calculated resolutions")
    ).any():
        intensity_name = energy_type
        df_copy["Intensity [g CO2eq/kWh]"] += (
            df_copy[intensity_name]
            * 1e-2
            * intensity_lookup.loc[
                energy_type.replace("[%]", "[MWh] Calculated resolutions"), "Med"
            ]
        )
for col in df_copy.columns:
    df[col] = df_copy[col]

if not "Time-dependent electricity mix" in model_assumptions:
    df["Intensity [g CO2eq/kWh]"] = df["Intensity [g CO2eq/kWh]"].mean()

# Simulation of heat pumps
df = el.load_el_profile(df, el.name_to_file[residents])
df = hd.simulate(
    df,
    b_type=building_type,
    hp_type=heatpump_model,
    b_age=building_year,
    A_windows=window_area,
    A=living_area,
    n_floors=floor_count,
    t_target=target_temp,
    t_range=comfort_temp_range,
    assumptions=model_assumptions,
)

if heating_power_override is not None:
    estimated_power = df["Q_dot_supplied [kW]"].sum()
    multiplier = heating_power_override / estimated_power
    print(f"Estimated heating power: {estimated_power} kWh", multiplier)

    colums_to_modify = list(df.filter(regex=r"\[kWh\]").columns)
    colums_to_modify.extend(list(df.filter(regex=r"\[kW\]").columns))
    colums_to_modify.extend(list(df.filter(regex=r"\[kg CO2eq\]").columns))
    colums_to_modify.extend(list(df.filter(regex=r"\[kJ\]").columns))
    df[colums_to_modify] = df[colums_to_modify] * multiplier

    print(colums_to_modify)

df = heatings.gas_heating(df)
df = heatings.oil_heating(df)
df = heatings.pellet_heating(df)

# Generate summary statistics
selected_hp_power = hp_lib_df.loc[
    hp_lib_df["Titel"] == heatpump_model, "Rated Power low T [kW]"
].iat[0]
summaries.generate_summaries(df, selected_hp_power, requested_hp_power, living_area)

# Plotting
widget_counter = 0


def customizable_plot(defaults=["T_outside [°C]", "T_house [°C]"], default_style=0):
    global widget_counter
    col1, col2 = st.columns(2)
    with col1:
        plot1_quantity = st.multiselect(
            "Plot Quantities", df.columns, defaults, key=widget_counter
        )
        widget_counter += 1
    with col2:
        plot1_style = st.radio(
            "Plot Style", ["line", "bar", "area"], default_style, key=widget_counter
        )
        widget_counter += 1

    if plot1_style == "line":
        fig = px.line(df, y=plot1_quantity)
    elif plot1_style == "bar":
        fig = px.histogram(df, x=df.index, y=plot1_quantity).update_traces(
            xbins_size="M1"
        )
    else:
        fig = px.area(df, y=plot1_quantity)

    pattern = r"\[(.*?)\]"
    if len(plot1_quantity) > 0:
        y_unit = re.findall(pattern, plot1_quantity[0])
        if len(y_unit) > 0:
            fig.update_yaxes(title_text=f"value [{y_unit[0]}]")
            fig.update_xaxes(title_text=f"Date")
    st.plotly_chart(fig, use_container_width=True)
    return fig


# CO2 plot
marks = (
    df["heat pump emissions [kg CO2eq]"].rolling(7 * 24, center=True).mean()
    > df["Gas heating emissions [kg CO2eq]"].rolling(7 * 24).mean()
)
marks = marks.loc[marks.diff() != 0]
columns = [
    "Oil heating emissions [kg CO2eq]",
    "Gas heating emissions [kg CO2eq]",
    "heat pump emissions [kg CO2eq]",
]
fig3 = px.line(
    df[columns].replace(0, np.nan),
    y=columns,
    title=(
        "CO2 emissions" + ("" if len(marks) <= 30 else " (could not display all marks)")
    ),
)
for i in range(
    min(len(marks) - 1, 30)
):  # Excessive number of vrects kills performance, limit to 30
    if marks.iat[i] > 0:
        fig3.add_vrect(
            x0=marks.index[i],
            x1=marks.index[i + 1],
            fillcolor="red",
            opacity=0.25,
            layer="below",
            line_width=0,
        )
st.plotly_chart(fig3, use_container_width=True)


with st.expander("Detailed Metrics"):
    summaries.detailed_summaries(df, selected_hp_power, requested_hp_power, living_area)

    customizable_plot()
    # customizable_plot(list(df.filter(regex='[%]').columns), 2)
    customizable_plot(
        [
            "P_el appliances [kW]",
            "Q_dot_solar [kW]",
            "Q_dot_ventilation [kW]",
            "Q_dot_transferred [kW]",
            "Q_dot_supplied [kW]",
        ],
        1,
    )

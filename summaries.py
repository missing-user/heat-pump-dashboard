import pandas as pd
import streamlit as st
from millify import millify
import plotly.graph_objects as go


def generate_summaries(df, selected_hp_power, requested_hp_power, A):
    # Compute total quantities
    df["heat pump emissions [kg CO2eq]"] = (
        df["P_el heat pump [kW]"] * df["Intensity [g CO2eq/kWh]"] * 1e-3
    )
    total_emission_hp = df["heat pump emissions [kg CO2eq]"].sum()
    total_emission_gas = df["Gas heating emissions [kg CO2eq]"].sum()
    total_emission_oil = df["Oil heating emissions [kg CO2eq]"].sum()
    total_heat = df["Q_dot_demand [kW]"].sum()
    total_electrical_energy_hp = df["P_el heat pump [kW]"].sum()
    spf = total_heat / total_electrical_energy_hp

    specific_co2_emissions = total_emission_hp * 1e3 / df["Q_dot_supplied [kW]"].sum()

    # Calculate energy efficiency
    energy_efficiency = df["Q_dot_supplied [kW]"].sum() / A

    col1, col2 = st.columns(2)

    with col1:
        # Create a gauge for specific CO2 emissions
        st.metric(
            "Specific CO2-emissions for heating [g CO2/kWh]",
            millify(specific_co2_emissions),
            delta=millify(specific_co2_emissions - 247),
            delta_color="inverse",
            help="The german average value is 247 g CO2/kWh.",
        )

        # Create a gauge for energy efficiency
        st.metric(
            "Energy Efficiency [kWh/m2 year]",
            millify(energy_efficiency),
            delta=millify(energy_efficiency - 170),
            delta_color="inverse",
            help="The german average value is 170 kWh/m2 year.",
        )
        st.empty()
    with col2:
        st.metric(
            "Total CO2 emissions (heat pump) [kg CO2eq]", millify(total_emission_hp, 1)
        )
        st.metric("Seasonal performance factor", millify(spf, 2))


def detailed_summaries(df, selected_hp_power, requested_hp_power, A):
    total_emission_hp = df["heat pump emissions [kg CO2eq]"].sum()
    total_emission_gas = df["Gas heating emissions [kg CO2eq]"].sum()
    total_emission_oil = df["Oil heating emissions [kg CO2eq]"].sum()
    total_heat = df["Q_dot_demand [kW]"].sum()
    total_electrical_energy_hp = df["P_el heat pump [kW]"].sum()

    # Display total quantities using st.metric
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total heat demand  [kWh]", millify(total_heat, 1))
        st.metric(
            "Total electrical energy (heat pump)  [kWh]",
            millify(total_electrical_energy_hp, 1),
        )
    with col2:
        st.metric(
            "Heat pump power [kW]",
            millify(selected_hp_power, 1),
            millify(selected_hp_power - requested_hp_power, 1),
            help="A green delta means the pump is larger than suggested, a red one smaller than suggested",
        )
        st.metric(
            "Total CO2 emissions of other electrical appliances [kg CO2eq]",
            millify(
                (df["P_el appliances [kW]"] * df["Intensity [g CO2eq/kWh]"]).sum()
                * 1e-3,
                1,
            ),
        )

    with col3:

        # Create a bar chart for annual CO2 emissions
        barchart = go.Figure(
            go.Bar(
                x=["Oil", "Gas", "Pellet", "Heat pump"],
                y=[
                    total_emission_oil,
                    total_emission_gas,
                    df["Pellet heating emissions [kg CO2eq]"].sum(),
                    total_emission_hp,
                ],
            )
        ).update_layout(title_text="CO2 emissions [kg CO2eq]", yaxis_title="kg CO2eq")
        st.plotly_chart(barchart, use_container_width=True)

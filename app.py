import dash
import numpy as np
from dash import dcc, html, Input, State, Output, callback
import pandas as pd

import co2intensity
import heatings
import electricity as el
import heatdemand as hd
import hplib as hpl

import datasource
from datetime import datetime, date

import plotly.io as pio
pio.templates.default = "plotly_white"

# Initialize the Dash app
app = dash.Dash(__name__, use_pages=True)

# Define the layout of the app
app.layout = html.Div([
    html.A("Free",href="./limited"),
    html.A("Premium",href="./academic"),
    dcc.Store('data'),

    # Inputs
    html.Div([
        html.Div([html.Div([
        html.Label("Zip Code"),
        dcc.Input(id="zip-input", type="number", value=80333, placeholder="Enter a Zip Code", debounce=True, persistence=True),
        html.Label('Simulation year'),
        dcc.Dropdown(id="year-input", options=list(range(2010, datetime.now().year)), value=2021, persistence=True),
        html.Label('Date range for simulation', className="advanced"),
        dcc.DatePickerRange(
            id='weather-date-picker-range',
            # TODO: check allowed date range
            min_date_allowed=date(2010, 1, 1),
            max_date_allowed=date(2022, 12, 31),
            persistence=True,
            className="advanced"
        ),
        html.Label('Building type'),
        dcc.Dropdown(
            id='building-dropdown',
            options=hd.tab_heat_demand["building_type"],
            value=hd.tab_heat_demand.iloc[0,0], persistence=True
        ),
        html.Label("Building year"),
        dcc.Dropdown(
            id='building-year-dropdown',
            options=hd.tab_heat_demand.columns[1:],
            value=hd.tab_heat_demand.columns[1], persistence=True
        ),
        html.Label("Residents"),
        dcc.Dropdown(id="family-type-dropdown",
                     options=[{"label":l.replace(".dat", ""),"value": v}for l,v in zip(el.list_readable_electricity_profiles(), el.list_electricity_profiles())],
                     value=el.list_electricity_profiles()[0],persistence=True),

        html.Label("Living area"),
        dcc.Input(id='area', min=1,value=120,type='number', placeholder="Enter area", persistence=True),
        html.Label("Floor count"),
        dcc.Input(2,id='floor', min=1,type='number', placeholder="Enter number of floors", persistence=True),

        html.Label("Window area (m²)",className="advanced"),        
        dcc.Input(id="window-area", min=0,value=20,type='number', placeholder="Enter window area", debounce=True, persistence=True,className="advanced"),

        html.Label("Target temperature (°C)",className="advanced"),
        dcc.Slider(id="target-temp-slider", min=15, max=25, value=20, persistence=True,className="advanced"),

        html.Label("Comfort temperature range (+-) (°C)",className="advanced"),
        dcc.Slider(id="target-temp-range-slider", min=0, max=5, value=1, persistence=True,className="advanced"),
        
        html.Label('Heat pump model',className="advanced"),
        dcc.Dropdown(id='heatpump-model', value='Carnot',persistence=True,className="advanced"),

        html.Label("Model assumptions",className="advanced"),
        dcc.Dropdown(id="model-assumptions", multi=True, value=[], persistence=True, 
                     options=["Close window blinds in summer", 
                            "Ventilation heat losses", 
                            "Time dependent electricity mix",
                            "CO2 aware controller",
                            "Floor heating"],className="advanced"),

        html.Label("Modify electricity mix", className="advanced"),
        dcc.Dropdown(id="electricity-source", multi=False,value=[],persistence=True,className="advanced"),
        html.Label("electricity weighted", className="advanced"),
        dcc.Slider(id="electricity-weight", min=0.,max=100.,value=0.,persistence=True,className="advanced"),

        html.Label("Plot 1 Quantities",className="advanced"), 
        dcc.Dropdown(id='plot1-quantity', multi=True, value="T_outside [°C]", placeholder="(mandatory) Select (multiple) y-Value(s)",persistence=True,className="advanced"),
        html.Label("Plot 1 Style",className="advanced"), 
        dcc.RadioItems(["line", "bar", "area"], "line", id="plot1-style",persistence=True,className="advanced"),
        html.Label("Plot 2 Quantities",className="advanced"), 
        dcc.Dropdown(id='plot2-quantity', multi=True, value="T_outside [°C]", placeholder="(mandatory) Select (multiple) y-Value(s)",persistence=True,className="advanced"),
        html.Label("Plot 2 Style",className="advanced"), 
        dcc.RadioItems(["line", "bar", "area"], "line", id="plot2-style", persistence=True,className="advanced"),
        ], className="input-container"),]),

        dash.page_container   
    ], className="main-container"),
])

@app.callback(
    Output("weather-date-picker-range","start_date"),
    Output("weather-date-picker-range","end_date"),
    Input("year-input", "value"))
def simple_date(year):
    return date(year, 1,1).isoformat(), date(year, 12, 31).isoformat()

@app.callback(
    Output('window-area', 'value'),
    Input('area','value'))
def set_window_area(floor_area):
    return floor_area * 0.2

@app.callback(
    Output('data','data'),
    Output('plot1-quantity','options'),
    Output('plot2-quantity','options'),
    Output('heatpump-model', 'options'),
    Output("electricity-source", "options"),
    Output("electricity-weight","value"),

    State("data","data"),

    Input('zip-input', 'value'),
    Input('weather-date-picker-range', 'start_date'),
    Input('weather-date-picker-range', 'end_date'),
    Input('building-dropdown','value'),
    Input('building-year-dropdown','value'),
    Input("family-type-dropdown", "value"),
    Input('area', 'value'),
    Input('floor','value'),
    Input('window-area', 'value'),
    Input("target-temp-slider", "value"),
    Input("target-temp-range-slider", "value"),
    Input('heatpump-model','value'),
    Input("model-assumptions", "value"),
    Input("electricity-source","value"),
    Input("electricity-weight","value"),
    )
def update_dashboard(df_json,
                     zip_code, start_date, end_date, building_type,
                     building_year, family_type, area, n_floors, window_area,
                      temperature_target, range_target, model,
                     assumptions, electricity_source, electricity_weight):
    hp_lib_df = pd.read_csv(hpl.cwd() + r'/data/hplib_database.csv', delimiter=',')
    hp_lib_df = hp_lib_df.loc[hp_lib_df['Type'] == 'Outdoor Air/Water', :]
    if model is None:
        model = "Carnot"

    # If initial call, check for existence of a data-frame
    print("triggered", dash.ctx.triggered_id)
    if dash.ctx.triggered_id is None:
        print("dataframe storage", df_json)
        if df_json is not None:
            print("prevented initial recalc call")
            df = pd.DataFrame(df_json["data"], df_json["index"], df_json["columns"])
            return df_json, df.columns.values, df.columns.values, hp_lib_df['Titel'].values

    # fetch data
    df = datasource.fetch_all("DE", zip_code, start_date, end_date)
    if not "Time dependent electricity mix" in assumptions:
        df["Intensity [g CO2eq/kWh]"] = df["Intensity [g CO2eq/kWh]"].mean()

    if electricity_source:
        # no weight specified
        if not electricity_weight:
            electricity_weight = df[electricity_source].mean()
        else:
            mean_weight = df[electricity_source].mean()
            # modify columns
            scaling = electricity_weight / mean_weight
            df_copy = df.copy()
            df_copy[electricity_source] = df_copy[electricity_source] * scaling
            total_percentage_to_distribute = 100 - df_copy[electricity_source]

            remaining_df = df_copy.filter(regex="[%]")
            remaining_df.drop(columns=electricity_source,inplace=True)
            scaling_factor = total_percentage_to_distribute / (remaining_df.sum(axis=1))
            for col in remaining_df.columns:
                remaining_df[col] = remaining_df[col] * scaling_factor
                df_copy.loc[:,col] = remaining_df.loc[:,col].clip(lower=0, upper=100)
            df_copy[electricity_source] = df_copy[electricity_source].clip(lower=0, upper=100)

            intensity_df = pd.read_csv("data/co2intensity/co2intensities.csv", sep=';')
            intensity_lookup = intensity_df.set_index("Emissions [g CO2eq/kWh]")
            for energy_type in df_copy.columns:
                if (intensity_df["Emissions [g CO2eq/kWh]"] == energy_type.replace( "[%]","[MWh] Calculated resolutions")).any():
                    intensity_name = energy_type
                    #df_copy[intensity_name] = df_copy[energy_type] / df_copy["MWh sum"] * 100
                    df_copy["Intensity [g CO2eq/kWh]"] += df_copy[intensity_name] * 1e-2 * intensity_lookup.loc[
                        energy_type.replace("[%]","[MWh] Calculated resolutions"), "Med"]
            pass
            for col in df_copy.columns:
                df[col] = df_copy[col]

    else:
        electricity_weight = 0.
    electricity_sources = df.filter(regex='[%]').columns


    df:pd.DataFrame = el.load_el_profile(df, family_type)
    df = hd.simulate(df, b_type=building_type, hp_type=model, b_age=building_year,
                     A_windows=window_area, A=area, n_floors=n_floors,
                     t_target=temperature_target, t_range=range_target,
                     assumptions=assumptions)
    df = heatings.gas_heating(df)
    df = heatings.oil_heating(df)
    df = heatings.pellet_heating(df)

    requested_hp_power = hd.heat_pump_size(b_type=building_type, b_age=building_year, A=area)

    hp_options = hp_lib_df.loc[(hp_lib_df["Rated Power low T [kW]"] > requested_hp_power*0.8) &
                  (hp_lib_df["Rated Power low T [kW]"] > requested_hp_power*1.1), 'Titel'].values

    return {"data-frame": df.reset_index().to_dict("split"),
            "heat-pump-power": requested_hp_power,
            "area":area,
            }, df.columns.values, df.columns.values, hp_options, electricity_sources, electricity_weight


if __name__ == '__main__':
    app.run_server(debug=True)

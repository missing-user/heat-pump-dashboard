import dash
from dash import dcc, html, Input, State, Output, callback
import pandas as pd
import heatings
import electricity as el
import heatdemand as hd

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
    html.Div(children=[
        html.Label('Enter location for weather data:'),
        html.Label("Zip Code"),
        dcc.Input(id="zip-input", type="number", value=80333, placeholder="Enter a Zip Code", debounce=True, persistence=False),
        html.Label('Pick date range for simulation'),
        dcc.Dropdown(id="year-input", options=list(range(2010, datetime.now().year)), value=2021, persistence=False),
        dcc.DatePickerRange(
            id='weather-date-picker-range',
            # TODO: check allowed date range
            min_date_allowed=date(2010, 1, 1),
            max_date_allowed=date(2022, 12, 31),
            persistence=False
        ),
        html.Div(id='selected-date'),
        html.Label('Select building type'),
        dcc.Dropdown(
            id='building-dropdown',
            options=hd.tab_heat_demand["building_type"],
            value=hd.tab_heat_demand.iloc[0,0], persistence=False
        ),
        dcc.Dropdown(
            id='building-year-dropdown',
            options=hd.tab_heat_demand.columns[1:],
            value=hd.tab_heat_demand.columns[3], persistence=False
        ),
        dcc.Dropdown(id="family-type-dropdown",
                     options=[{"label":l,"value": v}for l,v in zip(el.list_readable_electricity_profiles(), el.list_electricity_profiles())],
                     value=el.list_electricity_profiles()[0],persistence=False),

        dcc.Input(id='area', min=1,value=120,type='number', placeholder="Enter area", debounce=True, persistence=False),
        dcc.Input(id="window-area", min=0,value=20,type='number', placeholder="Enter window area", debounce=True, persistence=False),
        dcc.Slider(id="vorlauftemp-slider", min=35, max=80, value=35, persistence=False),
        dcc.Slider(id="target-temp-slider", min=15, max=25, value=20, persistence=False),
        html.Label('Select model for heat pump'),

        dcc.Dropdown(
            id='heatpump-model',
            options=[
                {'label': 'Carnot', 'value': 'Carnot'},
                {'label': 'sophisticated', 'value': 'soph'},
            ],
            value='Carnot',persistence=False
        ),
        html.Label("Floor count"),
        dcc.Input(2, min=1,type='number', placeholder="Enter number of floors", debounce=True, persistence=False),
        dcc.Dropdown(id="model-assumptions", multi=True, value=[], persistence=False, 
                     options=["Close window blinds in summer", 
                            "Ventilation heat losses", 
                            "Time dependent electricity mix"]),
        html.Br(),
        dcc.Dropdown(id='plot1-quantity', multi=True, value="T_outside [°C]", placeholder="(mandatory) Select (multiple) y-Value(s)",persistence=False),
        html.Div([html.Label("Plot 1 Style: "), dcc.RadioItems(["line", "bar"], "line", id="plot1-style")]),
        dcc.Dropdown(id='plot2-quantity', multi=True, value="T_outside [°C]", placeholder="(mandatory) Select (multiple) y-Value(s)",persistence=False),
        html.Div([html.Label("Plot 2 Style: "), dcc.RadioItems(["line", "bar"], "line", id="plot2-style")]),
        ], style={'width': '300px'}),

    dash.page_container   
])

@app.callback(
    Output("weather-date-picker-range","start_date"),
    Output("weather-date-picker-range","end_date"),
    Input("year-input", "value"))
def simple_date(year):
    return date(year, 1,1).isoformat(), date(year, 12, 31).isoformat()

@app.callback(
    Output('data','data'),
    Output('plot1-quantity','options'),
    Output('plot2-quantity','options'),

    State("data","data"),

    Input('zip-input', 'value'),
    Input('weather-date-picker-range', 'start_date'),
    Input('weather-date-picker-range', 'end_date'),
    Input('building-dropdown','value'),
    Input('building-year-dropdown','value'),
    Input("family-type-dropdown", "value"),
    Input('area', 'value'),
    Input('window-area', 'value'),
    Input("vorlauftemp-slider", "value"),
    Input("target-temp-slider", "value"),
    Input('heatpump-model','value'),
    Input("model-assumptions", "value")
    )
def update_dashboard(df_json,
                     zip_code, start_date, end_date, building_type, 
                     building_year, family_type, area, window_area, 
                     vorlauf_temp, temperature_target, model, 
                     assumptions):
    print(start_date, end_date)
    
    # If initial call, check for existence of a data-frame
    print("triggered", dash.ctx.triggered_id)
    if dash.ctx.triggered_id is None:
        print("dataframe storage", df_json)
        if df_json is not None:
            print("prevented initial recalc call")
            df = pd.DataFrame(df_json["data-frame"]).set_index("index")
            return df_json, df.columns.values, df.columns.values

    # fetch data
    df = datasource.fetch_all("DE", zip_code, start_date, end_date)
    if not "Time dependent electricity mix" in assumptions:
        df["Intensity [g CO2eq/kWh]"] = df["Intensity [g CO2eq/kWh]"].mean()

    df:pd.DataFrame = el.load_el_profile(df, family_type)
    # compute P and electrical Power
    df = heatings.compute_cop(df,model,vorlauf_temp)
    df = hd.simulate(df, b_type=building_type, b_age=building_year, 
                     A_windows=window_area, A=area, 
                     t_target=temperature_target,
                     assumptions=assumptions)
    df = heatings.compute_P_electrical(df)
    df = heatings.gas_heating(df)
    df = heatings.oil_heating(df)

    return {"data-frame": df.reset_index().to_dict(orient="split"),
            "heat-pump-power": hd.heat_pump_size(b_type=building_type, b_age=building_year, A=area)}, df.columns.values, df.columns.values


if __name__ == '__main__':
    app.run_server(debug=False)

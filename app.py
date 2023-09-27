import dash
from dash import dcc, html, Input, State, Output, callback
import pandas as pd
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
        dcc.Input(id="zip-input", type="number", value=80333, placeholder="Enter a Zip Code", debounce=True, persistence=False),
        html.Label('Simulation year'),
        dcc.Dropdown(id="year-input", options=list(range(2010, datetime.now().year)), value=2021, persistence=False),
        html.Label('Date range for simulation', className="advanced"),
        dcc.DatePickerRange(
            id='weather-date-picker-range',
            # TODO: check allowed date range
            min_date_allowed=date(2010, 1, 1),
            max_date_allowed=date(2022, 12, 31),
            persistence=False,
            className="advanced"
        ),
        html.Label('Building type'),
        dcc.Dropdown(
            id='building-dropdown',
            options=hd.tab_heat_demand["building_type"],
            value=hd.tab_heat_demand.iloc[0,0], persistence=False
        ),
        html.Label("Building year"),
        dcc.Dropdown(
            id='building-year-dropdown',
            options=hd.tab_heat_demand.columns[1:],
            value=hd.tab_heat_demand.columns[3], persistence=False
        ),
        html.Label("Residents"),
        dcc.Dropdown(id="family-type-dropdown",
                     options=[{"label":l.replace(".dat", ""),"value": v}for l,v in zip(el.list_readable_electricity_profiles(), el.list_electricity_profiles())],
                     value=el.list_electricity_profiles()[0],persistence=False),

        html.Label("Living area"),
        dcc.Input(id='area', min=1,value=120,type='number', placeholder="Enter area", debounce=True, persistence=False),
        html.Label("Floor count"),
        dcc.Input(2, min=1,type='number', placeholder="Enter number of floors", debounce=True, persistence=False),

        html.Label("Window area (m²)",className="advanced"),        
        dcc.Input(id="window-area", min=0,value=20,type='number', placeholder="Enter window area", debounce=True, persistence=False,className="advanced"),

        html.Label("Target temperature (°C)",className="advanced"),
        dcc.Slider(id="target-temp-slider", min=15, max=25, value=20, persistence=False,className="advanced"),
        
        html.Label('Heat pump model',className="advanced"),
        dcc.Dropdown(id='heatpump-model', value='Carnot',persistence=False,className="advanced"),

        html.Label("Model assumptions",className="advanced"),
        dcc.Dropdown(id="model-assumptions", multi=True, value=[], persistence=False, 
                     options=["Close window blinds in summer", 
                            "Ventilation heat losses", 
                            "Time dependent electricity mix"],className="advanced"),

        html.Label("Plot 1 Quantities",className="advanced"), 
        dcc.Dropdown(id='plot1-quantity', multi=True, value="T_outside [°C]", placeholder="(mandatory) Select (multiple) y-Value(s)",persistence=False,className="advanced"),
        html.Label("Plot 1 Style",className="advanced"), 
        dcc.RadioItems(["line", "bar"], "line", id="plot1-style",className="advanced"),
        html.Label("Plot 2 Quantities",className="advanced"), 
        dcc.Dropdown(id='plot2-quantity', multi=True, value="T_outside [°C]", placeholder="(mandatory) Select (multiple) y-Value(s)",persistence=False,className="advanced"),
        html.Label("Plot 2 Style",className="advanced"), 
        dcc.RadioItems(["line", "bar"], "line", id="plot2-style", className="advanced"),
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
    Output('data','data'),
    Output('plot1-quantity','options'),
    Output('plot2-quantity','options'),
    Output('heatpump-model', 'options'),

    State("data","data"),

    Input('zip-input', 'value'),
    Input('weather-date-picker-range', 'start_date'),
    Input('weather-date-picker-range', 'end_date'),
    Input('building-dropdown','value'),
    Input('building-year-dropdown','value'),
    Input("family-type-dropdown", "value"),
    Input('area', 'value'),
    Input('window-area', 'value'),
    #Input("vorlauftemp-slider", "value"),
    Input("target-temp-slider", "value"),
    Input('heatpump-model','value'),
    Input("model-assumptions", "value")
    )
def update_dashboard(df_json,
                     zip_code, start_date, end_date, building_type,
                     building_year, family_type, area, window_area, 
                      temperature_target, model,
                     assumptions):
    hp_lib_df = pd.read_csv(hpl.cwd() + r'/data/hplib_database.csv', delimiter=',')
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

    df:pd.DataFrame = el.load_el_profile(df, family_type)
    # compute P and electrical Power
    #df = heatings.compute_cop(df,model,vorlauf_temp)
    df = hd.simulate(df, b_type=building_type, hp_type=model, b_age=building_year,
                     A_windows=window_area, A=area, 
                     t_target=temperature_target,
                     assumptions=assumptions)
    #df = heatings.compute_P_electrical(df)
    df = heatings.gas_heating(df)
    df = heatings.oil_heating(df)

    return {"data-frame": df.reset_index().to_dict("split"),
            "heat-pump-power": hd.heat_pump_size(b_type=building_type, b_age=building_year, A=area)}, df.columns.values, df.columns.values, hp_lib_df['Titel'].values


if __name__ == '__main__':
    app.run_server(debug=True)

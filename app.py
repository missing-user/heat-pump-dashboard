import dash
from dash import Dash, dcc, html, Input, Output, callback
import plotly.express as px
import pandas as pd
import heatpump as hf
import heatdemand as hd

import datasource
from datetime import datetime, date
import numpy as np

# Initialize the Dash app
app = dash.Dash(__name__)

# Define the layout of the app
app.layout = html.Div([
    html.Div(children=[
        html.Label('Enter location for weather data:'),
        html.Label("Zip Code"),
        dcc.Input(id="zip-input", type="number", placeholder="Enter a Zip Code", debounce=True),
        html.Label('Pick date range for simulation'),
        dcc.DatePickerRange(
            id='weather-date-picker-range',
            # TODO: check allowed date range
            min_date_allowed=date(2015, 1, 1),
            max_date_allowed=date(2022, 12, 31),
            initial_visible_month=date(2021, 1, 1),
            start_date=date(2021,1,1),
            end_date=date(2021, 12, 31),
            updatemode='bothdates',
        ),
        html.Div(id='selected-date'),
        html.Label('Select building type'),
        dcc.Dropdown(
            id='building-dropdown',
            options=hd.tab_heat_demand["building_type"],
            value=hd.tab_heat_demand.iloc[0,0],
        ),
        dcc.Dropdown(
            id='building-year-dropdown',
            options=hd.tab_heat_demand.columns[1:],
            value=hd.tab_heat_demand.columns[3],
        ),

        dcc.Input(id='area',min=1,value=100,type='number', placeholder="Enter area", debounce=True),

        html.Label('Select model for heat pump'),

        dcc.Dropdown(
            id='heatpump-model',
            options=[
                {'label': 'Carnot', 'value': 'Carnot'},
                {'label': 'sophisticated', 'value': 'soph'},
            ],
        ),
        html.Div(id='selected-heat-pump-model'),
        dcc.Store(id='data'),
        html.Button(id='plot-button', n_clicks=0, children='plot'),
    ], style={'width': '300px', 'float': 'left'}),

    html.Div(children=[
    html.Div([
        dcc.Graph(id='plot1'),
        dcc.Graph(id='plot2'),
    ], style={'display': 'inline-block'}),
    html.Div([
        dcc.Graph(id='plot3'),
        dcc.Graph(id='plot4'),
    ], style={'display': 'inline-block'})
    ]),
], style = {'font-family':'sans-serif'})

@callback(
    Output('plot1','figure'),
    Output('plot2','figure'),
    Output('plot3', 'figure'),
    Output('plot4','figure'),

    Input('zip-input', 'value'),
    Input('weather-date-picker-range', 'start_date'),
    Input('weather-date-picker-range', 'end_date'),
    Input('building-dropdown','value'),
    Input('building-year-dropdown','value'),
    Input('area', 'value'),
    Input('heatpump-model','value'),
    Input('plot-button', 'n_clicks'),
    config_prevent_initial_callbacks=True,
    )
def update_dashboard(zip_code, start_date, end_date, building_type, building_year, area, model, n_clicks):
    df = pd.DataFrame()
    # fetch data
    df = fetch_data(df,start_date,end_date,zip_code)

    # compute COP and electrical Power
    df = hf.compute_cop(df,model)
    df = hd.heat_demand(df, b_type=building_type, b_age=building_year,t_design=-15, A=area)
    df = hf.compute_P_electrical(df)

    # compute total quantities
    df["emissions [kg CO2eq]"] = df["P_el"] * df["Intensity [g CO2eq/kWh]"] *1e-3
    total_emission = df["emissions [kg CO2eq]"].sum()
    total_heat = df['Q_H'].sum()
    total_electrical_energy = df['P_el'].sum()
    spf = total_heat/total_electrical_energy


    # generate plots/output
    print(total_emission, total_heat, total_electrical_energy, spf)
    fig1 = px.line(df,y='temp')
    fig2 = px.line(df,y='emissions [kg CO2eq]')
    fig3 = px.line(df,y='Q_H')
    fig4 = px.line(df,y='P_el')
    return [fig1,fig2,fig3,fig4]

def fetch_data(df, start_date,end_date,zip_code):
    if start_date and end_date and zip_code:
        start_date_object = datetime.fromisoformat(start_date)
        end_date_object = datetime.fromisoformat(end_date)
        df = datasource.fetch_all(country_code='DE',zip_code=zip_code,start=start_date_object,end=end_date_object,)
    return df

# Run the app
if __name__ == '__main__':
    app.run_server(debug=False)

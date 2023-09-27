import dash
from dash import Dash, dcc, html, Input, Output, State, callback
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
from plotly.subplots import make_subplots
import pandas as pd
import heatings
import electricity as el
import heatdemand as hd
import io
import datasource
from datetime import datetime, date
import numpy as np

pio.templates.default = "plotly_white"

dash.register_page(__name__)

# Define the layout of the app
layout = html.Div([
  html.Div([
    html.Label("Zip Code"),
    dcc.Input(id="zip-input", type="number", value=80333, placeholder="Enter a Zip Code", debounce=True, persistence=True),    
    html.Label('Select building type'),
    dcc.Dropdown(
        id='building-dropdown',
        options=hd.tab_heat_demand["building_type"],
        value=hd.tab_heat_demand.iloc[0,0], persistence=True
    ),
    html.Label('Select building year'),
    dcc.Dropdown(
        id='building-year-dropdown',
        options=hd.tab_heat_demand.columns[1:],
        value=hd.tab_heat_demand.columns[3], persistence=True
    ),
    html.Label('Load profile of habitants'),
    dcc.Dropdown(id="family-type-dropdown",
                  options=[{"label":l,"value": v}for l,v in zip(el.list_readable_electricity_profiles(), el.list_electricity_profiles())],
                  value=el.list_electricity_profiles()[0],persistence=True),

    dcc.Input(id='area', min=1,value=120,type='number', placeholder="Enter area", debounce=True, persistence=True),
        
  ]),
  html.Div([
    dcc.Loading(dcc.Graph(id='gauge-heatpump')),
    dcc.Loading(dcc.Graph(id='gauge-gas')),
    dcc.Loading(dcc.Graph(id='gauge-oil')),
    ])
])


@callback(
    Output('gauge-heatpump', 'figure'),
    Output('gauge-gas', 'figure'),
    Output('gauge-oil', 'figure'),
    
    Input('data','data'),
)
def update_gauges(df_json):
  if df_json is not None:
    df = pd.DataFrame(**df_json["data-frame"]).set_index("index")
    
  gauge = go.Figure(go.Indicator(
    mode = "gauge+number",
    value = 270,
    domain = {'x': [0, 1], 'y': [0, 1]},
    title = {'text': "CO2 Savings"}))
  
  barchart = px.bar(x=["Gas", "Oil"], y=[100, 200], title="CO2 Emissions")
  return gauge, barchart, {}

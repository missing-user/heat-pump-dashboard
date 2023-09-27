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
import dash_dangerously_set_inner_html
import datasource
from datetime import datetime, date
import numpy as np

pio.templates.default = "plotly_white"

dash.register_page(__name__)

# Define the layout of the app
layout = html.Div([
  html.Div([
    dcc.Loading(dcc.Graph(id='gauge-heatpump')),
    dcc.Loading(dcc.Graph(id='gauge-gas')),
    dcc.Loading(dcc.Graph(id='gauge-oil')),
    ]),

  dash_dangerously_set_inner_html.DangerouslySetInnerHTML('''
<style>.advanced {
  visibility: collapse;
  display: none !important;
}</style>'''),
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

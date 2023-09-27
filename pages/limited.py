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
  df = pd.DataFrame(df_json["data-frame"]["data"], df_json["data-frame"]["index"], df_json["data-frame"]["columns"]).set_index("index")
    
  gauge = go.Figure(go.Indicator(
      domain={'x': [0, 1], 'y': [0, 1]},
      value=450,
      mode="gauge+number",
      title={'text': "specific CO2-emissions [gCO2/kWh]"},
      delta={'reference': 247, },
      gauge={'axis': {'range': [None, 700], 'tickvals': [0, 100,200, 247,300,400,500,600, 700], 'ticktext': ["0", "100", "200", "AVG", "300", "400", "500", "600", "700"]},
             'bar': {'color': "lightgrey"},
             'steps': [
                 {'range': [0, 247], 'color': "green"},
                 {'range': [248, 700], 'color': "red"},
             ],
             'threshold': {'line': {'color': "black", 'width': 5}, 'thickness': 1, 'value': 247, }
             }
  ))

  gauge_2 = go.Figure(go.Indicator(
      domain={'x': [0, 1], 'y': [0, 1]},
      value=100,
      mode="gauge+number",
      title={'text': "specific heat demand [kWh/m^2*a]"},
      delta={'reference': 170, },
      gauge={'axis': {'range': [None, 300], 'tickvals': [15, 40, 62.5, 87.5, 115, 145, 170, 180, 225, 275],
                    'ticktext': ["A+", "A", "B", "C", "D", "E","AVG", "F", "G", "H" ],
             'ticks': ""},
             'bar': {'color': "lightgrey"},
             'steps': [
                 {'range': [0, 30], 'color': "darkgreen"},
                 {'range': [30, 50], 'color': "green"},
                 {'range': [50, 75], 'color': "greenyellow"},
                 {'range': [75, 100], 'color': "yellow"},
                 {'range': [100, 130], 'color': "orange"},
                 {'range': [130, 160], 'color': "darkorange"},
                 {'range': [160, 200], 'color': "red"},
                 {'range': [200, 250], 'color': "darkred"},
                 {'range': [250, 300], 'color': "purple"},
             ],
             'threshold': {'line': {'color': "black", 'width': 5}, 'thickness': 1, 'value': 170, }
             }
  ))
  barchart = px.bar(x=["Gas", "Oil"], y=[100, 200], title="CO2 Emissions")
  return gauge, gauge_2 , barchart

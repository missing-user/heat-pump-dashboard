import dash
from dash import Dash, dcc, html, Input, Output, callback
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
    html.Div(children=[
        html.Div(children=[
            html.Div(children=[

            ], style={'display':'inline-block', 'width':'40%'}),
        ]),

        html.H2('Total emissions:'),
        html.Div(id='total-emissions'),
        dcc.Loading(dcc.Graph(id='plot1')),
        dcc.Loading(dcc.Graph(id='plot2')),
        dcc.Loading(dcc.Graph(id='plot3')),
     ], style={'width': '100%'})
], style = {'display':'flex'})

@callback(
    Output('total-emissions','children'),    
    Input('data','data'),
  )
def show_summaries(df_json):
    df = pd.DataFrame(**df_json["data-frame"]).set_index("index")
    
    # compute total quantities
    df["heat pump emissions [kg CO2eq]"] = df["P_el heat pump [kW]"] * df["Intensity [g CO2eq/kWh]"] * 1e-3
    total_emission_hp = df["heat pump emissions [kg CO2eq]"].sum()
    total_emission_gas = df["Gas heating emissions [kg CO2eq]"].sum()
    total_emission_oil = df["Oil heating emissions [kg CO2eq]"].sum()
    total_heat = df['Q_dot_H [kW]'].sum()
    total_electrical_energy_hp = df['P_el heat pump [kW]'].sum()
    spf = total_heat/total_electrical_energy_hp

    # display total quantities
    fig2 = html.Div(children=[
        html.Div(f"Total heat demand:                   {total_heat:.1f} kWh"),
        html.Div(f"Total electrical energy (heat pump): {total_electrical_energy_hp:.1f} kWh"),
        html.Div(f"Total CO2 emissions (heat pump):     {total_emission_hp:.1f} kg CO2eq"),
        html.Div(f"Total CO2 emissions (oil heating):   {total_emission_oil:.1f} kg CO2eq"),
        html.Div(f"Total CO2 emissions (gas heating):   {total_emission_gas:.1f} kg CO2eq"),
        html.Div(f"SPF:                                 {spf:.1f}"),
        html.Div(f"Heat Pump Power:         {df_json['heat-pump-power']} kW")
    ])

    return fig2

@callback(
    Output('plot1','figure'),
    Output('plot2','figure'),
    Output('plot3','figure'),

    Input('data','data'),
    Input('plot1-quantity','value'),
    Input('plot2-quantity','value'),
    Input('plot1-style','value'),
    Input('plot2-style','value'),
    prevent_initial_call=True)
def draw_plot(df_json, y1, y2, s1, s2):
    df = pd.DataFrame(**df_json["data-frame"]).set_index("index")
    
    # generate plots
    fig = px.line(df,y=y1) if s1 == 'line' else px.histogram(df, x=df.index, y=y1).update_traces(xbins_size="M1")
    fig2 = px.line(df,y=y2) if s2 == 'line' else px.histogram(df, x=df.index, y=y2).update_traces(xbins_size="M1")   
    fig3 = px.line(df, y=['Oil heating emissions [kg CO2eq]',
                          'Gas heating emissions [kg CO2eq]',
                          'heat pump emissions [kg CO2eq]'])
    
    marks = df['heat pump emissions [kg CO2eq]'] > df['Gas heating emissions [kg CO2eq]']
    marks = marks.loc[marks.diff() != 0]
    for i in range(len(marks)):
        if marks.iat[i] > 0:
            fig3.add_vrect(x0=marks.index[i], x1=marks.index[i+1], fillcolor="red", opacity=0.25, layer="below", line_width=0)

    return fig, fig2, fig3


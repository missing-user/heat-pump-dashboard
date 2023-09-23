import dash
from dash import Dash, dcc, html, Input, Output, callback
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
from plotly.subplots import make_subplots
import pandas as pd
import heatpump as hf
import electricity as el
import heatdemand as hd

import datasource
from datetime import datetime, date
import numpy as np

pio.templates.default = "plotly_white"

# Initialize the Dash app
app = dash.Dash(__name__)

# Define the layout of the app
app.layout = html.Div([
    html.Div(children=[
        html.Label('Enter location for weather data:'),
        html.Label("Zip Code"),
        dcc.Input(id="zip-input", type="number", value=80333, placeholder="Enter a Zip Code", debounce=True),
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
        dcc.Dropdown(id="family-type-dropdown",
                     options=[{"label":l,"value": v}for l,v in zip(el.list_readable_electricity_profiles(), el.list_electricity_profiles())],
                     value=el.list_electricity_profiles()[0]),

        dcc.Input(id='area',min=1,value=120,type='number', placeholder="Enter area", debounce=True),

        html.Label('Select model for heat pump'),

        dcc.Dropdown(
            id='heatpump-model',
            options=[
                {'label': 'Carnot', 'value': 'Carnot'},
                {'label': 'sophisticated', 'value': 'soph'},
            ],
            value='Carnot'
        ),
        html.Div(id='selected-heat-pump-model'),
        dcc.Store(id='data'),
        html.Br(),
        dcc.Dropdown(id='plot1-quantity', multi=False, value="temp", placeholder="(mandatory) Select (multiple) y-Value(s)"),
        dcc.Dropdown(id='plot2-quantity', multi=False, value="temp", placeholder="(mandatory) Select (multiple) y-Value(s)"),
        dcc.Dropdown(id='plot3-quantity', multi=False, value="temp", placeholder="(mandatory) Select (multiple) y-Value(s)"),
        dcc.Dropdown(id='plot4-quantity', multi=False, value="T_house", placeholder="(mandatory) Select (multiple) y-Value(s)"),
        html.Div([html.Label("Plot 1 Style: "), dcc.RadioItems(["line", "bar"], "line", id="plot1-style", style={"display" : "inline-block"})]),
        html.Div([html.Label("Plot 2 Style: "), dcc.RadioItems(["line", "bar"], "line", id="plot2-style", style={"display" : "inline-block"})]),
        html.Div([html.Label("Plot 3 Style: "), dcc.RadioItems(["line", "bar"], "line", id="plot3-style", style={"display" : "inline-block"})]),
        html.Div([html.Label("Plot 4 Style: "), dcc.RadioItems(["line", "bar"], "line", id="plot4-style", style={"display" : "inline-block"})]),
        ], style={'width': '300px'}),

    html.Div(children=[
        html.Div(children=[
            html.Div(children=[

            ], style={'display':'inline-block', 'width':'40%'}),
        ]),
        dcc.Loading(dcc.Graph(id='plot1')),
        html.H2('Total emissions:'),
        html.Div(id='total-emissions'),
     ], style={'width': '100%'})
], style = {'display':'flex'})

@callback(
    Output('plot1','figure'),
    Output('total-emissions','children'),
    Output('plot1-quantity','options'),
    Output('plot2-quantity','options'),
    Output('plot3-quantity','options'),
    Output('plot4-quantity','options'),

    Input('zip-input', 'value'),
    Input('weather-date-picker-range', 'start_date'),
    Input('weather-date-picker-range', 'end_date'),
    Input('building-dropdown','value'),
    Input('building-year-dropdown','value'),
    Input("family-type-dropdown", "value"),
    Input('area', 'value'),
    Input('heatpump-model','value'),
    Input('plot1-quantity','value'),
    Input('plot2-quantity','value'),
    Input('plot3-quantity','value'),
    Input('plot4-quantity','value'),
    Input('plot1-style','value'),
    Input('plot2-style','value'),
    Input('plot3-style','value'),
    Input('plot4-style','value'),
    )
def update_dashboard(zip_code, start_date, end_date, building_type, building_year, family_type, area, model, y1, y2, y3, y4, s1, s2, s3, s4):
    ctx = dash.callback_context

    # fetch data
    df = fetch_data(start_date,end_date,zip_code)
    df = el.load_el_profile(df, family_type)
    # compute COP and electrical Power
    df = hf.compute_cop(df,model)
    #df = hd.heat_demand(df, b_type=building_type, b_age=building_year, A=area)
    df = hd.simulate(df, b_type=building_type, b_age=building_year, A=area)
    df = hf.compute_P_electrical(df)

    # compute total quantities
    df["emissions [kg CO2eq]"] = df["P_el"] * df["Intensity [g CO2eq/kWh]"] * 1e-3
    total_emission = df["emissions [kg CO2eq]"].sum()
    total_heat = df['Q_dot_H'].sum()
    total_electrical_energy = df['P_el'].sum()
    spf = total_heat/total_electrical_energy

    # generate plots
    fig = make_subplots(rows=2, cols=2, shared_xaxes=True).update_layout(height=900)
    if s1 == 'line':
        fig.add_trace(px.line(df,y=y1).data[0], row=1, col=1)
    elif s1 == 'bar':
        fig.add_trace(px.histogram(df, x=df.index, y=y1).update_traces(xbins_size="M1").data[0], row=1, col=1)

    if s2 == 'line':
        fig.add_trace(px.line(df,y=y2).data[0], row=1, col=2)
    elif s2 == 'bar':
        fig.add_trace(px.histogram(df, x=df.index, y=y2).update_traces(xbins_size="M1").data[0], row=1, col=2)

    if s3 == 'line':
        fig.add_trace(px.line(df,y=y3).data[0], row=2, col=1)
    elif s3 == 'bar':
        fig.add_trace(px.histogram(df, x=df.index, y=y3).update_traces(xbins_size="M1").data[0], row=2, col=1)

    if s4 == 'line':
        fig.add_trace(px.line(df,y=y4).data[0], row=2, col=2)
    elif s4 == 'bar':
        fig.add_trace(px.histogram(df, x=df.index, y=y4).update_traces(xbins_size="M1").data[0], row=2, col=2)

    
    # Add y axis labels
    fig.update_yaxes(title_text=y1, row=1, col=1)
    fig.update_yaxes(title_text=y2, row=1, col=2)
    fig.update_yaxes(title_text=y3, row=2, col=1)
    fig.update_yaxes(title_text=y4, row=2, col=2)

    # display total quantities
    fig2 = html.Div(children=[
        html.Div(f"Total emissions:         {total_emission:.1f} kg CO2eq"),
        html.Div(f"Total heat demand:       {total_heat:.1f} kWh"),
        html.Div(f"Total electrical energy: {total_electrical_energy:.1f} kWh"),
        html.Div(f"SPF:                     {spf:.1f}"),
        html.Div(f"Heat Pump Power:         {hd.heat_pump_size(b_type=building_type, b_age=building_year, A=area)} kW")
    ])
    return fig, fig2, df.columns.values, df.columns.values, df.columns.values, df.columns.values

def fetch_data(start_date,end_date,zip_code):
    if start_date and end_date and zip_code:
        start_date_object = datetime.fromisoformat(start_date)
        end_date_object = datetime.fromisoformat(end_date)
        df = datasource.fetch_all(country_code='DE', zip_code=zip_code, start=start_date_object, end=end_date_object,)
    return df

# Run the app
if __name__ == '__main__':
    app.run_server(debug=False)

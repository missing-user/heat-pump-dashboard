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

import datasource
from datetime import datetime, date
import numpy as np

from joblib import Memory
memory = Memory("cache", verbose=0)

pio.templates.default = "plotly_white"

# Initialize the Dash app
app = dash.Dash(__name__)

# Define the layout of the app
app.layout = html.Div([
    html.Div(children=[
        html.Label('Enter location for weather data:'),
        html.Label("Zip Code"),
        dcc.Input(id="zip-input", type="number", value=80333, placeholder="Enter a Zip Code", debounce=True, persistence=True),
        html.Label('Pick date range for simulation'),
        dcc.DatePickerRange(
            id='weather-date-picker-range',
            # TODO: check allowed date range
            min_date_allowed=date(2015, 1, 1),
            max_date_allowed=date(2022, 12, 31),
            initial_visible_month=date(2021, 1, 1),
            start_date=date(2021,1,1),
            end_date=date(2021, 12, 31),
            updatemode='bothdates', persistence=True
        ),
        html.Div(id='selected-date'),
        html.Label('Select building type'),
        dcc.Dropdown(
            id='building-dropdown',
            options=hd.tab_heat_demand["building_type"],
            value=hd.tab_heat_demand.iloc[0,0], persistence=True
        ),
        dcc.Dropdown(
            id='building-year-dropdown',
            options=hd.tab_heat_demand.columns[1:],
            value=hd.tab_heat_demand.columns[3], persistence=True
        ),
        dcc.Dropdown(id="family-type-dropdown",
                     options=[{"label":l,"value": v}for l,v in zip(el.list_readable_electricity_profiles(), el.list_electricity_profiles())],
                     value=el.list_electricity_profiles()[0],persistence=True),

        dcc.Input(id='area',min=1,value=120,type='number', placeholder="Enter area", debounce=True,persistence=True),
        dcc.Slider(id="vorlauftemp-slider", min=35, max=80, value=35, marks={20:"20°C", 50:"50°C", 80:"80°C"},persistence=True),
        html.Label('Select model for heat pump'),

        dcc.Dropdown(
            id='heatpump-model',
            options=[
                {'label': 'Carnot', 'value': 'Carnot'},
                {'label': 'sophisticated', 'value': 'soph'},
            ],
            value='Carnot',persistence=True
        ),
        html.Div(id='selected-heat-pump-model'),
        dcc.Store(id='data'),
        html.Br(),
        dcc.Dropdown(id='plot1-quantity', multi=True, value="T_outside [°C]", placeholder="(mandatory) Select (multiple) y-Value(s)",persistence=True),
        dcc.Dropdown(id='plot2-quantity', multi=True, value="T_outside [°C]", placeholder="(mandatory) Select (multiple) y-Value(s)",persistence=True),
        html.Div([html.Label("Plot 1 Style: "), dcc.RadioItems(["line", "bar"], "line", id="plot1-style", style={"display" : "inline-block"})]),
        html.Div([html.Label("Plot 2 Style: "), dcc.RadioItems(["line", "bar"], "line", id="plot2-style", style={"display" : "inline-block"})]),
        ], style={'width': '300px'}),

    html.Div(children=[
        html.Div(children=[
            html.Div(children=[

            ], style={'display':'inline-block', 'width':'40%'}),
        ]),
        dcc.Loading(dcc.Graph(id='plot1')),
        dcc.Loading(dcc.Graph(id='plot2')),
        dcc.Loading(dcc.Graph(id='plot3')),
        html.H2('Total emissions:'),
        html.Div(id='total-emissions'),
     ], style={'width': '100%'})
], style = {'display':'flex'})



@callback(
    Output('data','data'),
    Output('total-emissions','children'),
    Output('plot1-quantity','options'),
    Output('plot2-quantity','options'),

    Input('zip-input', 'value'),
    Input('weather-date-picker-range', 'start_date'),
    Input('weather-date-picker-range', 'end_date'),
    Input('building-dropdown','value'),
    Input('building-year-dropdown','value'),
    Input("family-type-dropdown", "value"),
    Input('area', 'value'),
    Input("vorlauftemp-slider", "value"),
    Input('heatpump-model','value'),
    )
def update_dashboard(zip_code, start_date, end_date, building_type, building_year, family_type, area, vorlauf_temp, model):
    ctx = dash.callback_context

    # fetch data
    df = fetch_data(start_date,end_date,zip_code)
    df = el.load_el_profile(df, family_type)
    # compute P and electrical Power
    df = heatings.compute_cop(df,model,vorlauf_temp)
    #df = hd.heat_demand(df, b_type=building_type, b_age=building_year, A=area)
    df = hd.simulate(df, b_type=building_type, b_age=building_year, A=area)
    df = heatings.compute_P_electrical(df)
    df = heatings.gas_heating(df)
    df = heatings.oil_heating(df)


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
        html.Div(f"Heat Pump Power:         {hd.heat_pump_size(b_type=building_type, b_age=building_year, A=area)} kW")
    ])

    return {"data-frame": df.reset_index().to_dict("records")}, fig2, df.columns.values, df.columns.values

@app.callback(
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
    df = pd.DataFrame(df_json["data-frame"]).set_index("index")

    fig = px.line(df,y=y1) if s1 == 'line' else px.histogram(df, x=df.index, y=y1).update_traces(xbins_size="M1")
    fig2 = px.line(df,y=y2) if s2 == 'line' else px.histogram(df, x=df.index, y=y2).update_traces(xbins_size="M1")
    # generate plots
    # fig = make_subplots(rows=2, cols=2, shared_xaxes=True).update_layout(height=900)
    # if s1 == 'line':
    #     fig.add_trace(px.line(df,y=y1).data[0], row=1, col=1)
    # elif s1 == 'bar':
    #     fig.add_trace(px.histogram(df, x=df.index, y=y1).update_traces(xbins_size="M1").data[0], row=1, col=1)

    # if s2 == 'line':
    #     fig.add_trace(px.line(df,y=y2).data[0], row=1, col=2)
    # elif s2 == 'bar':
    #     fig.add_trace(px.histogram(df, x=df.index, y=y2).update_traces(xbins_size="M1").data[0], row=1, col=2)

    # if s3 == 'line':
    #     fig.add_trace(px.line(df,y=y3).data[0], row=2, col=1)
    # elif s3 == 'bar':
    #     fig.add_trace(px.histogram(df, x=df.index, y=y3).update_traces(xbins_size="M1").data[0], row=2, col=1)

    # if s4 == 'line':
    #     fig.add_trace(px.line(df,y=y4).data[0], row=2, col=2)
    # elif s4 == 'bar':
    #     fig.add_trace(px.histogram(df, x=df.index, y=y4).update_traces(xbins_size="M1").data[0], row=2, col=2)
    
    # Add y axis labels
    # fig.update_yaxes(title_text=y1, row=1, col=1)
    # fig.update_yaxes(title_text=y2, row=1, col=2)
    # fig.update_yaxes(title_text=y3, row=2, col=1)
    # fig.update_yaxes(title_text=y4, row=2, col=2)

    fig3 = px.line(df, y=['Oil heating emissions [kg CO2eq]',
                          'Gas heating emissions [kg CO2eq]',
                          'heat pump emissions [kg CO2eq]'])
    
    marks = df['heat pump emissions [kg CO2eq]'] > df['Gas heating emissions [kg CO2eq]']
    marks = marks.loc[marks.diff() != 0]
    for i in range(len(marks)):
        if marks.iat[i] > 0:
            fig3.add_vrect(x0=marks.index[i], x1=marks.index[i+1], fillcolor="red", opacity=0.25, layer="below", line_width=0)

    return fig, fig2, fig3


#@memory.cache
def fetch_data(start_date,end_date,zip_code):
    if start_date and end_date and zip_code:
        start_date_object = datetime.fromisoformat(start_date)
        end_date_object = datetime.fromisoformat(end_date)
        df = datasource.fetch_all(country_code='DE', zip_code=zip_code, start=start_date_object, end=end_date_object,)
    return df

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)

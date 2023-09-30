import dash
from dash import dcc, html, Input, Output, callback
import plotly.express as px
import pandas as pd

dash.register_page(__name__)

# Define the layout of the app
layout = html.Div([
        html.H2('Total emissions:'),
        dcc.Loading(html.Div(id='total-emissions')),
        dcc.Loading(dcc.Graph(id='plot1')),
        dcc.Loading(dcc.Graph(id='plot2')),
        dcc.Loading(dcc.Graph(id='plot3')),
     ])

@callback(
    Output('total-emissions','children'),    
    Input('data','data'),
  )
def show_summaries(df_json):
    df = pd.DataFrame(df_json["data-frame"]["data"], df_json["data-frame"]["index"], df_json["data-frame"]["columns"]).set_index("index")
    
    # compute total quantities
    df["heat pump emissions [kg CO2eq]"] = df["P_el heat pump [kW]"] * df["Intensity [g CO2eq/kWh]"] * 1e-3
    total_emission_hp = df["heat pump emissions [kg CO2eq]"].sum()
    total_emission_gas = df["Gas heating emissions [kg CO2eq]"].sum()
    total_emission_oil = df["Oil heating emissions [kg CO2eq]"].sum()
    total_heat = df['Q_dot_demand [kW]'].sum()
    total_electrical_energy_hp = df['P_el heat pump [kW]'].sum()
    spf = total_heat/total_electrical_energy_hp

    # display total quantities
    fig2 = html.Div(children=[
        html.Div(f"Total heat demand:                   {total_heat:.1f} kWh"),
        html.Div(f"Total electrical energy (heat pump): {total_electrical_energy_hp:.1f} kWh"),
        html.Div(f"Total CO2 emissions (heat pump):     {total_emission_hp:.1f} kg CO2eq"),
        html.Div(f"Total CO2 emissions (oil heating):   {total_emission_oil:.1f} kg CO2eq"),
        html.Div(f"Total CO2 emissions (gas heating):   {total_emission_gas:.1f} kg CO2eq"),
        html.Div(f"Seasonal performance factor:         {spf:.1f}"),
        html.Div(f"Suggested heat pump power:         {df_json['heat-pump-power']:.1f} kW")
    ])

    return fig2

@callback(
    Output('plot1','figure'),

    Input('data','data'),
    Input('plot1-quantity','value'),
    Input('plot1-style','value'),
    prevent_initial_call=True)
def draw_plot(df_json, y, s):
    
    df = pd.DataFrame(df_json["data-frame"]["data"], df_json["data-frame"]["index"], df_json["data-frame"]["columns"]).set_index("index")
    if s == 'line':
        fig = px.line(df, y=y)
    elif s == 'bar':
        fig = px.histogram(df, x=df.index, y=y).update_traces(xbins_size="M1")
    else:
        fig = px.area(df, y=y)
    return fig


@callback(
    Output('plot2', 'figure'),

    Input('data', 'data'),
    Input('plot2-quantity', 'value'),
    Input('plot2-style', 'value'),
    prevent_initial_call=True)
def draw_plot2(df_json, y, s):
    df = pd.DataFrame(df_json["data-frame"]["data"], df_json["data-frame"]["index"],
                      df_json["data-frame"]["columns"]).set_index("index")
    if s == 'line':
        fig = px.line(df, y=y)
    elif s == 'bar':
        fig = px.histogram(df, x=df.index, y=y).update_traces(xbins_size="M1")
    else:
        fig = px.area(df, y=y)
    return fig


@callback(
    Output('plot3', 'figure'),

    Input('data', 'data'),
    prevent_initial_call=True)
def draw_plot3(df_json):
    df = pd.DataFrame(df_json["data-frame"]["data"], df_json["data-frame"]["index"],
                      df_json["data-frame"]["columns"]).set_index("index")

    marks = df['heat pump emissions [kg CO2eq]'].rolling(7*24, center=True).mean() > df['Gas heating emissions [kg CO2eq]'].rolling(7*24).mean()
    marks = marks.loc[marks.diff() != 0]

    fig3 = px.line(df, y=['Oil heating emissions [kg CO2eq]',
                          'Gas heating emissions [kg CO2eq]',
                          'heat pump emissions [kg CO2eq]'], 
                    title=("CO2 emissions" + ("" if len(marks)<=30 else " (could not display all marks)")))

    for i in range(min(len(marks) - 1, 30)):
        if marks.iat[i] > 0:
            fig3.add_vrect(x0=marks.index[i], x1=marks.index[i + 1], fillcolor="red", opacity=0.25, layer="below",
                           line_width=0)

    return fig3

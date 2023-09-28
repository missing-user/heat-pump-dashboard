import dash
from dash import dcc, html, Input, Output, State, callback
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import dash_dangerously_set_inner_html

dash.register_page(__name__)

# Define the layout of the app
layout = html.Div([
  html.Div([
    html.Div(id="total-emissions2"),
    dcc.Loading(dcc.Graph(id='gauge-heatpump')),
    dcc.Loading(dcc.Graph(id='gauge-oil')),
    dcc.Loading(dcc.Graph(id='gauge-gas')), 
  ], className="grid-container halves"),

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
      value=df["heat pump emissions [kg CO2eq]"].sum()*1e3/df["Q_dot_supplied [kW]"].sum(),
      mode="gauge+number",
      title={'text': "Specific CO2-emissions<br>[g CO2/kWh]"},
      delta={'reference': 247, },
      gauge={'axis': {'range': [None, 700], 'tickvals': [0, 100,200, 247,300,400,500,600, 700], 'ticktext': ["0", "100", "200", "AVG", "300", "400", "500", "600", "700"]},
             'bar': {'color': "rgba(255, 255, 255, 0.7)"},
             'steps': [
                 {'range': [0, 247], 'color': "green"},
                 {'range': [248, 700], 'color': "red"},
             ],
             'threshold': {'line': {'color': "gray", 'width': 2}, 'thickness': 1, 'value': 247, }
             }
  ))

  gauge_2 = go.Figure(go.Indicator(
      domain={'x': [0, 1], 'y': [0, 1]},
      value=df["Q_dot_supplied [kW]"].sum()/df_json["area"],
      mode="gauge+number",
      title={'text': "Energy Efficiency<br>[kWh/m2 year]"},
      delta={'reference': 170, },
      gauge={'axis': {'range': [None, 300], 'tickvals': [15, 40, 62.5, 87.5, 115, 145, 170, 180, 225, 275],
                    'ticktext': ["A+", "A", "B", "C", "D", "E","AVG", "F", "G", "H" ],
             'ticks': ""},
             'bar': {'color': "rgba(255, 255, 255, 0.7)"},
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
             'threshold': {'line': {'color': "gray", 'width': 2}, 'thickness': 1, 'value': 170, }
             }
  ))
  barchart = go.Figure(go.Bar(
    x=["Oil", "Gas", "Pellet", "Heat pump"],
    y=[df["Oil heating emissions [kg CO2eq]"].sum(), 
       df["Gas heating emissions [kg CO2eq]"].sum(), 
       df["Pellet heating emissions [kg CO2eq]"].sum(),
       df["heat pump emissions [kg CO2eq]"].sum()],
       )).update_layout(title_text="Annual CO2 emissions [kg CO2eq]", yaxis_title="kg CO2eq",height=600)
  
  return gauge, gauge_2 , barchart



@callback(
    Output('total-emissions2','children'),    
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

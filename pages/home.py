import dash
from dash import html, dcc
import plotly.graph_objects as go
import dash_dangerously_set_inner_html

dash.register_page(__name__, path='/')

fig = go.Figure(go.Sankey(
    arrangement = "snap",
    node = {
        "label": ["Location", "Year", "Building Age", "Building Type", "Floor Area", "Family Type", #5
                  "Weather", "Insulation",#7
                  "Temperature", "Solar Radiation", "Electricity Usage","Body Heat",#11
                  "Heat Losses", "Heat Gains", "Ventilation",#ends with 14
                  "Room Temperature", "Heat Supply",#16
                  "Heat Pump Type","Heat Pump Model",#18
                  "Heat Pump Electricity Usage",
                  "CO2 Emissions", "Electricity Mix"#21
                  ],
        "pad":20},
    link = {
        "arrowlen":10,
        "source": [0,1,2,3,4,5,5,10,4,
                   6,6,14,11,
                   8,9,7,
                   12,13,
                   0,1,21,19,
                   17,18,15,16,18,19],
        "target": [6,6,7,7,7,11,10,13,14,
                   8,9,12,13,
                   12,13,12,
                   15,15,
                   21,21,19,20,
                   18,16,18,13,19,20],
        "value": [1,1,1,1,1,1,1,1,1,
                1,1,1,1,
                1,1,3, 
                5,4, # Heat demand
                1,1,2,12,2,1,9,1,10],}))

fig.update_layout(title_text="Heat Pump Simulation Components", font_size=14, height=500)

layout = [
  dash_dangerously_set_inner_html.DangerouslySetInnerHTML('''
<style> .main-container {
    grid-template-columns: 0 1fr;
  }
  .input-container{
  visibility: collapse;
  display: none !important;
}</style>'''),
    html.Div([
      html.Div([
        html.H1('Carbon Emissions of Heat Pumps'),
        html.P('The Simulation Tool for Calculating CO2 Emissions of Heat Pumps is a powerful software application designed to assist in the evaluation and analysis of the environmental impact of heat pump systems. Heat pumps are energy-efficient heating devices widely used in residential settings. This tool aims to provide users with valuable insights into the carbon dioxide (CO2) emissions associated with the operation of heat pumps, helping them make informed decisions to reduce their carbon footprint and contribute to a more sustainable future. For premium users only, this tool provides more detailed insights, overviews, and offers different levels of customization that take your environmental analysis to the next level. '),
        html.Br(),
        html.B("Developed at Ferienakademie 2023")
        #html.Img(src='assets/TitleImage.png', className="u-full-width"),
      ]),
      html.Div([
        html.H1('How it works'),
        dcc.Graph(figure=fig)
      ]),
              
    html.Div([
      html.H3('Basic Plan'),

      html.Ul([
        html.Li([html.B("Heat Pump Modeling:"), " Input individual parameters related to building age, size, and heat pump system."]),
        html.Li([html.B("Energy Consumption Analysis:"), " Breakdown energy consumption associated with heat pump operation. Visualize how much energy their heat pump consumes over one year."]),
        html.Li([html.B("CO2 Emissions Estimation:"), " By considering the energy consumption data and the selected geographical location, the tool calculates the CO2 emissions produced by the heat pump's operation. It takes into account factors such as electricity source (renewable, fossil fuels), heating demand, and the overall energy efficiency of the heat pump."]),
        html.Li([html.B("Comparison:"), " Compare emissions of different standard heating systems (oil, gas, and pellets) to a heat pump system."]),
        html.Li([html.B("Categorization:"), " Results are compared to average values for German households."]),
        html.Li(html.B("Ad supported"))
    ])
    ]),

    html.Div([
      html.H3('Professional Plan'),
      html.Ul([
        html.Li([html.B("Deeper insight")]),
        html.Li(["More input parameters offer high customizability (window area, target temperature, and more)"]),
        html.Li(["Plots of every parameter over individual time intervals possible"]),
        html.Li(["Choose plot styles"]),
        html.Li([html.B("Advanced settings")]),
        html.Li(["Model heat losses due to ventilation"]),
        html.Li(["Set heat gains"]),
        html.Li(["Set electrical energy mix"]),
        html.Li(["Set heating control strategy"]),
        html.Li(["Unlimited selection of >6000 heat pump models"]),
        html.Li(html.B("No ads"))
    ])
    ]),
              
    html.A("Free",href="./captcha", className="button"),
    html.A("Premium (Only 49.99 $/month)",href="./academic", className="button button-primary"),
  ], className="grid-container halves"),
  html.Div(style={"height":"20em"})
]
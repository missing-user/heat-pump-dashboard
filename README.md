# Heat pumps

## What we want to do?

We want to build a dashboard to visualize the CO2 emissions of heat pumps

- Users gain insight about how their own heat pump setup
- Users can experiment how different setups would decrease their carbon footprint
- Suggestions how it could be optimized (e.g. optimal Vorlauftemperatur, storage size, etc.)
- Insight about heat pump performance in different geographic regions
- Scenario analysis of heat pump performance with future weather + energy mix predictions (up to 2050)
- Comparisons to other heating technologies (primary energy demand, CO2 emissions, costs)

- Would a higher percentage in solar electricity mix have changed CO2 emissions significantly?
- Does the temporal dependence make a difference

## How we want to do it

- Model the demand of different house types (domestic hot water usage, space heating) for different sizes, habitants, preferences (e.g. Warmduscher)
- 1. Standard demand profiles (DIN Norm)
  2. Model a more accurate temperature-demand-relationship based on synthetic data from Fraunhofer ISE
- Model the electricity usage of the heat pump based on current demand
- 1. Carnot cycle
  2. Interpolated datasheet reference values
  3. Fancy heat pump library?
- Model energy storage (hot water)
- 1. Naive storage of excess energy with rate and storage limits
  2. Model losses during storage
  3. Simple thresholding algorithm to optimize storage
- Model the CO2 intensity of available electricity from the datasources
- Interactive Plotly dashboard to visualize the results
- 1. Selectable User parameters as input -> Graphs of CO2 emissions over time
  2. KPIs like coefficient of performance (COP) 
  2. Visualization of saved CO2/cost/energy
  3. Colored map of heat pump efficiency for geographic locations
  4. Different Variants for global insight and single household
  5. 
- Integration with Solar team for PV production

## Documentation of sources
Carbon intensity factors:
Hydro pump storage: according to http://dse.univr.it/home/workingpapers/wp2021n8.pdf effective footprint is 31% above grid average due to round trip losses



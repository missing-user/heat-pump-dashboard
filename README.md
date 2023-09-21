# Heat pumps

## What we want to do?

We want to build a dashboard to visualize the CO2 emissions of heat pumps


- Users gain insight about how their own heat pump setup
- Suggestions how it could be optimized (e.g. optimal Vorlauftemperatur, storage size, etc.)
- Insight about heat pump performance in different geographic regions
- Insight about cost of such a setup

## How we want to do it

- Model the demand of different house types (Direct hot water usage, heating needs)
- Build a simplified model of
- 1. Demand (Heizlastprofil), initially tabular, scaled to different house sizes
  2. Heat pump (initially e.g. Carnot cycle)
  3. Energy storage (including losses, simple energy management)
  4. Electricity grid CO2 intensity
- Interactive Plotly dashboard to visualize the results
- Integration with Solar team for PV production
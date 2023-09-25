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
specific heat demand:   http://www.bosy-online.de/heizlastberechnung_nach_din_en_12831.htm
                        https://www.waermepumpe.de/normen-technik/heizlastrechner/
                        https://www.npro.energy/main/de/load-profiles/heat-load-and-demand
Heating limit temperature: https://www.effizienzhaus-online.de/lexikon/heizgrenztemperatur/


3000 L Heizoel
30000 kWh Waermebedarf pro Jahr

Berater: 55000 kWh Waermebedarf


Electricity stats for Germany: https://www.smard.de/en/downloadcenter/download-market-data/?downloadAttributes=%7B%22selectedCategory%22:1,%22selectedSubCategory%22:1,%22selectedRegion%22:false,%22selectedFileType%22:%22CSV%22,%22from%22:1514761200000,%22to%22:1672613999999%7D


Annahme: - 95% von allem elektrischen Verbrauch wird als waerme im Gebaeude frei.
- Sonneneinstrahlung durch die Fenster wird ebenfalls als Waerme gewertet. Fenster sind 1/3 Ost, 1/3 West 1/3 Sud (Einerseits nehmen wir keine Nord Fenster an, andererseits werden auch Dachfenster als vertikale Fenster gewertet und Uebertragungen durch Dach und Waende vernachlassigt)
- Wohnflaeche zu Wand+Dachflaeche ist etwa Faktor 3 (Faustregel und Bestaetigt anhand von Ullis Haus Werten)
- Wir verwenden den Wert von Ullis Haus runtergerechnet auf die Wohnflaeche. Faktoren fur spezifische Wearmekapazitaet (from 140 to 315 kJ m-2 K-1) aus https://www.sciencedirect.com/science/article/pii/S2214509522005551

We simulate closing the blinds when it is too hot, ventilation losses, losses through walls, windows etc., solar radiation gains, gains through electrical appliances and habitants.
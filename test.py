import pandas as pd
import plotly.express as px
import numpy as np

# constants
T_VL = 35
degradation = .5

def plot_by_col(df_filtered, y_plot):
    '''
    Helper function to plot one column of provided DataFrame.
    :param df_filtered:
    :param y_plot:
    :return: None
    '''
    fig = px.line(df_filtered,x='time',y=y_plot,color='day', facet_col="month", facet_col_wrap=4)
    fig.update_xaxes(
        title='Time',
        tickformat='%H:%M:%S',  # Format time as hours:minutes:seconds
        tickangle=45,  # Rotate x-axis labels for better readability
    )
    fig.update_yaxes(title=y_plot)
    fig.show()

# load data
water_df = pd.read_csv("data/heatingload/domestic_hot_water/synPRO_passive_single_family_house.dat", comment="#", sep=";")
df = pd.read_csv("data/heatingload/room_heating/synPRO_passive_single_family_house.dat", comment="#", sep=";")
df = pd.concat([df,water_df['Q_dhw']],axis=1)

# reformat weather DF
weather_df = pd.read_csv('data/weather/DWD/TRY_488641091042/TRY2015_488641091042_Jahr.dat',comment='#', delim_whitespace=True, encoding_errors='ignore',skip_blank_lines=True,skiprows=32)
weather_df.dropna(inplace=True)
weather_df.reset_index(inplace=True,drop=True)
weather_df['year'] = 2021
weather_df.rename(columns={'DD':'day','MM':'month','HH':'hour'}, inplace=True)
weather_df['hour'] = weather_df['hour'] - 1
weather_df['datetime'] = pd.to_datetime(weather_df[['year', 'month', 'day', 'hour']])
weather_df['time'] = weather_df['datetime'].dt.time

# Convert the 'unixtimestamp' column to datetime and extract components
df['datetime'] = pd.to_datetime(df['unixtimestamp'], unit='s')
df['year'] = df['datetime'].dt.year
df['month'] = df['datetime'].dt.month
df['day'] = df['datetime'].dt.day
df['hour'] = df['datetime'].dt.hour
df['minute'] = df['datetime'].dt.minute
df['second'] = df['datetime'].dt.second
df['time'] = df['datetime'].dt.time

# convert W to kW
df.loc[:,'Q_htg'] = df.loc[:,'Q_htg'] * 0.001
df.loc[:,'Q_dhw'] = df.loc[:,'Q_dhw'] * 0.001

# restrict values to 2021
df = df[df.year == 2021]
df.reset_index(drop=True,inplace=True)

df_filtered = df[df.minute == 0].copy()
df_15 = df[df.minute == 15]
df_30 = df[df.minute == 30]
df_45 = df[df.minute == 45]
df_filtered.reset_index(drop=True, inplace=True)
df_15.reset_index(drop=True, inplace=True)
df_30.reset_index(drop=True, inplace=True)
df_45.reset_index(drop=True, inplace=True)

# compute averaged heat demand and add temperature vaues
df_filtered.loc[:,'Q_htg_avg'] = (df_filtered.loc[:,'Q_htg'] + df_15.loc[:,'Q_htg'] + df_30.loc[:,'Q_htg'] + df_45.loc[:,'Q_htg'])/4
df_filtered.loc[:,'Q_dhw_avg'] = (df_filtered.loc[:,'Q_dhw'] + df_15.loc[:,'Q_dhw'] + df_30.loc[:,'Q_dhw'] + df_45.loc[:,'Q_dhw'])/4
df_filtered.reset_index(drop=True, inplace=True)
df_filtered = pd.concat([df_filtered,weather_df['t']],axis=1)

# compute COP and P_el
df_filtered.loc[:,'COP'] = degradation * (273.15 + T_VL)/(T_VL - df_filtered.loc[:,'t'])
df_filtered.loc[:,'P_el'] = df_filtered.loc[:,'Q_htg_avg'] / df_filtered.loc[:,'COP']
df_filtered.loc[df_filtered['Q_htg_avg'] == 0,'COP'] = np.nan
df_filtered.loc[:,'z'] = 435.
df_filtered.loc[:,'Z'] = df_filtered.loc[:,'z'] * df_filtered.loc[:,'P_el'] * 0.001

# print details
print('Total CO2 emissions heat pump: ', df_filtered['Z'].sum(), ' kg.')
print('Total electrical Energy: ', df_filtered['P_el'].sum(), 'kWh.')
print('Total heat demand: ', df_filtered['Q_htg_avg'].sum(), 'kWh.')
print('SPF: ', df_filtered['Q_htg_avg'].sum()/df_filtered['P_el'].sum())
print('Total CO2 emissions gas heating: ', df_filtered['Q_htg_avg'].sum() / 0.9 * 0.2, ' kg.')

# Plotting
plot_by_col(df_filtered, 'COP')
plot_by_col(df_filtered,'Z')

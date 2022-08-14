import os
import streamlit as st
import pandas as pd
import pydeck as pdk
import holoviews as hv
import hvplot.pandas
from pathlib import Path
import requests
import nasdaqdatalink
import shutil
import pandas_ta as ta
from MCForecastTools import MCSimulation
from datetime import datetime
import realestate_data as red
import realestate_stats as res
import macd

import matplotlib.pyplot as plt
import numpy as np
import pytz


NASDAQ_DATA_LINK_API_KEY = st.secrets['NASDAQ_DATA_LINK_API_KEY']
# from application.app.folder.file import func_name

st.set_page_config(layout="wide")

# Global variables
region_df = pd.DataFrame()
zillow_df = pd.DataFrame()
county_coordinates_df = pd.DataFrame()
master_df = pd.DataFrame()

#
# Load data
#
region_df = red.load_zillow_region_data()
zillow_df = red.load_zillow_sales_data(region_df)
county_coordinates_df = red.load_county_coordinates()


#
# Clean and Merge Data
#
# Merge the Region dataframe with the Zillow sales data
zillow_merge_df = pd.merge(region_df, zillow_df, on=['region_id'])

# Rename county_x and state_x so that we can return a clean dataframe
zillow_merge_df.rename(
    columns={'county_x': 'county', 'state_x': 'state'}, inplace=True)

# Drop unnecessary columns
zillow_merge_df = zillow_merge_df[[
    'region_id', 'county', 'state', 'date', 'value']]

# Check the merged Zillow data
zillow_merge_df.head()

# Merge the Zillow data and county coordinates data.
master_df = pd.merge(zillow_merge_df, county_coordinates_df,
                     on=['county', 'state'])

master_df['date'] = pd.to_datetime(master_df['date'])
# st.write(master_df.head())

# Set up containers
header = st.container()
avg_home_sales = st.container()
pct_change_sales = st.container()
macd_container = st.container()
montecarlo = st.container()

with header:
    st.title('Realestate of Mind')

with avg_home_sales:

    st.subheader("Average Home Sales")

    min_year = st.slider('Starting Year', 1997, 2022, 1997)
    max_year = st.slider('Ending Year', 1997, 2022, 2022)

    # Display average home sales per county
    county_mean_df = res.get_county_df_with_mean(
        master_df, str(min_year) + '-01-01', str(max_year) + '-01-01')

    # Divide price by 1000 so that it looks better on map.
    county_mean_df["value"] = county_mean_df["value"] / 1000

    # Tooltip to display county data
    tooltip = {
        "html": "County: {county}</br> State: {state}</br>  Mean Sales: ${value}</br> " +
        "Latitude: {latitude} </br> Longitude: {longitude} </br> "
    }

    # Define a layer to display on a map
    layer = pdk.Layer(
        "ScatterplotLayer",
        county_mean_df,
        pickable=True,
        opacity=0.8,
        stroked=True,
        filled=True,
        radius_scale=20,
        radius_min_pixels=1,
        radius_max_pixels=100,
        line_width_min_pixels=1,
        get_position='[longitude, latitude]',
        get_radius="value",
        get_fill_color=[255, 140, 0],
        get_line_color=[0, 0, 0],
    )

    # Set the viewport location
    view_state = pdk.ViewState(
        latitude=30.00,
        longitude=-99,
        zoom=4.1,
        pitch=50,
        height=700,
        width=1200,
    )

    # Render
    r = pdk.Deck(
        layers=[layer],
        initial_view_state=view_state,
        tooltip=tooltip)

    col1, col2 = st.columns((3, 1))
    # col1.write(hv.render(county_mean_plot, backend='bokeh'))
    col1.write(r)
    col2.dataframe(county_mean_df, 700, 700)


with pct_change_sales:
    st.subheader("Percent Change in Home Sales")

    # Display percent change per county
    county_pct_change_df = res.get_county_df_with_cum_pct_change(
        master_df, '2010-01-01', '2022-08-01')

    # Not sure why county_pct_change is missing the longitude and latitude, but I have to add it back :(
    merge_county_pct_change_df = pd.merge(
        county_pct_change_df, county_coordinates_df, on=['county', 'state'])

    # Drop unnecessary columns
    merge_county_pct_change_df = merge_county_pct_change_df[[
        'region_id', 'county', 'state', 'latitude', 'longitude', 'cum_pct_ch']]

    # Tooltip to display county data
    tooltip = {
        "html": "County: {county}</br> State: {state}</br>  Pct Change: {cum_pct_ch}%</br> " +
        "Latitude: {latitude} </br> Longitude: {longitude} </br> "
    }

    # Define a layer to display on a map
    layer = pdk.Layer(
        "ScatterplotLayer",
        merge_county_pct_change_df,
        pickable=True,
        opacity=0.8,
        stroked=True,
        filled=True,
        radius_scale=100,
        radius_min_pixels=1,
        radius_max_pixels=100,
        line_width_min_pixels=1,
        get_position='[longitude, latitude]',
        get_radius="cum_pct_ch",
        get_fill_color=[255, 140, 0],
        get_line_color=[0, 0, 0],
    )

    # Set the viewport location
    view_state = pdk.ViewState(
        latitude=30.00,
        longitude=-99,
        zoom=4.1,
        pitch=50,
        height=700,
        width=1200,
    )

    # Render
    r = pdk.Deck(
        layers=[layer],
        initial_view_state=view_state,
        tooltip=tooltip)

    col1, col2 = st.columns((3, 1))
    # col1.write(hv.render(county_mean_plot, backend='bokeh'))
    col1.write(r)
    col2.dataframe(merge_county_pct_change_df, 1000, 700)


with macd_container:
    st.subheader("MAC/D")
    st.write("Please enter the number of months below:")
    col1, col2, col3 = st.columns(3)
    fast = col1.text_input("Fast EMA", 6)
    slow = col2.text_input("Slow EMA", 12)
    signal = col3.text_input("Signal", 4)

    fast = int(fast)
    slow = int(slow)
    signal = int(signal)

    # Creates a DataFrame using only the columns we are interested in
    filtered_df = master_df[['date', 'county', 'state', 'value']]

    filtered_df['county'] = filtered_df['county'] + ", " + filtered_df['state']
    drop_cols = ['state']
    filtered_df = filtered_df.drop(columns=drop_cols)

    # Figured out the change in number of counties was messing up the charts
    exploratory_df = filtered_df.groupby('date').count()

    # Create new DataFrame with summed county markets to represent the entire nation
    nationwide_df = filtered_df.groupby(
        filtered_df['date']).agg({'value': 'sum'})

    # Must divide 'values' by number of counties that make up said value so data isn't skewed by county number
    nationwide_df['avg'] = nationwide_df['value']/exploratory_df['county']

    # Use Nationwide MACD funtion
    nationwide_macd_df = macd.get_nationwide_macd(
        nationwide_df, fast, slow, signal)

    # Graph
    plotting_macd = nationwide_macd_df.hvplot(
        title='US Housing Market Momentum', ylabel='Momentum')
    st.write(hv.render(plotting_macd, backend='bokeh'))

    county_list = filtered_df['county'].unique()
    # st.write(county_list)

    col1, col2 = st.columns(2)
    county = col2.selectbox(
        'Counties', county_list)

    # Use County MACD
    county_macd_df = macd.get_county_macd(
        filtered_df, county, fast, slow, signal)

    st.write('You selected:', county)

    # Graph
    plotting_county_macd = county_macd_df.hvplot(
        title='MAC/D by County', groupby='county', x='date', ylabel='Momentum')
    col1.write(hv.render(plotting_county_macd, backend='bokeh'))

with montecarlo:
    st.header("Monte Carlo Simulations")
    monte_carlo_county_list = filtered_df['county'].unique()
    options = st.multiselect(
        'Choose list of counties that you would like to get simulations for',
        monte_carlo_county_list,
        [])

    start_date = '2015-01-31'
    end_date = '2022-06-30'
    mc_df = filtered_df
    monte_carlo_options = []
    for group_loc in options:
        df_temp = mc_df.loc[(mc_df['county'] == group_loc) & (
            mc_df['date'] <= end_date) & (mc_df['date'] >= start_date)]
        monte_carlo_options.append(
            df_temp.drop('county', axis=1).reset_index())

    try:
        monte_carlo_df = pd.concat(monte_carlo_options, axis=1, keys=options)
        calculate_monte_carlo_results = st.button("Get Monte Carlo Results")
        if calculate_monte_carlo_results:
            mc_sim = MCSimulation(monte_carlo_df, "", 1000, 120)
            plt_sim = mc_sim.calc_cumulative_return()
            st.write("Cumulative Returns")
            st.write(plt_sim)
            st.write("120 Month Monte Carlo Sim(PCT Return)")
            st.line_chart(plt_sim)

            hist_data_arr = np.array(plt_sim.iloc[-1, :])
            fig, ax = plt.subplots()
            ax.hist(hist_data_arr, bins=10)
            confidence_interval = plt_sim.iloc[-1,
                                               :].quantile(q=[0.025, 0.975])

            fig.add_artist(plt_sim.iloc[-1, :].plot(kind='hist', bins=10, density=True,
                           title="Plot Distribution").axvline(confidence_interval.iloc[0], color='red'))
            fig.add_artist(plt_sim.iloc[-1, :].plot(kind='hist', bins=10,
                           density=True).axvline(confidence_interval.iloc[1], color='red'))
            st.pyplot(fig)

            st.write("Cumulative Returns Summary over the next 10 years")
            st.write(mc_sim.summarize_cumulative_return())
    except:
        st.write("Please select options")

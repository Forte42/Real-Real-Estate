import os
import streamlit as st
import pandas as pd
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

# Set up containers
header = st.container()
avg_home_sales = st.container()
pct_change_sales = st.container()
macd = st.container()
montecarlo = st.container()

with header:
    st.title('Realestate of Mind')

with avg_home_sales:

    st.subheader("Average Home Sales")

    # Display average home sales per county
    county_mean_df = res.get_county_df_with_mean(
        master_df, '2010-01-01', '2021-12-31')
    # display(county_mean_df.head())

    # Divide price by 1000 so that it looks better on map.
    county_mean_df["value"] = county_mean_df["value"] / 1000

    county_mean_plot = county_mean_df.hvplot.points(
        'longitude',
        'latitude',
        geo=True,
        hover=True,
        hover_cols=['county', 'cum_pct_ch'],
        size='value',
        color='value',
        tiles='OSM',
        height=700,
        width=700,
        title='Average home sales per county from 1/1/2010 to 12/31/2021')

    col1, col2 = st.columns(2)
    col1.write(hv.render(county_mean_plot, backend='bokeh'))
    col2.write(county_mean_df)


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

    pct_change_plot = merge_county_pct_change_df.hvplot.points(
        'longitude',
        'latitude',
        geo=True,
        hover=True,
        hover_cols=['county', 'cum_pct_ch'],
        size='cum_pct_ch',
        color='cum_pct_ch',
        tiles='OSM',
        height=700,
        width=700,
        title='Percent change per county from 1/1/2010 to 12/31/2021')

    col1, col2 = st.columns(2)
    col1.write(hv.render(pct_change_plot, backend='bokeh'))
    col2.write(merge_county_pct_change_df)

with macd:

    st.subheader("MAC/D")


with montecarlo:

    st.subheader("Monte Carlo Simulations")

import os
from turtle import title
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
import macd

import matplotlib.pyplot as plt
import matplotlib.lines as lines
import numpy as np
import altair as alt


# from application.app.folder.file import func_name

NASDAQ_DATA_LINK_API_KEY=st.secrets['NASDAQ_DATA_LINK_API_KEY']

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

    county_mean_plot = county_mean_df.hvplot.points(
        'longitude',
        'latitude',
        geo=True,
        hover=True,
        hover_cols=['county', 'cum_pct_ch'],
        size='value',
        cmap='seismic',
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
        cmap='seismic',
        tiles='OSM',
        height=700,
        width=700,
        title='Percent change per county from 1/1/2010 to 12/31/2021')

    col1, col2 = st.columns(2)
    col1.write(hv.render(pct_change_plot, backend='bokeh'))
    col2.write(merge_county_pct_change_df)


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
        df_temp = mc_df.loc[(mc_df['county']==group_loc) & (mc_df['date'] <= end_date) & (mc_df['date'] >= start_date)]
        monte_carlo_options.append(df_temp.drop('county', axis=1).reset_index())
   
    
    try:   
        monte_carlo_df = pd.concat(monte_carlo_options, axis=1, keys=options)
        calculate_monte_carlo_results = st.button("Get Monte Carlo Results")
        if calculate_monte_carlo_results:
            mc_sim = MCSimulation(monte_carlo_df, "", 1000, 120)
            plt_sim = mc_sim.calc_cumulative_return()
            st.write("Cumulative Returns")
            st.write(plt_sim)
            st.write("120 Month Monte Carlo Sim(PCT Return)")
            st.line_chart(plt_sim, x='Months', y='PCT Return')
          
          
            
            # chart = (
            #         alt.Chart(
            #             data=plt_sim,
            #             title="Your title",
            #         )
            #         .mark_line()
            #         .encode(
            #         x=alt.X("capacity 1", axis=alt.Axis(title="Capacity 1")),
            #             x=alt.X("capacity 2", axis=alt.Axis(title="Capacity 2")),
            #         )
            # )

            # st.altair_chart(chart)
            


            hist_data_arr = np.array(plt_sim.iloc[-1, :])
            fig, ax = plt.subplots()
            ax.hist(hist_data_arr, bins=10)
            confidence_interval = plt_sim.iloc[-1, :].quantile(q=[0.025, 0.975])
        
            fig.add_artist(plt_sim.iloc[-1, :].plot(kind='hist', bins=10,density=True, title="Plot Distribution").axvline(confidence_interval.iloc[0], color='red'))
            fig.add_artist(plt_sim.iloc[-1, :].plot(kind='hist', bins=10,density=True).axvline(confidence_interval.iloc[1], color='red'))
            st.pyplot(fig)

            st.write("Cumulative Returns Summary over the next 10 years")
            st.write(mc_sim.summarize_cumulative_return())
    except:
        st.write("Please select options")
    
    
        


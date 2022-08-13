#!/usr/bin/env python
# coding: utf-8

# In[2]:


# Standard imports. Note: You must pip install nasdaqdatalink first
import os
import pandas as pd
import hvplot.pandas
from pathlib import Path
import requests

# For API Calls
import nasdaqdatalink
# For opening zip folder
import shutil 
# For technical analysis
import pandas_ta as ta

from MCForecastTools import MCSimulation

from datetime import datetime
import realestate_data as red
import realestate_stats as res


# In[3]:


# Linking my API key to .env in the same folder. The key is stored in the folder without any quotations around it 
nasdaqdatalink.read_key(filename=".env")


# # 1. Fetching Data 
# In order to analyze the historical real estate and execute Monte Carlo simulations, we will need to fetch the real estate data from Zillow.    We will fetch the following datasets: 
# - Zillow Region Data - This dataset provides a list of states and counties, along with Zillow 'region_id', which is a unique identifier for that specific region. 
# - Zillow Sales Data - This dataset provides a list of historical sales with 'region_id' as the unique id.
# - Coordinates Data - To display the Zillow sales data on a map, we need to merge it with a dataset that provides coordinates.   However, we couldn't find the county coordinates from Zillow, so we sourced the data from Wikipedia.   We are going to have to merge the data with Zillow based on county and state. 
# 
# ## Fetching Zillow Region Data   
# In this section, we fetch a list region data from Zillow.  The Zillow region data provides a list of states and counties, along with Zillow 'region_id', which is a unique identifier for that specific region. 

# In[4]:


# Using get_regions to retrieve a list of counties
region_df = red.load_zillow_region_data()

# Check data for region_df
#print(region_df.head())
#print(region_df.tail())


# ## Fetching Zillow Sales Data  
# In this section, we fetch Zillow sales data in the form of a CSV file.   The Zillow sales data provides a list of historical sales with 'region_id' as the unique id.   

# In[ ]:


# Load Zillow sales data
zillow_data = red.load_zillow_sales_data(region_df)

# Check the Zillow sales data
#print(zillow_data.head())
#print(zillow_data.tail())


# ## Fetcing Coordinates Data
# We want to display our Zillow sales data on a map.  However, we couldn't find the county coordinates from Zillow, so we sourced the data from Wikipedia.   We are going to have to merge the data with Zillow based on county and state. 

# In[ ]:


# Read in county data with coordinates
county_coordinates_df = red.load_county_coordinates()

# Check the county coordinates data
print(county_coordinates_df.head())


# # 2. Cleaning and Merging Data

# ## Merge the Zillow region and sales data
# Now that we have the Zillow region and sales data, we want to merge the two DataFrames into one DataFrame that contains sales data along with state and county columns.

# In[ ]:


# Merge the Region dataframe with the Zillow sales data
zillow_merge_df = pd.merge(region_df, zillow_data, on=['region_id'])

# Rename county_x and state_x so that we can return a clean dataframe
zillow_merge_df.rename(
        columns={'county_x': 'county', 'state_x': 'state'}, inplace=True)

# Drop unnecessary columns
zillow_merge_df = zillow_merge_df[['region_id', 'county', 'state', 'date', 'value']]

# Check the merged Zillow data
print(zillow_merge_df.head())


# ## Merge Zillows sales data with coordinates data
# Now that we have fetched the county coordinates data that includes longitude and latitude, we can merge the data with the Zillow sales data.   This requires us to merge on `county` and `state` columns since the coordinates data does not have a `region_id`.

# In[ ]:


# Merge the Zillow data and county coordinates data.
master_df = pd.merge(zillow_merge_df, county_coordinates_df, on=['county', 'state'])

master_df['date']=pd.to_datetime(master_df['date'])

# Check the master data
#print(master_df)


# # 3. Display Historical Data
# ## Display average home sales per county from 1/1/2010 to 12/31/2021

# In[ ]:


county_mean_df = res.get_county_df_with_mean(master_df,'2010-01-01', '2021-12-31')
# display(county_mean_df.head())

# Divide price by 1000 so that it looks better on map.
county_mean_df["value"] = county_mean_df["value"] / 1000

county_mean_df.hvplot.points(
    'longitude',
    'latitude',
    geo=True,
    hover=True,
    hover_cols=['county','cum_pct_ch'],
    size='value',
    color='value',
    tiles='OSM',
    height=700,
    width=1200, 
    title='Average home sales per county from 1/1/2010 to 12/31/2021')


# ## Display percent change per county from 1/1/2010 to 12/31/2021

# In[ ]:


county_pct_change_df = res.get_county_df_with_cum_pct_change(master_df,'2010-01-01', '2022-08-01')

# Not sure why county_pct_change is missing the longitude and latitude, but I have to add it back :( 
merge_county_pct_change_df = pd.merge(county_pct_change_df, county_coordinates_df, on=['county', 'state'])


# Drop unnecessary columns
merge_county_pct_change_df = merge_county_pct_change_df[['region_id', 'county', 'state', 'latitude', 'longitude', 'cum_pct_ch']]

# Check the master data
#print(merge_county_pct_change_df.head())

merge_county_pct_change_df.hvplot.points(
    'longitude',
    'latitude',
    geo=True,
    hover=True,
    hover_cols=['county','cum_pct_ch'],
    size='cum_pct_ch',
    color='cum_pct_ch',
    tiles='OSM',
    height=700,
    width=1200, 
    title='Percent change per county from 1/1/2010 to 12/31/2021')


# # 4. The MAC/D

# In[ ]:


# Creates a DataFrame using only the columns we are interested in

filtered_df = master_df[['date','county','state','value']]

filtered_df['county'] = filtered_df['county'] + ", " + filtered_df['state']
drop_cols = ['state']
filtered_df = filtered_df.drop(columns=drop_cols) 


# In[ ]:


# Figured out the change in number of counties was messing up the charts

exploratory_df=filtered_df.groupby('date').count()


# In[ ]:


# Create new DataFrame with summed county markets to represent the entire nation
nationwide_df = filtered_df.groupby(filtered_df['date']).agg({'value':'sum'})

# Must divide 'values' by number of counties that make up said value so data isn't skewed by county number
nationwide_df['avg'] = nationwide_df['value']/exploratory_df['county']


# In[ ]:


# Define a function for getting a nationwide MACD indicator using pandas_ta
def get_nationwide_macd(fast, slow, signal):
    nationwide_macd_df = nationwide_df.ta.macd(close='avg', fast=fast, slow=slow, signal=signal, append=True)
    # Making DataFrame look nice
    nationwide_macd_df = nationwide_macd_df.rename(columns={f'MACD_{fast}_{slow}_{signal}':'fast_ema',f'MACDh_{fast}_{slow}_{signal}':'signal',f'MACDs_{fast}_{slow}_{signal}':'slow_ema'}).dropna()
    # Divide by 1000 so it looks more like a momentum indicator
    nationwide_macd_df = nationwide_macd_df/1000
    return nationwide_macd_df


# In[ ]:


# Use newly defined funtion

nationwide_macd_df = get_nationwide_macd(6, 12, 4)


# In[ ]:


# Graph

nationwide_macd_df.hvplot(title='US Housing Market Momentum', ylabel='Momentum')


# In[ ]:


# Show mean housing price in county

filtered_df.hvplot(title='Mean Single Famiy Home Price',groupby='county', x='date', yformatter='%.0f')


# In[ ]:


# Define a function for getting a county-specific MACD indicator using pandas_ta
def get_county_macd(fast, slow, signal):
    
    county_macd_df=filtered_df.copy()
    
    county_macd_df.ta.macd(close='value', fast=fast, slow=slow, signal=signal, append=True)
    
    # Making DataFrame look nice
    county_macd_df = county_macd_df.rename(columns={f'MACD_{fast}_{slow}_{signal}':'fast_ema',f'MACDh_{fast}_{slow}_{signal}':'signal',f'MACDs_{fast}_{slow}_{signal}':'slow_ema'}).dropna()
    
    county_macd_df = county_macd_df.drop(columns='value').set_index('date')

    county_macd_df[['fast_ema','signal','slow_ema']] = county_macd_df[['fast_ema','signal','slow_ema']]/1000
    
    return county_macd_df


# In[ ]:


# Use newly defined function
county_macd_df=get_county_macd(6,12,4)


# In[ ]:


county_macd_df.hvplot(title='MAC/D by County', groupby='county', x='date', ylabel='Momentum')


# # 5. Monte Carlo

# In[ ]:


filtered_df = master_df[['date','county','state','value']]
filtered_df = filtered_df.sort_values('value', ascending=False)


# In[ ]:


# Deleting county and state columns and replacing with location column which contains county, state
# This is necessary because same county names exist in different states. 
mc_df = filtered_df
mc_df['location'] = mc_df['county'] + ", " + mc_df['state']
drop_cols = ['county', 'state']
mc_df = mc_df.drop(columns=drop_cols)
mc_df.set_index(mc_df['location'])


# In[ ]:


# Getting average home value for each location
values_df = mc_df.groupby('location', as_index=False)['value'].mean()
values_df = values_df.sort_values(by='value')
list_of_all_counties = values_df['location'].tolist()
list_of_all_counties.sort()
highest_df = values_df.tail(3)
lowest_df = values_df.head(3)
print(highest_df)
print(lowest_df)
#display(list_of_all_counties)


# In[ ]:


most_expensive_counties = highest_df['location'].to_numpy()
least_expensive_counties = lowest_df['location'].to_numpy()
print(most_expensive_counties)
print(least_expensive_counties)


# In[ ]:


mc_df = mc_df.sort_values(by='date')
expensive_dataframe_array = []
start_date = '2009-04-30'
end_date = '2022-06-30'
for group_loc in most_expensive_counties:
    df_exp_temp = mc_df.loc[(mc_df['location']==group_loc) & (mc_df['date'] <= end_date) & (mc_df['date'] >= start_date)]
    expensive_dataframe_array.append(df_exp_temp.drop('location', axis=1).reset_index())
    
#dataframe_array
expensive_df = pd.concat(expensive_dataframe_array, axis=1, keys=most_expensive_counties)
print(mc_df)
print(expensive_df)


# In[ ]:


#mc_df = mc_df.sort_values(by='date')
least_exp_dataframe_array = []
start_date = '2009-04-30'
end_date = '2022-06-30'
for group_loc in least_expensive_counties:
    df_temp = mc_df.loc[(mc_df['location']==group_loc) & (mc_df['date'] <= end_date) & (mc_df['date'] >= start_date)]
    least_exp_dataframe_array.append(df_temp.drop('location', axis=1).reset_index())
    
#dataframe_array
least_exp_df = pd.concat(least_exp_dataframe_array, axis=1, keys=least_expensive_counties)
#print(least_exp_df)


# In[ ]:


#Monte Carlo Simulation for 3 most expensive counties
mc_expensive_data = MCSimulation(expensive_df, "", 1000, 120)


# In[ ]:


print(mc_expensive_data.calc_cumulative_return())


# In[ ]:


mc_expensive_data.plot_simulation()


# In[ ]:


mc_expensive_data.plot_distribution()


# In[ ]:


mc_expensive_data.summarize_cumulative_return()


# In[ ]:


#Monte Carlo Simulation for 3 least expensive counties
mc_least_exp_data = MCSimulation(least_exp_df, "", 1000, 120)


# In[ ]:


display(mc_least_exp_data.calc_cumulative_return())


# In[ ]:


mc_least_exp_data.plot_simulation()


# In[ ]:


mc_least_exp_data.plot_distribution()


# In[ ]:


mc_least_exp_data.summarize_cumulative_return()


# In[ ]:





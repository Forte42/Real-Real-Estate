#!/usr/bin/env python
# coding: utf-8

# In[6]:


# Standard imports. Note: You must pip install nasdaqdatalink 1st
import os
import pandas as pd
import hvplot.pandas
from pathlib import Path

# For API Calls
import nasdaqdatalink
# Do we need requests?
import requests
# For opening zip folder
import shutil 
# For technical analysis
import pandas_ta as ta


# In[7]:


# Linking my API key to .env in the same folder. The key is stored in the folder without any quotations around it 

nasdaqdatalink.read_key(filename=".env")


# In[8]:


# A function to retrieve a dataframe of counties, zips, etc
def get_regions(regions):
    region_df=nasdaqdatalink.get_table('ZILLOW/REGIONS', region_type=regions)  
    return region_df


# # 1. Get the regions data from Zillow REST APIs.   
# This contains a list of all counties in the US.

# In[9]:


# Using get_regions to retrieve a list of counties
region_df = get_regions('county')
region_df[["county", "state"]] = region_df["region"].str.split(';', 1, expand=True)
region_df["state"] = region_df["state"].str.split(';', 1, expand=True)[0]

#
# Clean up regions data
# Remove ' County' so that we can match the Zillow data with Wikipedia data.
region_df["county"] = region_df["county"].str.replace(" County", "")

# Remove the leading blank space from the 'state' column.
region_df["state"] = region_df['state'].str[1:]

# Clean up region_id datatype.
region_df['region_id']=region_df['region_id'].astype(int)

# Check data for region_df
print(region_df.head())
print(region_df.tail())


# # 2. Get the Zillow sales data.  
# In this example, we read in Zillow sales data in the form of a CSV file.  

# In[10]:


# Get the Zillow sales data. 
# The actual API call using the SDK.
# Instructions can be found here https://data.nasdaq.com/databases/ZILLOW/usage/quickstart/python
# Replace 'quandl' w/ 'nasdaqdatalink
# Turned into a function to prevent constant re-downloading massive csv

def get_zillow_data():
    data = nasdaqdatalink.export_table('ZILLOW/DATA', indicator_id='ZSFH', region_id=list(region_df['region_id']),filename='db.zip')
    
    # Unzipping database from API call
    shutil.unpack_archive('db.zip')
    return data        


# In[11]:


# Reading in Database
zillow_data=pd.read_csv(
    Path('ZILLOW_DATA_d5d2ff90eb7172dbde848ea36de12dfe.csv')
)

# Check the Zillow sales data
print(zillow_data.head())
print(zillow_data.tail())


# In[12]:


## Merge the Region dataframe with the Zillow sales data
zillow_merge_df = pd.merge(region_df, zillow_data, on=['region_id'])

# Check the merged Zillow data
zillow_merge_df.head()


# # 3. Get the county coordinates data.
# We couldn't find the county coordinates from Zillow, so we sourced the data from Wikipedia.   We are going to have to merge the data with Zillow based on county and state. 

# In[13]:


# Read in county data with coordinates
county_coordinates_df=pd.read_csv(
    Path('counties_w_coordinates.csv')
)

# Clean up data.
# We need to rename the columns so that we can merge our Zillow data set 
# with the county coordinates data.   The dataframes will be merged against 'county' and 'state'. 
county_coordinates_df = county_coordinates_df.rename(columns={"County\xa0[2]" : "county"})
# county_coordinates_df = county_coordinates_df.rename(columns={"region" : "region"})
county_coordinates_df = county_coordinates_df.rename(columns={"State" : "state"})

# Remove degrees 
county_coordinates_df["Latitude"] = county_coordinates_df["Latitude"].str.replace("°", "")
county_coordinates_df["Longitude"] = county_coordinates_df["Longitude"].str.replace("°", "")

# Remove + sign for Latitude and Longitude
county_coordinates_df["Latitude"] = county_coordinates_df["Latitude"].str.replace("+", "")
county_coordinates_df["Longitude"] = county_coordinates_df["Longitude"].str.replace("+", "")

# Some of the data uses unicode hyphens which causes problems when trying to convert the Longitude and Latitude to float.
county_coordinates_df["Latitude"] = county_coordinates_df["Latitude"].str.replace('\U00002013', '-')
county_coordinates_df["Longitude"] = county_coordinates_df["Longitude"].str.replace('\U00002013', '-')

# Convert Longitude and Latitude to float so we can display on the map. 
county_coordinates_df["Latitude"] = county_coordinates_df["Latitude"].astype(float)
county_coordinates_df["Longitude"] = county_coordinates_df["Longitude"].astype(float)

# Check the county coordinates data
county_coordinates_df.head()


# In[14]:


# Merge the Zillow data and county coordinates data.
master_df = pd.merge(zillow_merge_df, county_coordinates_df, on=['county', 'state'])

master_df['date']=pd.to_datetime(master_df['date'])

# Check the master data
master_df


# # 4. Display in a Map

# In[15]:


# Get mean data by state and county
county_df = master_df.groupby(["state", "county"]).mean()

# Divide price by 1000 so that it looks better on map.
county_df["value"] = county_df["value"] / 1000

# Check data
print(county_df.head())
print(county_df.tail())


# In[16]:


county_df.hvplot.points(
    'Longitude',
    'Latitude',
    geo=True,
    size='value',
    color='value',
    tiles='OSM',
    height=700,
    width=1200)


# # The MAC/D

# In[17]:


# Creates a DataFrame using only the columns we are interested in

filtered_df = master_df[['date','county','state','value']]

filtered_df['county'] = filtered_df['county'] + ", " + filtered_df['state']
drop_cols = ['state']
filtered_df = filtered_df.drop(columns=drop_cols) 


# In[18]:


# Figured out the change in number of counties was messing up the charts

exploratory_df=filtered_df.groupby('date').count()


# In[19]:


# Create new DataFrame with summed county markets to represent the entire nation
nationwide_df = filtered_df.groupby(filtered_df['date']).agg({'value':'sum'})

# Must divide 'values' by number of counties that make up said value so data isn't skewed by county number
nationwide_df['avg'] = nationwide_df['value']/exploratory_df['county']


# In[50]:


# Define a function for getting a nationwide MACD indicator using pandas_ta
def get_nationwide_macd(fast, slow, signal):
    nationwide_macd_df = nationwide_df.ta.macd(close='avg', fast=fast, slow=slow, signal=signal, append=True)
    # Making DataFrame look nice
    nationwide_macd_df = nationwide_macd_df.rename(columns={f'MACD_{fast}_{slow}_{signal}':'fast_ema',f'MACDh_{fast}_{slow}_{signal}':'signal',f'MACDs_{fast}_{slow}_{signal}':'slow_ema'}).dropna()
    # Divide by 1000 so it looks more like a momentum indicator
    nationwide_macd_df = nationwide_macd_df/1000
    return nationwide_macd_df


# In[48]:


# Use newly defined funtion

nationwide_macd_df = get_nationwide_macd(6, 12, 4)


# In[49]:


# Graph

nationwide_macd_df.hvplot(title='US Housing Market Momentum', ylabel='Momentum')


# In[58]:


# Show mean housing price in county

filtered_df.hvplot(title='Mean Single Famiy Home Price',groupby='county', x='date', yformatter='%.0f')


# In[62]:


# Define a function for getting a county-specific MACD indicator using pandas_ta
def get_county_macd(fast, slow, signal):
    
    county_macd_df=filtered_df.copy()
    
    county_macd_df.ta.macd(close='value', fast=fast, slow=slow, signal=signal, append=True)
    
    # Making DataFrame look nice
    county_macd_df = county_macd_df.rename(columns={f'MACD_{fast}_{slow}_{signal}':'fast_ema',f'MACDh_{fast}_{slow}_{signal}':'signal',f'MACDs_{fast}_{slow}_{signal}':'slow_ema'}).dropna()
    
    county_macd_df = county_macd_df.drop(columns='value').set_index('date')

    county_macd_df[['fast_ema','signal','slow_ema']] = county_macd_df[['fast_ema','signal','slow_ema']]/1000
    
    return county_macd_df


# In[63]:


# Use newly defined function
county_macd_df=get_county_macd(6,12,4)


# In[64]:


county_macd_df.hvplot(title='MAC/D by County', groupby='county', x='date', ylabel='Momentum')


# In[ ]:





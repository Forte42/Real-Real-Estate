import os
import pandas as pd
import hvplot.pandas
from pathlib import Path
# For technical analysis
import pandas_ta as ta

# Creates a DataFrame using only the columns we are interested in

filtered_df = master_df[['date','county','state','value']]

filtered_df['county'] = filtered_df['county'] + ", " + filtered_df['state']
drop_cols = ['state']
filtered_df = filtered_df.drop(columns=drop_cols)

# Figured out the change in number of counties was messing up the charts

exploratory_df=filtered_df.groupby('date').count()

# Create new DataFrame with summed county markets to represent the entire nation
nationwide_df = filtered_df.groupby(filtered_df['date']).agg({'value':'sum'})

# Must divide 'values' by number of counties that make up said value so data isn't skewed by county number
nationwide_df['avg'] = nationwide_df['value']/exploratory_df['county']

# Define a function for getting a nationwide MACD indicator using pandas_ta
def get_nationwide_macd(fast, slow, signal):
    nationwide_macd_df = nationwide_df.ta.macd(close='avg', fast=fast, slow=slow, signal=signal, append=True)
    # Making DataFrame look nice
    nationwide_macd_df = nationwide_macd_df.rename(columns={f'MACD_{fast}_{slow}_{signal}':'fast_ema',f'MACDh_{fast}_{slow}_{signal}':'signal',f'MACDs_{fast}_{slow}_{signal}':'slow_ema'}).dropna()
    # Divide by 1000 so it looks more like a momentum indicator
    nationwide_macd_df = nationwide_macd_df/1000
    return nationwide_macd_df

# Use newly defined funtion

nationwide_macd_df = get_nationwide_macd(6, 12, 4)

# Graph

nationwide_macd_df.hvplot(title='US Housing Market Momentum', ylabel='Momentum')

# Show mean housing price in county

filtered_df.hvplot(title='Mean Single Famiy Home Price',groupby='county', x='date', yformatter='%.0f')

# Define a function for getting a county-specific MACD indicator using pandas_ta
def get_county_macd(fast, slow, signal):
    
    county_macd_df=filtered_df.copy()
    
    county_macd_df.ta.macd(close='value', fast=fast, slow=slow, signal=signal, append=True)
    
    # Making DataFrame look nice
    county_macd_df = county_macd_df.rename(columns={f'MACD_{fast}_{slow}_{signal}':'fast_ema',f'MACDh_{fast}_{slow}_{signal}':'signal',f'MACDs_{fast}_{slow}_{signal}':'slow_ema'}).dropna()
    
    county_macd_df = county_macd_df.drop(columns='value').set_index('date')

    county_macd_df[['fast_ema','signal','slow_ema']] = county_macd_df[['fast_ema','signal','slow_ema']]/1000
    
    return county_macd_df

# Use newly defined function
county_macd_df=get_county_macd(6,12,4)

county_macd_df.hvplot(title='MAC/D by County', groupby='county', x='date', ylabel='Momentum')
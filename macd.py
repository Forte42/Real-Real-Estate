import os
import pandas as pd
import hvplot.pandas
from pathlib import Path
# For technical analysis
import pandas_ta as ta


def get_nationwide_macd(nationwide_df, fast, slow, signal):
    nationwide_macd_df = nationwide_df.ta.macd(
        close='avg', fast=fast, slow=slow, signal=signal, append=True)
    # Making DataFrame look nice
    nationwide_macd_df = nationwide_macd_df.rename(
        columns={f'MACD_{fast}_{slow}_{signal}': 'fast_ema', f'MACDh_{fast}_{slow}_{signal}': 'signal', f'MACDs_{fast}_{slow}_{signal}': 'slow_ema'}).dropna()
    # Divide by 1000 so it looks more like a momentum indicator
    nationwide_macd_df = nationwide_macd_df/1000
    return nationwide_macd_df


def get_county_macd(filtered_df, county, fast, slow, signal):

    county_macd_df = filtered_df.copy()
    county_macd_df = county_macd_df[county_macd_df['county'] == county]

    county_macd_df.ta.macd(close='value', fast=fast,
                           slow=slow, signal=signal, append=True)

    # Making DataFrame look nice
    county_macd_df = county_macd_df.rename(columns={f'MACD_{fast}_{slow}_{signal}': 'fast_ema',
                                           f'MACDh_{fast}_{slow}_{signal}': 'signal', f'MACDs_{fast}_{slow}_{signal}': 'slow_ema'}).dropna()

    county_macd_df = county_macd_df.drop(columns='value').set_index('date')

    county_macd_df[['fast_ema', 'signal', 'slow_ema']
                   ] = county_macd_df[['fast_ema', 'signal', 'slow_ema']]/1000

    return county_macd_df

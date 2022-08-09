# Import libraries and dependencies
import numpy as np
import pandas as pd
import os
import datetime as dt
import pytz

class MCSimulation:

    def __init__(self, pandas_df, weights=""):
        pct_change_df = pandas_df.xs('value',level=1,axis=1).pct_change()
        locations = pandas_df.columns.get_level_values(0).unique()
        column_names = [(x,"monthly_return") for x in locations]
        pct_change_df.columns = pd.MultiIndex.from_tuples(column_names)
        pandas_df = pandas_df.merge(pct_change_df,left_index=True,right_index=True).reindex(columns=locations,level=0)
        
        self.df = pandas_df
        self.weights = weights
        self.nSim = 500
        self.nTrading = 12 * 8
        self.simulated_return = ""
        
    def calc_cumulative_return(self):
        last_prices = self.portfolio_data.xs('value',level=1,axis=1)[-1:].values.tolist()[0]
        print(last_prices)
        

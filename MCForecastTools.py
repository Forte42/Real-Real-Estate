# Import libraries and dependencies
import numpy as np
import pandas as pd
import os
import datetime as dt
import pytz

class MCSimulation:
    def __init__(self, pandas_df):
        pct_change_df = pandas_df.xs('value',level=1,axis=1).pct_change()
        cities = pandas_df.columns.get_level_values(0).unique()
        df1 = pandas_df.sum(level=0, axis=1)
        df1.columns = pd.MultiIndex.from_product([df1.columns,["pct_change"]])
        df1 = pd.concat([pandas_df,df1],axis=1).sort_index(1)
        #for col in pct_change_df.columns:
            #df1.merge(pct_change_df, how="outer", on="pct_change")
            #df1[col]["pct_change"] = pct_change_df[col]
        
        print(df1)
        print(pct_change_df)


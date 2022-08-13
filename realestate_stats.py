import pandas as pd

def get_county_df_with_mean(df, start_date, end_date):    
    """
    Return a DataFrame that provides the mean value for a date range grouped by counties and states
    
    Parameters: 
        df - DataFrame to calculate mean value for
        start_date - filter data after this date
        end_date - filter data before this date
    
    Returns: 
        DataFrame with mean value grouped by counties and states
        
    """
    start_date = pd.to_datetime(start_date) 
    end_date = pd.to_datetime(end_date)

    cur_df = df
    cur_df = cur_df[cur_df['date'].dt.year > start_date.year]
    cur_df = cur_df[cur_df['date'].dt.year < end_date.year]
    
    mean_df = cur_df.groupby(["state", "county", "region_id"]).mean()
    return mean_df


def get_county_df_with_cum_pct_change(df, start_date, end_date):   
    """
    Return a DataFrame that provides the cumulative percentage change for a 
    date range grouped by counties and states
    
    Parameters: 
        df - DataFrame to calculate mean value for
        start_date - filter data after this date
        end_date - filter data before this date
    
    Returns: 
        DataFrame with cumulative percentage change
        
    """
    start_date = pd.to_datetime(start_date) 
    end_date = pd.to_datetime(end_date)

    cur_df = df
    cur_df = cur_df[cur_df['date'].dt.year > start_date.year]
    cur_df = cur_df[cur_df['date'].dt.year < end_date.year]
    
    cur_df["pct_change"] = cur_df.groupby(["state", "county", "region_id"])["value"].pct_change()

    yearly_df = cur_df.groupby(["state", "county", "region_id"])["pct_change"].sum().mul(100).reset_index().rename(columns={'pct_change': 'cum_pct_ch'})

    return yearly_df
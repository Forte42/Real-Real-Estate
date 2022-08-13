import pandas as pd
import nasdaqdatalink
from pathlib import Path

# A function to retrieve a dataframe of counties, zips, etc
def get_regions(regions):    
    region_df=nasdaqdatalink.get_table('ZILLOW/REGIONS', region_type=regions)  
    return region_df

def load_zillow_region_data():
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
    
    return region_df


def load_zillow_sales_data(region_df):
    # A function to load and clean Zillow sales data
    # Reading in Database
    zillow_data = pd.read_csv(
        Path('ZILLOW_DATA_d5d2ff90eb7172dbde848ea36de12dfe.csv', parse_dates=['date'])
    )

    # Merge the Region dataframe with the Zillow sales data
    zillow_merge_df = pd.merge(region_df, zillow_data, on=['region_id'])

    # Check the merged Zillow data
    return zillow_merge_df

def load_county_coordinates():
    # Load county coordinates

    # Read in county data with coordinates
    county_coordinates_df = pd.read_csv(
        Path('counties_w_coordinates.csv')
    )

    # Clean up data.
    # We need to rename the columns so that we can merge our Zillow data set
    # with the county coordinates data.   The dataframes will be merged against 'county' and 'state'.
    county_coordinates_df = county_coordinates_df.rename(
        columns={"County\xa0[2]": "county"})
    # county_coordinates_df = county_coordinates_df.rename(columns={"region" : "region"})
    county_coordinates_df = county_coordinates_df.rename(
        columns={"State": "state"})

    # Remove degrees
    county_coordinates_df["Latitude"] = county_coordinates_df["Latitude"].str.replace(
        "°", "")
    county_coordinates_df["Longitude"] = county_coordinates_df["Longitude"].str.replace(
        "°", "")

    # Remove + sign for Latitude and Longitude
    county_coordinates_df["Latitude"] = county_coordinates_df["Latitude"].str.replace(
        "+", "")
    county_coordinates_df["Longitude"] = county_coordinates_df["Longitude"].str.replace(
        "+", "")

    # Some of the data uses unicode hyphens which causes problems when trying to convert the Longitude and Latitude to float.
    county_coordinates_df["Latitude"] = county_coordinates_df["Latitude"].str.replace(
        '\U00002013', '-')
    county_coordinates_df["Longitude"] = county_coordinates_df["Longitude"].str.replace(
        '\U00002013', '-')

    # Convert Longitude and Latitude to float so we can display on the map.
    county_coordinates_df["Latitude"] = county_coordinates_df["Latitude"].astype(
        float)
    county_coordinates_df["Longitude"] = county_coordinates_df["Longitude"].astype(
        float)

    # Rename column names
    county_coordinates_df.rename(
        columns={'Latitude': 'latitude', 'Longitude': 'longitude'}, inplace=True)

    return county_coordinates_df



def get_county_df_with_mean(df, start_date, end_date):    
    display(df.head())
    start_date = pd.to_datetime(start_date) 
    end_date = pd.to_datetime(end_date)

    cur_df = df
    cur_df = cur_df[cur_df['date'].dt.year > start_date.year]
    cur_df = cur_df[cur_df['date'].dt.year < end_date.year]
    
    mean_df = cur_df.groupby(["state", "county"]).mean()
    return mean_df

# Return a DataFrame for a given region_id for a date range
def get_region_df(df, region_id, start_date, end_date): 
    # print("XXXX")
    # display(region_id)
    
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)
    
    cur_df = df[df['region_id'] == region_id]
    cur_df = cur_df[cur_df['date'].dt.year >= start_date.year ]  
    # cur_df = cur_df[cur_df['date'].dt.month >= start_date.month]
    cur_df = cur_df[cur_df['date'].dt.year <= end_date.year]
    # cur_df = cur_df[cur_df['date'].dt.month <= end_date.month]
    
    return cur_df

# Return a DataFrame that includes pct_change for a given region_id for a date range.
def get_region_df_with_pct_change(df, region_id, start_date, end_date):
    cur_df = get_region_df(df, region_id, start_date, end_date)
    cur_df['pct_change'] = cur_df['value'].pct_change() 
    cur_df['pct_change'] = cur_df['pct_change'].fillna(0) 
    return cur_df
    # return df

# Return the total pct_change for a given region_id for a date range.
def calc_pct_change(df, region_id, start_date, end_date):
    cur_df = get_region_df(df, region_id, start_date, end_date)
    cur_df['pct_change'] = cur_df['value'].pct_change(len(cur_df.index)-1) 
    cur_df['pct_change'] = cur_df['pct_change'].fillna(0) 
    val = cur_df.tail(1)['pct_change']
    
    return val.iloc[0].astype(float)
    


def hello_world(start_date): 
    print(f"start_date: {start_date}")
    start_date = pd.to_datetime(start_date) 
    return start_date
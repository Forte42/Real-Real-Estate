import pandas as pd
import nasdaqdatalink
from pathlib import Path


def get_regions(regions):    
    """
    Fetches a dataframe of Zillow region data (counties, states, etc) from Zillow's REST APIs.
    
    Parameters: 
        regions - the type of region to return, eg county, state 
        
    Returns: 
        DataFrame with Zillow region data
        
    """
    region_df=nasdaqdatalink.get_table('ZILLOW/REGIONS', region_type=regions)  
    return region_df

def load_zillow_region_data():
    """
    Fetches Zillow county data and returns a cleaned up DataFrame.
    
    Returns: 
        DataFrame with Zillow county data
        
    """
        
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
    """
    Loads Zillow sales data from a CSV file.  We then merge the Zillow sales 
    data with the region DataFrame.
    
    Parameters: 
        region_df - Zillow region DataFrame 
    
    Returns: 
        merged DataFrame with Zillow sales and region data.
        
    """
    # A function to load and clean Zillow sales data
    # Reading in Database
    zillow_data = pd.read_csv(
        Path('ZILLOW_DATA_d5d2ff90eb7172dbde848ea36de12dfe.csv', parse_dates=['date'])
    )

    # Merge the Region dataframe with the Zillow sales data
    zillow_merge_df = pd.merge(region_df, zillow_data, on=['region_id'])

    # Check the merged Zillow data
    return zillow_merge_df


def get_zillow_data():
    """
    Get the Zillow sales data. 
    The actual API call using the SDK.
    Instructions can be found here https://data.nasdaq.com/databases/ZILLOW/usage/quickstart/python
    Replace 'quandl' w/ 'nasdaqdatalink
    """
    data = nasdaqdatalink.export_table('ZILLOW/DATA', indicator_id='ZSFH', region_id=list(region_df['region_id']),filename='db.zip')
    
    # Unzipping database from API call
    shutil.unpack_archive('db.zip')
    return data        

def load_county_coordinates():
    """
    Loads county coordinates data from a CSV file.  
    
    Returns: 
        DataFrame with county coordinates
        
    """
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
    
    # Drop unnecessary columns
    county_coordinates_df = county_coordinates_df[['county', 'state', 'latitude', 'longitude']]

    return county_coordinates_df


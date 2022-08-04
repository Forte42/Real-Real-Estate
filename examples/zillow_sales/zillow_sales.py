import streamlit as st
import pandas as pd
import numpy as np
import pydeck as pdk
import nasdaqdatalink
import requests
from pathlib import Path
import shutil
import hvplot.pandas

st.set_page_config(layout="wide")
st.title('Zillow Sales')


# A function to retrieve a dataframe of counties, zips, etc
def get_regions(regions):
    region_df = nasdaqdatalink.get_table('ZILLOW/REGIONS', region_type=regions)
    return region_df

# A function to load and clean Zillow region data


@st.cache
def load_zillow_region_data(nrows):
    region_df = get_regions('county')
    region_df[["county", "state"]] = region_df["region"].str.split(
        ';', 1, expand=True)
    region_df["state"] = region_df["state"].str.split(';', 1, expand=True)[0]

    #
    # Clean up regions data
    # Remove ' County' so that we can match the Zillow data with Wikipedia data.
    region_df["county"] = region_df["county"].str.replace(" County", "")

    # Remove the leading blank space from the 'state' column.
    region_df["state"] = region_df['state'].str[1:]

    # Clean up region_id datatype.
    region_df['region_id'] = region_df['region_id'].astype(int)
    return region_df

# A function to load and clean Zillow sales data


@st.cache
def load_zillow_sales_data(nrows, region_df):
    # data = nasdaqdatalink.export_table(
    #     'ZILLOW/DATA', indicator_id='ZSFH', region_id=list(region_df['region_id']), filename='db.zip')

    # # Unzipping database from API call
    # shutil.unpack_archive('db.zip')

    # Reading in Database
    zillow_data = pd.read_csv(
        Path('./zillow_sales/data/zillow_sales.csv')
    )

    # Merge the Region dataframe with the Zillow sales data
    zillow_merge_df = pd.merge(region_df, zillow_data, on=['region_id'])

    # Check the merged Zillow data
    return zillow_merge_df

# Load county coordinates


@st.cache
def load_county_coordinates():
    # Read in county data with coordinates
    county_coordinates_df = pd.read_csv(
        Path('./zillow_sales/data/counties_w_coordinates.csv')
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
        columns={'Latitude': 'lat', 'Longitude': 'lon'}, inplace=True)

    return county_coordinates_df

# Merge Zillow region and sales data


def merge_zillow_data(region_df, sales_df):
    # Merge the Region dataframe with the Zillow sales data
    zillow_merge_df = pd.merge(region_df, sales_df, on=['region_id'])
    zillow_merge_df.rename(
        columns={'county_x': 'county', 'state_x': 'state'}, inplace=True)

    return zillow_merge_df

# Merge Zillow data with county coordinates


def merge_zillow_county_coordinate_data(zillow_df, county_coordinates_df):
    print(zillow_df.dtypes)
    # print(county_coordinates_df.dtypes)
    # county_coordinates_df.columns.dtype

    # Merge the Zillow data and county coordinates data.
    master_df = pd.merge(
        zillow_df,
        county_coordinates_df,
        on=['state', 'county'])

    # Check the master data
    return master_df


# Layout
# col_a = st.columns(1)
# with col_a:
data_load_state = st.text('Loading Zillow region data...')
region_df = load_zillow_region_data(10000)

data_load_state = st.text('Loading Zillow sales data...')
sales_df = load_zillow_sales_data(10000, region_df)

data_load_state = st.text('Loading county coordinates data...')
county_coordinates_df = load_county_coordinates()

data_load_state = st.text('Merging Zillow dataframes...')
zillow_df = merge_zillow_data(region_df, sales_df)

# try:
data_load_state = st.text(
    'Merging Zillow and county coordinates dataframes')
master_df = merge_zillow_county_coordinate_data(
    zillow_df, county_coordinates_df)

data_load_state.text("Done! (using st.cache)")
# except BaseException as err:
#     print(f"Unexpected {err=}, {type(err)=}")

# if st.checkbox('Show raw data'):
#     st.subheader('Raw data')
#     st.write(county_coordinates_df)


# Layout
col1, col2, col3 = st.columns(3)

with col1:
    st.subheader('Coordinates Data')
    st.write(county_coordinates_df)

with col2:
    st.subheader('Sales Data')
    st.write(sales_df)

with col3:
    st.subheader('Region Data')
    st.write(region_df)


# Layout
county_df = master_df.groupby(["state", "county"]).mean()

# Divide price by 1000 so that it looks better on map.
county_df["value"] = county_df["value"] / 1000

col1, col2, col3 = st.columns(3)
with col1:
    st.subheader('Histogram')

    # st.subheader('Number of pickups by hour')
    # hist_values = np.histogram(
    #     data[DATE_COLUMN].dt.hour, bins=24, range=(0, 24))[0]
    # st.bar_chart(hist_values)

    # # Some number in the range 0-23
    # hour_to_filter = st.slider('hour', 0, 23, 17)
    # st.bar_chart(county_df)


with col2:
    st.subheader('2D Map')
    # st.write(sales_df)
    # filtered_data = data[data[DATE_COLUMN].dt.hour == hour_to_filter]

    # st.subheader('Map of all pickups at %s:00' % hour_to_filter)
    # county_df.hvplot.points(
    #     'Longitude',
    #     'Latitude',
    #     geo=True,
    #     size='value',
    #     color='value',
    #     tiles='OSM',
    #     height=700,
    #     width=1200)
    st.map(county_df)

with col3:
    st.subheader('3D Map')
    # st.write(region_df)

    df = pd.DataFrame(
        county_df,
        columns=['lat', 'lon'])

    st.pydeck_chart(pdk.Deck(
        map_style='mapbox://styles/mapbox/light-v9',
        initial_view_state=pdk.ViewState(
            latitude=40.7530,
            longitude=-73.9966,
            zoom=5,
            pitch=50,
        ),
        layers=[
            pdk.Layer(
                'HexagonLayer',
                data=df,
                get_position='[lon, lat]',
                radius=200,
                elevation_scale=4,
                elevation_range=[0, 1000],
                pickable=True,
                extruded=True,
            ),
            pdk.Layer(
                'ScatterplotLayer',
                data=df,
                get_position='[lon, lat]',
                get_color='[200, 30, 0, 160]',
                get_radius=200,
            ),
        ],
    ))

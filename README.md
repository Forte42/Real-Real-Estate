# Realestate of Mind

## Description

---

"Real estate is an imperishable asset, ever increasing in value. It is the most solid security that human ingenuity has devised. It is the basis of all security and about the only indestructible security." - Russell Sage

Housing is an investment that has several financial benefits, including:

- Portfolio Diversification
- Increases in Value
- Quality of Life

However, real estate purchases, especially for first time home buyers, can be a highly emotional decision, driven by rationales that are not based on analytics.

The purpose of this project is to build an application that enables home buyers to make more educated decisions on real estate. Features include:

- Display historical housing prices by county - This allows users to see trends, such as which counties are gaining or losing value. The data will be displayed in different views, such as in a datagrid, line plot, barchart or a map.
- MACD Analysis
- Provides predictive analytics for future real estate prices. This allows users to execute simulations, such as the Monte Carlo simulation, to determine which county is a better real estate purchase.

## User Stories

---

Our MVP will be based on the following user stories to start:

As a home buyer, I want to fetch historical housing prices by county in America from 2018-2022

As a home buyer, I want to list which counties gained or loss value in a specifc timeframe

As a home buyer, I want to view a map of which counties gained or loss value in a specific timeframe

As a home buyer, I want to determine which county has the highest probability of gaining or losing in the future

We will groom user stories and add acceptance critera during team meetings.

## Technology Stack

---

This code uses Python 3.9.12 with Pandas (1.4.2), Jupyterlab (3.3.2), hvPlot (0.7.3), Streamlit (1.12.0),Nasdaq-Data-Link (1.0.2), and Pandas_ta (0.3.14b0).

## Installation

In order to use this application, you will need to install `Jupyter`, `pandas` and `hvPlot`. Below are the instructions for installing each required library.

- Installing Jupyter - To install Jupyter, please refer to the [Jupyter Installation Guide](https://jupyter.org/install).

- Installing pandas - To install `pandas`, please refer to the [pandas Installation Guide](https://pandas.pydata.org/pandas-docs/stable/getting_started/install.html).

- Installing hvPlot - To install `hvPlot`, please refer to the [hvPlot Installation Guide](https://pypi.org/project/hvplot).

## Usage

To launch the Notebook, perform the following steps:

1. Open Terminal.
2. Navigate to the location of the Notebook.
3. Enter `jupyter lab` at the Terminal prompt.
4. Verify that you can access Jupyter in your browser.
5. Once you have launched the notebook, you can then execute each section.

- Fetching Data
- Cleanup and Merging
- Displaying Historical Data
- MACD Analysis
- Monte Carlo Simulations

## Contributors

This sample application was authored by:

- Garrett Hernandez (gtkhhz@gmail.com)
- Quinn Wong (quinn.wong@gmail.com)
- Smruthi Danda
- Kristen Potter
- Matthew Ho

## License

The MIT License (MIT)

Copyright (c) 2022 Realestate of Mind

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

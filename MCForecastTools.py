# Import libraries and dependencies
import numpy as np
import pandas as pd
import os
import datetime as dt
import pytz

class MCSimulation:

    def __init__(self, pandas_df):
        pct_change_df = pandas_df.xs('value',level=1,axis=1).pct_change()
        locations = pandas_df.columns.get_level_values(0).unique()
        column_names = [(x,"monthly_return") for x in locations]
        pct_change_df.columns = pd.MultiIndex.from_tuples(column_names)
        pandas_df = pandas_df.merge(pct_change_df,left_index=True,right_index=True).reindex(columns=locations,level=0)
        
        
        num_stocks = len(pandas_df.columns.get_level_values(0).unique())
        weights = [1.0/num_stocks for s in range(0,num_stocks)]
        
        
        self.df = pandas_df
        self.weights = weights
        self.nSim = 500
        self.nTrading = 12 * 8
        self.simulated_return = ""
        
    def calc_cumulative_return(self):
        # Get closing prices of each stock
        last_prices = self.df.xs('value',level=1,axis=1)[-1:].values.tolist()[0]
        
        # Calculate the mean and standard deviation of daily returns for each stock
        monthly_returns = self.df.xs('monthly_return', level=1, axis=1)
        mean_returns = monthly_returns.mean().tolist()
        std_returns = monthly_returns.std().tolist()
        print(mean_returns)
        print(std_returns)

        # Initialize empty Dataframe to hold simulated prices
        portfolio_cumulative_returns = pd.DataFrame()

        # Run the monte carlo simulation based on nSim
        for n in range(self.nSim):
            if n % 10 == 0:
                print(f"Running Monte Carlo simulation number {n}.")
        
            # Create a list of lists to contain the simulated values for each stock
            simvals = [[p] for p in last_prices]
            
            # For each stock in our data:
            for s in range(len(last_prices)):

                # Simulate the returns for each trading day
                for i in range(self.nTrading):
        
                    # Calculate the simulated price using the last price within the list
                    simvals[s].append(simvals[s][-1] * (1 + np.random.normal(mean_returns[s], std_returns[s])))
                    
            # Calculate the daily returns of simulated prices
            sim_df = pd.DataFrame(simvals).T.pct_change()
    
            # Use the `dot` function with the weights to multiply weights with each column's simulated daily returns
            sim_df = sim_df.dot(self.weights)
    
            # Calculate the normalized, cumulative return series
            portfolio_cumulative_returns[n] = (1 + sim_df.fillna(0)).cumprod()
        
        # Set attribute to use in plotting
        self.simulated_return = portfolio_cumulative_returns
        
        # Calculate 95% confidence intervals for final cumulative returns
        self.confidence_interval = portfolio_cumulative_returns.iloc[-1, :].quantile(q=[0.025, 0.975])
        
        return portfolio_cumulative_returns


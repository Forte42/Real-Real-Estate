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
        
    
    def plot_simulation(self):
        """
        Visualizes the simulated stock trajectories using calc_cumulative_return method.
        """ 
        
        # Check to make sure that simulation has run previously. 
        if not isinstance(self.simulated_return,pd.DataFrame):
            self.calc_cumulative_return()
            
        # Use Pandas plot function to plot the return data
        plot_title = f"{self.nSim} Simulations of Cumulative Portfolio Return Trajectories Over the Next {self.nTrading} Trading Months."
        return self.simulated_return.plot(legend=None,title=plot_title)
        
    def plot_distribution(self):
        """
        Visualizes the distribution of cumulative returns simulated using calc_cumulative_return method.
        """
        
        # Check to make sure that simulation has run previously.
        if not isinstance(self.simulated_return,pd.DataFrame):
            self.calc_cumulative_return()
        
        # Use the `plot` function to create a probability distribution histogram of simulated ending prices
        # with markings for a 95% confidence interval
        plot_title = f"Distribution of Final Cumuluative Returns Across All {self.nSim} Simulations"
        plt = self.simulated_return.iloc[-1, :].plot(kind='hist', bins=10,density=True,title=plot_title)
        plt.axvline(self.confidence_interval.iloc[0], color='r')
        plt.axvline(self.confidence_interval.iloc[1], color='r')
        return plt
        
    def summarize_cumulative_return(self):
        """
        Calculate final summary statistics for Monte Carlo simulated stock data.
        
        """
        
        # Check to make sure that simulation has run previously.
        if not isinstance(self.simulated_return,pd.DataFrame):
            self.calc_cumulative_return()
            
        metrics = self.simulated_return.iloc[-1].describe()
        ci_series = self.confidence_interval
        ci_series.index = ["95% CI Lower","95% CI Upper"]
        return metrics.append(ci_series)
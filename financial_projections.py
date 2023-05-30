import pandas as pd
import numpy as np
import plotly.graph_objects as go

# functions
def calculate_tax(income):
    brackets = [9950, 40525, 86375, 164925, 209425, 523600]
    rates = [0.10, 0.12, 0.22, 0.24, 0.32, 0.35, 0.37]
    tax = 0

    for i in range(len(brackets)):
        if income > brackets[i]:
            if i == 0:
                tax += rates[i] * brackets[i]
            else:
                tax += rates[i] * (brackets[i] - brackets[i-1])
        else:
            if i == 0:
                tax += rates[i] * income
            else:
                tax += rates[i] * (income - brackets[i-1])
            break

    if income > brackets[-1]:
        tax += rates[-1] * (income - brackets[-1])
        
    return tax

# parameters
variables = ['robert_income', 'isabel_income', 'expenses', 'assets']

# create initial setup DataFrame
data = pd.DataFrame({
    'year': [2023],
    'robert_income': [100000],
    'isabel_income': [90000],
    'expenses': [50000],
    'assets': [800000]
}).set_index('year')

growth_assumptions = {
    'robert_income': 0.03,
    'isabel_income': 0.02,
    'expenses': 0.02,
    'assets': 0.05
}
shocks = {
    2027: {
        'robert_income': -10000,
    }
}
volatility = 0.08  # standard deviation of asset growth
simulations = 1000  # number of simulations

# create a DataFrame to hold the future projections
projection = pd.DataFrame(index=range(2023, 2083))

# initialize a DataFrame with simulations for assets
asset_simulations = pd.DataFrame((1 + growth_assumptions['assets']) + volatility * np.random.standard_normal(size=(60,1000)), 
                                 index=projection.index,
                                 columns=['simulation_'+str(i) for i in range(1000)]
)

# loop over years
for year in projection.index:
    if year == 2023:
        # handle base year
        for var in variables:
            projection.loc[year, var] = data.loc[2023, var]
            asset_simulations.loc[year] = data.loc[2023, 'assets']
    else:
        # apply growth assumptions and shocks
        for var in variables:
            projection.loc[year, var] = projection.loc[year - 1, var] * (1 + growth_assumptions[var])
            if year in shocks and var in shocks[year]:
                projection.loc[year, var] += shocks[year][var]

        # add volatility to assets
        asset_simulations.loc[year] = projection.loc[year - 1, 'assets'] * (asset_simulations.loc[year])

# # calculate tax
# projection['tax'] = projection.apply(calculate_tax, axis='columns')

# plot income
fig = go.Figure()

for var in variables:
    fig.add_trace(go.Scatter(x=projection.index, y=projection[var], mode='lines', name=var))

fig.show()

# plot asset simulations
fig = go.Figure()

percentiles = [1, 5, 20, 50, 80, 95, 99]
colors = ['red', 'orange', 'yellow', 'green', 'cyan', 'blue', 'purple']

for i in range(len(percentiles)):
    percentile = percentiles[i]
    color = colors[i]
    asset_percentile = asset_simulations.apply(lambda x: np.percentile(x, percentile), axis=1)
    fig.add_trace(go.Scatter(x=asset_simulations.index, y=asset_percentile, fill='tonexty', line_color=color, name=f'{percentile}th Percentile', opacity=0.5))

fig.show()
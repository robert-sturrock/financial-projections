import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.io as pio
from matplotlib import cm

# set defaults for charts
pio.templates.default = "plotly_white"

@np.vectorize
def calculate_tax(income):
    brackets = [9950, 40525, 86375, 164925, 209425, 523600]
    rates = [0.10, 0.12, 0.22, 0.24, 0.32, 0.35, 0.37]
    tax = 0
    for i in range(len(brackets)):
        if income > brackets[i]:
            if i == 0:
                tax += rates[i] * brackets[i]
            else:
                tax += rates[i] * (brackets[i] - brackets[i - 1])
        else:
            if i == 0:
                tax += rates[i] * income
            else:
                tax += rates[i] * (income - brackets[i - 1])
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
    'isabel_income': [200000],
    'expenses': [50000],
    'assets': [800000]
}).set_index('year')

growth_assumptions = {
    'robert_income': 0.0,
    'isabel_income': 0.0,
    'expenses': 0.01,
    'assets': 0.04
}

shocks = {
    2027: {
        'robert_income': (-10000, 'Robert leaves Google'),
        'isabel_income': (-100000, 'Isabel book deals are smaller')
    },
    2030: {
        'expenses': (30000, 'Childcare')
    }
}


volatility = 0.08  # standard deviation of asset growth
simulations = 1000  # number of simulations

# create a DataFrame to hold the future projections
projection = pd.DataFrame(index=range(2023, 2083))

# initialize a DataFrame with simulations for assets
asset_simulations = pd.DataFrame(1 + volatility * np.random.standard_normal(size=(60,10000)), 
                                 index=projection.index,
                                 columns=['simulation_'+str(i) for i in range(10000)]
)

# chain all 
asset_simulations = asset_simulations.cumprod()

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
                shock, _ = shocks[year][var]
                projection.loc[year, var] += shock
        
        # calculate household income and savings
        projection.loc[year, 'household_income'] = projection.loc[year, 'robert_income'] + projection.loc[year, 'isabel_income']
        projection.loc[year, 'taxes'] = calculate_tax(projection.loc[year, 'household_income'])
        projection.loc[year, 'net_household_income'] = projection.loc[year, 'household_income'] - projection.loc[year, 'taxes']

        # calculate savings
        projection.loc[year, 'savings'] = projection.loc[year, 'net_household_income'] - projection.loc[year, 'expenses']

        # add savings to assets
        projection.loc[year, 'assets'] += projection.loc[year, 'savings']

        # add volatility to assets
        asset_simulations.loc[year] = projection.loc[year - 1, 'assets'] * (asset_simulations.loc[year])

# plot income, expenses, and savings
fig = go.Figure(layout=go.Layout(template='plotly_white'))

for var in ['robert_income', 'isabel_income', 'expenses', 'savings', 'household_income','net_household_income','taxes']:
    fig.add_trace(go.Scatter(x=projection.index, y=projection[var], mode='lines', name=var))

fig.show()

# plot asset simulations as a fan chart
fig = go.Figure()

percentiles = [1, 5, 20, 50, 80, 95, 99]
colors = [cm.Blues(x) for x in np.linspace(0.01, 1, 7)]

for i in range(len(percentiles)):
    percentile = percentiles[i]
    color = colors[i]
    asset_percentile = asset_simulations.apply(lambda x: np.percentile(x, percentile), axis=1)
    fig.add_trace(go.Scatter(x=asset_percentile.index, y=asset_percentile, fill='tonexty', fillcolor='rgba'+str(color), line_color='rgba'+str(color), name=str(percentile)+'th percentile'))

fig.show()


# plot shocks
all_shock_values = []

for shock_type in ['assets', 'robert_income', 'isabel_income', 'expenses']:
    for year, shocks_in_year in shocks.items():
        if shock_type in shocks_in_year:
            all_shock_values.append(shocks_in_year[shock_type][0])

fig = make_subplots(rows=4, cols=1, shared_xaxes=True, shared_yaxes='rows')

for shock_type, subplot in zip(['assets', 'robert_income', 'isabel_income', 'expenses'], [1, 2, 3, 4]):
    shock_years = []
    shock_values = []
    hover_texts = []  # New list to store hover text labels
    for year, shocks_in_year in shocks.items():
        if shock_type in shocks_in_year:
            shock_years.append(year)
            shock_values.append(shocks_in_year[shock_type][0])
            hover_texts.append(shocks_in_year[shock_type][1])  # Add the hover text label to the list
    fig.add_trace(go.Bar(x=shock_years, y=shock_values, name=shock_type + ' shocks', text=hover_texts, textposition='outside', hovertemplate='%{text}', textfont=dict(color='rgba(0,0,0,0)')), row=subplot, col=1)

fig.update_xaxes(range=[2023, 2082])
fig.update_yaxes(range=[min(all_shock_values), max(all_shock_values)])
fig.update_layout(template='plotly_white')
fig.show()


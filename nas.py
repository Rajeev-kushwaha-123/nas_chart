import pandas as pd
import numpy as np
from sqlalchemy import create_engine
from datetime import datetime
import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
import plotly.io as pio
import io
import os
from plotly.subplots import make_subplots
from dotenv import load_dotenv  # Add this line
from dash import dcc
from dash import html
import plotly.graph_objects as go



# Load environment variables from .env file
load_dotenv() 
db_url =  create_engine(f'{os.getenv("ENGINE")}://{os.getenv("DTABASE_USER")}:{os.getenv("PASSWORD")}@{os.getenv("HOST")}/{os.getenv("NAS_DATABASE")}')
# db_url = create_engine('postgresql://postgres:root@10.24.89.107:5432/nas_db')
# Construct database URL from environment variables



# Read data from the database
post_state = pd.read_sql_query('select * from nas_fact', db_url)
post_data = pd.DataFrame(post_state)

def Indicator_Code():
    indicator_query = 'select indicator_code, description, short from indicator'
    indicator_mstr = pd.read_sql_query(indicator_query, db_url)
    return indicator_mstr

data = Indicator_Code()

filtered_data = post_data[post_data['indicator_code'].isin(['01', '05','21','22'])]
post_data1 = pd.read_sql_query('select frequency_code , description from frequency', db_url)
post_data2 = pd.read_sql_query('select revision_code, description from revision', db_url)
post_data3  = pd.read_sql_query('select quarterly_code , description from quarterly', db_url)
post_data4 = pd.read_sql_query('select industry_code, description from industry', db_url)
df = filtered_data[['indicator_code','financial_year', 'quarterly_code', 'revision_code','industry_code', 'frequency_code', 'current_price', 'constant_price']]


# Dictionary mapping column names to their respective DataFrames and keys
mappings = {
    'indicator_code': (data, 'indicator_code'),
    'frequency_code': (post_data1, 'frequency_code'),
    'revision_code': (post_data2, 'revision_code'),
    'quarterly_code': (post_data3, 'quarterly_code'),
    'industry_code': (post_data4, 'industry_code'),
}

# Perform the mapping for each column
for col, (df_mapping, key) in mappings.items():
    mapping_dict = df_mapping.set_index(key)['description'].to_dict()
    print(f"Mapping for {col}: {mapping_dict}")  # Debugging statement
    df.loc[:, col] = df[col].map(mapping_dict)

# Explicitly copy the DataFrame if needed
df = df.copy()

df['industry_code'] = df['industry_code'].fillna('NA')
df['quarterly_code']= df['quarterly_code'].fillna('NA')

df = df.dropna(subset=['constant_price'], how='any')

df_GDP_growth = df[df['indicator_code'] == "GDP Growth Rate"]
df_GVA_growth = df[df['indicator_code'] == "GVA Growth Rate"]
df_1 = df[(df['indicator_code'] != "GDP Growth Rate") & (df['indicator_code'] != "GVA Growth Rate")]

df_GDP_growth.loc[:, "constant_price"] = df_GDP_growth["constant_price"].round(1)
df_GDP_growth.loc[:,"constant_price"] = df_GDP_growth["constant_price"].round(1)
df_GVA_growth.loc[:,"current_price"] = df_GVA_growth["current_price"].round(1)
df_GVA_growth.loc[:,"constant_price"] = df_GVA_growth["constant_price"].round(1)

df_GDP_growth = df_GDP_growth.rename(columns={"current_price": "current_price_growth"})
df_GDP_growth = df_GDP_growth.rename(columns={"constant_price": "constant_price_growth"})
df_GVA_growth = df_GVA_growth.rename(columns={"current_price": "current_price_growth"})
df_GVA_growth = df_GVA_growth.rename(columns={"constant_price": "constant_price_growth"})

df_GGVA = df_1[df_1['indicator_code'] == "Gross Value Added"]
df_GGDP = df_1[df_1['indicator_code'] == "Gross Domestic Product"]

# on GDP 

 # Now applying the logic to get the latest available value in the prefrence of order for GDP

# Define the order of preference for revision_code
preference_order = {
    'Additional Revision':1,
    'Third Revised Estimates': 2,
    'Second Revised Estimates': 3,
    'First Revised Estimates': 4,
    'Provisional Estimates': 5,
    'Second Advance Estimates': 6,
    'First Advance Estimates': 7
}

# Create a new column for preference order
df_GGDP.loc[:, 'revision_preference'] = df_GGDP['revision_code'].map(preference_order)


# Sort the DataFrame by financial_year and revision_preference
df_GGDP_sorted = df_GGDP.sort_values(by=['financial_year', 'revision_preference'])

# Drop duplicates to keep only the latest data for each financial_year
df_GGDP_latest = df_GGDP_sorted.drop_duplicates(subset=['financial_year'], keep='first')

# Remove the helper column before final selection if not needed
df_GGDP_latest = df_GGDP_latest.drop(columns=['revision_preference'])

# The result contains all columns
result_GGDP_annually = df_GGDP_latest

# Filter df_GDP based on quarterly_code
df_GGDP_quarterly = df_GGDP[df_GGDP['quarterly_code'] != 'NA']

# Remove the helper column before final selection if not needed
df_GGDP_quarterly = df_GGDP_quarterly.drop(columns=['revision_preference'])

# On GDP growth

 # Now applying the logic to get the latest available value in the prefrence of order for GDP

# Define the order of preference for revision_code
preference_order = {
    'Additional Revision':1,
    'Third Revised Estimates': 2,
    'Second Revised Estimates': 3,
    'First Revised Estimates': 4,
    'Provisional Estimates': 5,
    'Second Advance Estimates': 6,
    'First Advance Estimates': 7
}

# Create a new column for preference order
df_GDP_growth['revision_preference'] = df_GDP_growth['revision_code'].map(preference_order)

# Sort the DataFrame by financial_year and revision_preference
df_GDP_growth_sorted = df_GDP_growth.sort_values(by=['financial_year', 'revision_preference'])

# Drop duplicates to keep only the latest data for each financial_year
df_GDP_growth_latest = df_GDP_growth_sorted.drop_duplicates(subset=['financial_year'], keep='first')

# Remove the helper column before final selection if not needed
df_GDP_growth_latest = df_GDP_growth_latest.drop(columns=['revision_preference'])
result_GDP_growth_annually = df_GDP_growth_latest

# Filter df_GDP based on quarterly_code
df_GDP_growth_quarterly = df_GDP_growth[df_GDP_growth['quarterly_code'] != 'NA']

# Remove the helper column before final selection if not needed
df_GDP_growth_quarterly = df_GDP_growth_quarterly.drop(columns=['revision_preference'])

# Merging GDP

# GDP Annual

# Example merge operation
df_GDP_Annually_merged = pd.merge(result_GGDP_annually,result_GDP_growth_annually[['financial_year', 'quarterly_code', 'revision_code', 'industry_code', 'frequency_code', 'current_price_growth', 'constant_price_growth']],
                    on=['financial_year', 'quarterly_code', 'revision_code', 'industry_code', 'frequency_code'],
                    how='left')

# GDP Quartely

# Example merge operation
df_GDP_Quarterly_merged = pd.merge(df_GGDP_quarterly,df_GDP_growth_quarterly[['financial_year', 'quarterly_code', 'revision_code', 'industry_code', 'frequency_code', 'current_price_growth', 'constant_price_growth']],
                    on=['financial_year', 'quarterly_code', 'revision_code', 'industry_code', 'frequency_code'],
                    how='left')

# on GVA

# Filter df_GVA based on quarterly_code
df_GGVA_annually = df_GGVA[df_GGVA['quarterly_code'] == 'NA']

# Define the priority order for revision_code
revision_code_priority_order = {
    'Additional Revision':1,
    'Third Revised Estimates': 2,
    'Second Revised Estimates': 3,
    'First Revised Estimates': 4,
    'Provisional Estimates': 5,
    'Second Advance Estimates': 6,
    'First Advance Estimates': 7
}

# Define a function to generate sorting keys
def custom_sort_key(row):
    return (
        row['financial_year'],  # Sort by financial_year in ascending order
        revision_code_priority_order.get(row['revision_code'], float('inf')),  # Sort by revision_code based on priority order
        0 if row['industry_code'] == 'Total Gross Value Added' else 1,  # Sort by industry_code with preference to 'Total Gross Value Added'
        row['industry_code']  # Sort by industry_code in any order
    )

# Create a new DataFrame to hold the sorting keys
sorting_keys = df_GGVA.apply(custom_sort_key, axis=1)

# Sort the original DataFrame based on the sorting keys
df_GGVA_annually_sorted = df_GGVA.iloc[sorting_keys.argsort()]

# Group the DataFrame by 'financial_year' and select the first row of each group
df_GGVA_annually_final = df_GGVA_annually_sorted.groupby('financial_year').first().reset_index()

# Filter df_GVA based on quarterly_code
df_GGVA_quarterly = df_GGVA[df_GGVA['quarterly_code'] != 'NA']

# Filter the DataFrame to only include rows where industry_code is 'Total Gross Value Added'
df_GGVA_quarterly_filtered = df_GGVA_quarterly[df_GGVA_quarterly['industry_code'] == 'Total Gross Value Added']

# Drop duplicates based on 'financial_year' and 'quarterly_code', keeping the first occurrence
df_GGVA_quarterly_filtered  = df_GGVA_quarterly_filtered .drop_duplicates(subset=['financial_year', 'quarterly_code'])

# on GVA growth
# Boolean indexing to filter rows where both constant_price and current_price are not NaN
df_filtered_GVA = df_GVA_growth[(~df_GVA_growth['constant_price_growth'].isna()) & (~df_GVA_growth['current_price_growth'].isna())]

# If you want to reset index after filtering
df_filtered_GVA.reset_index(drop=True, inplace=True)
df_filtered_GVA_for_annually = df_filtered_GVA.copy()
 
import pandas as pd
import numpy as np

# Assuming df_filtered_GVA is your DataFrame

# Define the priority order dictionary
revision_code_priority_order = {
    'Third Revised Estimates': 1,
    'Second Revised Estimates':2,
    'First Revised Estimates': 3,
    'Provisional Estimates': 4,
    'Second Advance Estimates': 5,
    'First Advance Estimates': 6
}

# Convert the industry_code to numeric, so NaNs are sorted first
df_filtered_GVA_for_annually['industry_code'] = pd.to_numeric(df_filtered_GVA_for_annually['industry_code'], errors='coerce')

# Map revision_code to its priority order
df_filtered_GVA_for_annually['revision_code_priority'] = df_filtered_GVA_for_annually['revision_code'].map(revision_code_priority_order)

# Sort the DataFrame
df_sorted = df_filtered_GVA_for_annually.sort_values(by=['financial_year', 'revision_code_priority', 'industry_code'],
                                        ascending=[True, True, True])

# Group by 'financial_year' and select the first row from each group
df_GGVA_annually_sorted = df_sorted.groupby('financial_year').first().reset_index()

# Filter df_GVA based on quarterly_code
df_GGVA_growth_quarterly = df_filtered_GVA[df_filtered_GVA['quarterly_code'] != 'NA']

# Filter the DataFrame to only include rows where industry_code is 'Total Gross Value Added'
df_GGVA_growth_quarterly_filtered = df_GGVA_growth_quarterly[df_GGVA_growth_quarterly['industry_code'] == 'Total GVA Growth Rate']

# Drop duplicates based on 'financial_year' and 'quarterly_code', keeping the first occurrence
df_GGVA_growth_quarterly_filtered = df_GGVA_growth_quarterly_filtered.drop_duplicates(subset=['financial_year', 'quarterly_code'])

# Merging GVA

# Example merge operation
df_GVA_Annually_merged = pd.merge(df_GGVA_annually_final,df_GGVA_annually_sorted[['financial_year', 'quarterly_code', 'revision_code', 'industry_code', 'frequency_code', 'current_price_growth', 'constant_price_growth']],
                    on=['financial_year', 'quarterly_code', 'revision_code', 'frequency_code'],
                    how='left')

# Example merge operation
df_GVA_Quarterly_merged = pd.merge(df_GGVA_quarterly_filtered,df_GGVA_growth_quarterly_filtered[['financial_year', 'quarterly_code', 'revision_code', 'industry_code', 'frequency_code', 'current_price_growth', 'constant_price_growth']],
                    on=['financial_year', 'quarterly_code', 'revision_code', 'frequency_code'],
                    how='left')
df_GVA_Quarterly_merged

# Final GDP

# Concatenate result_GDP_annually and df_GDP_filtered
df_GDP_Final = pd.concat([df_GDP_Annually_merged, df_GDP_Quarterly_merged])

# Reset the index of df_GDP_Final
df_GDP_Final.reset_index(drop=True, inplace=True)

# df_GDP_Final.fillna("NA", inplace=True)

# Final GVA

# Concatenate result_GDP_annually and df_GDP_filtered
df_GVA_Final = pd.concat([df_GVA_Annually_merged, df_GVA_Quarterly_merged])

# Reset the index of df_GDP_Final
df_GVA_Final.reset_index(drop=True, inplace=True)

# df_GVA_Final.fillna("NA", inplace=True)

# Final Data Frame

# Finally combning dataframe to work upon
df = pd.concat([df_GVA_Final, df_GDP_Final])
df = df.reindex(columns=['financial_year', 'indicator_code', 'quarterly_code', 'revision_code', 'industry_code', 'frequency_code', 'constant_price', 'current_price', 'constant_price_growth', 'current_price_growth'])
# df.fillna('NA', inplace=True)

#######################################################################################################################################################
#######################################################################################################################################################

# Create a Dash application
external_stylesheets = [
    {
        "href": "https://fonts.googleapis.com/css2?family=Lato:wght@400;700&display=swap",
        "rel": "stylesheet",
    },
    {
        "href": "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css",
        "rel": "stylesheet",
    },
]

#app = dash.Dash(__name__, external_stylesheets=external_stylesheets, suppress_callback_exceptions=True)
app = dash.Dash(__name__, external_stylesheets=external_stylesheets, routes_pathname_prefix='/viz/nas/', requests_pathname_prefix='/viz/nas/')
app.title = "National Accounts Statistics"

# Default figure for initial graph display
default_fig = go.Figure()

# App layout
app.layout = html.Div(
    className="content-wrapper",
    children=[
        html.Div(
            style={'flex': '0 1 320px', 'padding': '10px', 'boxSizing': 'border-box',},
            #  'width': '300px', 'height': '100vh'
            children=[
                html.H1(
                    html.Div(
                        "Select Parameters to Get Chart",
                        className="parameter-data",
                        style={'fontSize': '15px', 'fontWeight': 'normal'},
                    ),
                    style={'marginBottom': '0px', 'marginTop': '20px'}
                ),
                html.Div(
                    children=[
                        html.Div(children="Series", className="menu-title"),
                        dcc.Dropdown(
                            id="series-dropdown",
                            options=[
                                {'label':'All','value':'All'},
                                {'label': 'Current', 'value': 'Current'},
                                {'label': 'Back ', 'value': 'Back'},
                            ],
                            value='All',
                            placeholder="series-type",
                            clearable=False,
                            searchable=False,
                        ),
                    ],
                    style={'marginBottom': '0px'}
                ),
                html.Div(
                    children=[
                        html.Div(children="Indicator", className="menu-title"),
                        dcc.Dropdown(
                            id="indicator-dropdown",
                            options=[{'label': str(i), 'value': i} for i in df['indicator_code'].unique()],
                            multi=False,
                            clearable=False,
                            className="dropdown",
                            placeholder="Select Indicator",
                            searchable=False,
                            value="Gross Domestic Product",  # Adjust default value if necessary
                        ),

                    ],
                    style={'marginBottom': '0px'}
                ),
                html.Div(
                    children=[
                        html.Div(children="Frequency", className="menu-title"),
                        dcc.Dropdown(
                            id="frequency-dropdown",
                            options=[{'label': i, 'value': i} for i in df['frequency_code'].unique()],
                            clearable=False,
                            placeholder="Frequency",
                            searchable=False,
                            className="dropdown",
                            value="Annual",
                        ),
                    ],
                    style={'marginBottom': '0px'}
                ),

                html.Div(
                    children=[
                        html.Div(children="Price Type", className="menu-title"),
                        dcc.Dropdown(
                            id="price-type-dropdown",
                            options=[
                                {'label': 'Current Price', 'value': 'current_price'},
                                {'label': 'Constant Price', 'value': 'constant_price'}
                            ],
                            value='constant_price',
                            placeholder="Price Type",
                            clearable=False,
                            searchable=False,
                        ),
                    ],
                    style={'marginBottom': '0px'}
                ),

                html.Div(
                    children=[
                        html.Div(children="Financial Year", className="menu-title"),
                        dcc.Dropdown(
                            id="financial-year-dropdown",
                            options=[
                                {'label': 'Select All', 'value': 'Select All'}
                            ] + [{'label':str(year), 'value': year} for year in df['financial_year'].unique()],
                            multi=True,
                            placeholder="Select Financial Year",
                            className="dropdown",
                            value=['Select All'],  # Select all by default
                        ),
                    ],
                    style={'marginBottom': '0px'}
                ),

                html.Button(
                    'Apply', id='apply-button', n_clicks=0, className='mr-1',
                    style={
                        'width': '100%',
                        'background': 'radial-gradient(circle, #0a266c 0, #085858 3%, #0a266c 94%)',
                        'color': 'white',
                        'border': 'none',
                        'padding': '10px 20px',
                        'text-align': 'center',
                        'text-decoration': 'none',
                        'display': 'inline-block',
                        'font-size': '16px',
                        'margin': '15px 0',
                        'cursor': 'pointer',
                        'border-radius': '8px',
                        'marginTop': '30px',
                        'marginBottom': '0px'
                    }
                ),
               # Inside app.layout within the HTML structure where buttons are placed
                html.Button(
                       'Reset', id='reset-button', n_clicks=0, className='mr-1',
                        style={
                          'width': '100%',
                          'background': 'radial-gradient(circle, #0a266c 0, #085858 3%, #0a266c 94%)',
                         'color': 'white',
                         'border': 'none',
                         'padding': '10px 20px',
                         'text-align': 'center',
                         'text-decoration': 'none',
                          'display': 'inline-block',
                          'font-size': '16px',
                          'margin': '15px 0',
                          'cursor': 'pointer',
                           'border-radius': '8px',
                           'marginTop': '30px',
                         'marginBottom': '0px'
                      }
                ),
                html.Button(
                    'Download', id='download-svg-button', n_clicks=0, className='mr-1',
                    style={
                        'width': '100%',
                        'background': 'radial-gradient(circle, #0a266c 0, #085858 3%, #0a266c 94%)',
                        'color': 'white',
                        'border': 'none',
                        'padding': '10px 20px',
                        'text-align': 'center',
                        'text-decoration': 'none',
                        'display': 'inline-block',
                        'font-size': '16px',
                        'margin': '20px 0',
                        'cursor': 'pointer',
                        'border-radius': '8px',
                        'marginBottom': '0px'
                    }
                ),

                html.Div(
                    id='error-message',
                    style={'color': 'red', 'textAlign': 'center', 'marginTop': '20px'}
                ),
            ]
        ),
        dcc.Download(id="download-svg"),
        html.Div(
            style={'flex': '1', 'padding': '20px', 'position': 'relative', 'text-align': 'center', 'height': 'calc(100% - 50px)'},
            children=[
                dcc.Loading(
                    id="loading-graph",
                    type="circle", color='#83b944',  # or "default"
                    children=[
                        html.Div(
                            id='graph-container',
                            style={ 'position': 'relative'},  # Adjust height as needed 'width': '100%', 'height': 'calc(100vh - 150px)',
                            children=[
                                html.Div(
                                    className="loader",
                                    id="loading-circle",
                                    style={"position": "absolute", "top": "50%", "left": "50%", "transform": "translate(-50%, -50%)"}
                                ),
                                dcc.Graph(
                                    id="time-series-plot",
                                    config={"displayModeBar": False},
                                    # style={'width': '100%', 'height': '100%'}  # Ensure the graph takes full container size
                                ),
                            ]
                        ),
                    ]
                ),
            ],
        ),
    ]
)



@app.callback(
    Output("frequency-dropdown", "options"),
    Output("financial-year-dropdown", "options"),
    [ Input("series-dropdown", "value")]
)
def update_financial_year_options(series_selected):
    print('Selected Series:',series_selected)
    

    # Extract unique financial years
    financial_year = (list(df['financial_year'].unique()))
    print('Financial Years List:',financial_year)
    # Create dropdown options
    
    options,financial_year_updated = get_years_list(series_selected,financial_year)

    options1 = ""
    if series_selected=="Back":
        options1=[{'label':'Annual','value':'Annual'}]
    else:
        options1=[{'label':'Annual','value':'Annual'}]+[{'label':'Quarterly','value':'Quarterly'}]


    return options1,options



def get_years_list(series_selected,financial_year):
    financial_year_updated = []

    options = ''
    if series_selected == 'Back':
        for year in financial_year:
            if int(year[0:4]) <2012:
                financial_year_updated.append(year)
                options = [{'label': 'Select All', 'value': 'Select All'}] + [{'label': str(year), 'value': year} for year in financial_year_updated]

    elif series_selected == 'Current':
        for year in financial_year:
            #print('int(year[0:4])',int(year[0:4]))
            if int(year[0:4]) >=2011:
                financial_year_updated.append(year)
                options = [{'label': 'Select All', 'value': 'Select All'}] + [{'label': str(year), 'value': year} for year in financial_year_updated]

    else:
        for year in financial_year:
            if int(year[0:4]) >= 1950:
                financial_year_updated.append(year)          
                options = [{'label': 'Select All', 'value': 'Select All'}] + [{'label': str(year), 'value': year} for year in financial_year_updated]
    return options,financial_year_updated

@app.callback(
    [Output("time-series-plot", "figure"),
     Output("error-message", "children"),
     Output('graph-container', 'style'),],
    [Input('apply-button', 'n_clicks'),],
    [State("indicator-dropdown", "value"),
     State("frequency-dropdown", "value"),
     State("price-type-dropdown", "value"),
     State("financial-year-dropdown", "value"),
     State("series-dropdown", "value")
     ]
)
def update_plot(n_clicks_plot, selected_indicator, selected_frequency, selected_price_type, selected_years,series_selected):
    ctx = dash.callback_context

    if not ctx.triggered:
        button_id = None
    else:
        button_id = ctx.triggered[0]["prop_id"].split(".")[0]

    if button_id == "plot-button":
        if n_clicks_plot == 0 or not (selected_indicator and selected_frequency):
            return dash.no_update, "", {'display': 'none'}, selected_indicator, selected_frequency, selected_financial_years

        if not selected_financial_years or 'Select All' in selected_financial_years:
            selected_financial_years = df['financial_year'].unique()
            
            
    if not selected_frequency or not selected_price_type or not selected_years:
        return default_fig, "", {'display': 'none'}
    
    if not selected_indicator:
        return dash.no_update, "Please select an indicator.", {'display': 'none'}
    
    if not isinstance(selected_indicator, list):
        selected_indicator = [selected_indicator]

    # Handle 'Select All' for financial years
    if 'Select All' in selected_years:
        selected_years = df['financial_year'].unique()

    filtered_df = df[
        (df['frequency_code'] == selected_frequency) &
        (df['indicator_code'].isin(selected_indicator)) &
        
        (df['financial_year'].isin(selected_years))  # Filter by selected financial years
    ]

    if filtered_df.empty:
        return dash.no_update, f"No data found for {selected_frequency} frequency, {selected_indicator}, and selected financial years. Please try another combination.", {'display': 'none'}

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    #filtered_df should contain only those data which are according to selected series

    p,financial_year_updated = get_years_list(series_selected,filtered_df['financial_year'])
    filtered_df = filtered_df[filtered_df['financial_year'].isin(financial_year_updated)]

    for indicator in selected_indicator:
        indicator_df = filtered_df[filtered_df['indicator_code'] == indicator]

        if selected_frequency == 'Annual' :
            x_axis = indicator_df['financial_year']
            tickangle = 270  # Set tickangle to 0 for Annual data
        elif selected_frequency == 'Quarterly':
            x_axis = [f"{quarter} {year}" for quarter, year in zip(indicator_df['quarterly_code'], indicator_df['financial_year'])]
            tickangle = 270  # Set tickangle to 270 for Quarterly data
        fig.add_trace(go.Bar(
            x=x_axis,
            y=indicator_df[selected_price_type],
            name=f'{indicator} - {selected_price_type.replace("_", " ").title()}',
            marker_color='#0F4366' if selected_price_type in ['current_price', 'constant_price'] else 'red',
            legendgroup=f'{indicator}-{selected_price_type}',
        ), secondary_y=False)

        growth_type = f"{selected_price_type}_growth"
        if series_selected=='All' or series_selected=='Current':
            fig.add_trace(go.Scatter(
                x=x_axis,
                y=indicator_df[growth_type],
                mode='lines+markers',
                name=f'{indicator} - {growth_type.replace("_", " ").title()}',
                marker=dict(symbol='circle', size=8),
                line=dict(shape='linear'),
                legendgroup=f'{indicator}-{growth_type}',
                text = [f"{val:.1f}%" for val in indicator_df[growth_type]],
                hoverinfo='text+x',  # Show only text and x in the hover tooltip
                ), secondary_y=True)

   
    fig.update_layout(
        xaxis_title='Financial Year' if selected_frequency == 'Annual' else 'Quarters',
        template='plotly_white',
        xaxis_title_font=dict(size=18, family='Arial, sans-serif', color='black', weight='bold'),
        yaxis_title_font=dict(size=18, family='Arial, sans-serif', color='black', weight='bold'),
        font_color='black',
        margin=dict(t=0),
        # width=1520,
        # height=760,
        xaxis=dict(
            tickangle=tickangle  # Set the tickangle based on selected_frequency
        ),
        legend=dict(
            yanchor="top",
            y=1.1,
            xanchor="right"
        )
    )
    if series_selected=='Current':

        fig.update_xaxes(type='category', color='black')
        fig.update_yaxes(title_text='Price (₹ Crore)', color='black', secondary_y=False)  
        fig.update_yaxes(title_text='Growth Rate (%)', title_font=dict(size=18, family='Arial, sans-serif', color='black', weight='bold'), secondary_y=True)
    elif series_selected=='All':
        fig.update_xaxes(type='category', color='black')
        fig.update_yaxes(title_text='Price (₹ Crore)', color='black', secondary_y=False)  
        fig.update_yaxes(title_text='Growth Rate (%)', title_font=dict(size=18, family='Arial, sans-serif', color='black', weight='bold'), secondary_y=True)
    else:
        fig.update_xaxes(type='category', color='black')
        fig.update_yaxes(title_text='Price (₹ Crore)', color='black', secondary_y=False)  

    return fig, "", {'display': 'block'}

# Callback to reset dropdowns
@app.callback(
    [
        Output('series-dropdown', 'value'),
        Output('indicator-dropdown', 'value'),
        Output('frequency-dropdown', 'value'),
        Output('price-type-dropdown', 'value'),
        Output('financial-year-dropdown', 'value')
    ],
    [Input('reset-button', 'n_clicks')],
    [State('series-dropdown', 'value'),
     State('indicator-dropdown', 'value'),
     State('frequency-dropdown', 'value'),
     State('price-type-dropdown', 'value'),
     State('financial-year-dropdown', 'value')]
)
def reset_dropdowns(n_clicks, series, indicator, frequency, price_type, financial_year):
    if n_clicks > 0:
        return 'All', 'Gross Domestic Product', 'Annual', 'constant_price', ['Select All']
    return series, indicator, frequency, price_type, financial_year


# Define callback to download SVG
@app.callback(
    Output("download-svg", "data"),
    Input("download-svg-button", "n_clicks"),
    State("time-series-plot", "figure"),
    prevent_initial_call=True
)
def download_svg(n_clicks, figure):
    if n_clicks > 0:
        # Create the SVG content
        fig = go.Figure(figure)
        svg_str = pio.to_image(fig, format="svg")

        # Create a BytesIO buffer and write the SVG string to it
        buffer = io.BytesIO()
        buffer.write(svg_str)
        buffer.seek(0)

        # Return the SVG data for download
        return dcc.send_bytes(buffer.getvalue(), "plot.svg")


# Run the app
if __name__ == '__main__':
    # app.run_server(debug=True,dev_tools_ui=False, dev_tools_props_check=False, port=4574,host='localhost' )
    app.run_server(debug=True, port=4574,host='localhost')


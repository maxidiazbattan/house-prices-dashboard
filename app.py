#Importing the libraries.
import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc

import plotly.graph_objs as go
import plotly.express as px
from dash.dependencies import Input, Output

import pandas as pd
import numpy as np


# =================================================================
# Data  
# =================================================================
df_data = pd.read_csv("dataset/house_prices.csv", index_col=0)

df_data["size_m2"] = df_data["GROSS SQUARE FEET"] / 10.764
df_data = df_data[df_data["YEAR BUILT"] > 0]
df_data["SALE DATE"] = pd.to_datetime(df_data["SALE DATE"])

df_data.loc[df_data["size_m2"] > 10000, "size_m2"] = 10000
df_data.loc[df_data["SALE PRICE"] > 50000000, "SALE PRICE"] = 50000000
df_data.loc[df_data["SALE PRICE"] < 100000, "SALE PRICE"] = 100000

locations = {
    1: "Manhattan",
    2: "Bronx",
    3: "Brooklyn",
    4:"Queens",
    5: "Staten Island ",
}

df_data['BOROUGH NAMES'] = df_data['BOROUGH'].map(locations)


list_of_locations = {
    "All": 0,
    "Manhattan": 1,
    "Bronx": 2,
    "Brooklyn": 3,
    "Queens": 4,
    "Staten Island ": 5,
}

slider_size = [20, 100, 1000, 10000]

app = dash.Dash(__name__,external_stylesheets = [dbc.themes.CYBORG]) 
server = app.server


app.layout = dbc.Container([
    dbc.Row([
            dbc.Col([
                      dcc.Store(id='store-global'),
                        html.Img(id="logo", src=app.get_asset_url("new-york.png"), style={"width": 50, 'height': 70}),
                        html.H4("House prices - NYC", style={"margin-top": "20px"}),
                        html.P(
                        """Real estate prices in New York City over the years. """
                        ),

                        html.H5("""Disctrict""", style={"margin-top": "30px", "margin-bottom": "30px"}),
                        dcc.Dropdown(
                            id="location-dropdown",
                            options=[{"label": i, "value": j} for i, j in list_of_locations.items()],
                            value=0,
                            placeholder="Select a borought"),

                        html.H5("""Square mts (m2)""", style={"margin-top": "20px"}),

                        dcc.Slider(min=0, max=3, id='slider-square-size', value=3,
                        marks = {i: str(j)for i, j in enumerate(slider_size)}),

                        html.H5("""Variable to analize""", style={"margin-top": "20px"}),
                        
                        dcc.Dropdown(
                            options=[
                                {'label': 'LAND SQUARE FEET', 'value': 'LAND SQUARE FEET'},
                                {'label': 'TAX CLASS', 'value': 'TAX CLASS AT TIME OF SALE'},
                                {'label': 'SALE PRICE', 'value': 'SALE PRICE'},
                            ],
                            value='SALE PRICE',
                            id="dropdown-color"), ],width={'size':3}),

         dbc.Col([
                  dcc.Graph(id="map-graph", figure={},)
                 
         ], width={'size':9}),

    ], className="mb-0"),


    dbc.Row([
         dbc.Col([
                  dcc.Graph(id="hist-graph", figure={}, style={'height': '150px'}),
                  ], width={'size':4, 'offset': 3}),

        dbc.Col([
                  dcc.Graph(id="bar-graph", figure={}, style={'height': '150px'}),
         
                ], width={'size':5,}),
         ], className="mt-0"),

], fluid=True)


# ========================================================
# Callbacks 
@app.callback([Output('map-graph', 'figure'), 
              Output('hist-graph', 'figure'),
              Output('bar-graph', 'figure')
              ],
              [
               Input('location-dropdown', 'value'), 
               Input('slider-square-size', 'value'), 
               Input('dropdown-color', 'value')
               ]            
             )

def update_hist(location, square_size, color):

    if location is None:
            df_intermediate = df_data.copy()
    else:

        size_limit = slider_size[square_size] if square_size is not None else df_data["size_m2"].max() 
        df_intermediate = df_data[df_data["BOROUGH"] == location] if location != 0 else df_data.copy()
        df_intermediate = df_intermediate[df_intermediate["size_m2"] <= size_limit]


    # ==========================
    # Map

    map_fig=px.scatter_mapbox(df_intermediate, lat="LATITUDE", lon="LONGITUDE", color=color, 
                     size="size_m2", size_max=20, zoom=10, opacity=0.4)
    map_fig.update_layout(mapbox_style="carto-darkmatter")
    map_fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, 
                  mapbox=dict(
                      pitch=10,
                      bearing=30,
                  ))
    
    color_scale = px.colors.sequential.Plasma

    map_fig.update_coloraxes(colorscale=color_scale)
    map_fig.update_layout(coloraxis_showscale=False)


    # ==========================
    # Histogram
    hist_fig = px.histogram(df_intermediate, x=color, opacity=0.75, color_discrete_sequence=color_scale)
    hist_fig.update_layout(margin=dict(t=100, b=0, l=70, r=40),
                  hovermode="x unified", 
                  template="plotly_dark", 
                  title= f'{color.capitalize()} variablility', 
                  xaxis_title=' ', yaxis_title=" ",
                  paper_bgcolor='rgba(0,0,0,0)',
                  plot_bgcolor='rgba(0,0,0,0)',
                  title_font=dict(size=15, color='#a5a7ab', family="Lato, sans-serif"),
                  font=dict(color='#8a8d93', size=6))


    # ==========================
    # Bar
    df_intermediate['NEIGHBORHOOD'] = df_intermediate['NEIGHBORHOOD'].str.split('-').apply(lambda x: x[0])
    neigh = df_intermediate.groupby('NEIGHBORHOOD')[color].mean().sort_values(ascending=False).astype(int)

    bar_fig = px.bar(data_frame=neigh.iloc[0:10], x=neigh.index[0:10], y=color, color_discrete_sequence=color_scale)
    bar_fig.update_layout(margin=dict(t=100, b=0, l=70, r=40),
                  hovermode="x unified", 
                  template="plotly_dark", 
                  title= f' Top 10 Neighborhoods by {color.capitalize()}', 
                  xaxis_title=' ', yaxis_title=" ",
                  paper_bgcolor='rgba(0,0,0,0)',
                  plot_bgcolor='rgba(0,0,0,0)',
                  title_font=dict(size=15, color='#a5a7ab', family="Lato, sans-serif"),
                  font=dict(color='#8a8d93', size=5))


    return map_fig, hist_fig, bar_fig

if __name__ =='__main__':
    app.run_server(host='127.0.0.1',port=8500, use_reloader=False)

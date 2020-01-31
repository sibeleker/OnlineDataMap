#!/usr/bin/env python
# coding: utf-8

# In[9]:


import pandas as pd
import numpy as np
import math

import geopandas as gpd
import json

from bokeh.io import output_notebook, show, output_file
from bokeh.plotting import figure
from bokeh.models import GeoJSONDataSource, LinearColorMapper, ColorBar, NumeralTickFormatter
from bokeh.palettes import brewer

from bokeh.io.doc import curdoc
from bokeh.models import Slider, HoverTool, Select
from bokeh.layouts import widgetbox, row, column

# Create a function the returns json_data for the year selected by the user
def json_data(df):   
    # Fill the null values
    #df = df.fillna(0)
    
    # Bokeh uses geojson formatting, representing geographical features, with json
    # Convert to json
    df_json = json.loads(df.to_json())
    
    # Convert to json preferred string-like object 
    json_data = json.dumps(df_json)
    return json_data

# Create a plotting function
def make_plot(field_name):
    # Set the format of the colorbar
    min_range = format_df.loc[format_df['field'] == field_name, 'min_range'].iloc[0]
    max_range = format_df.loc[format_df['field'] == field_name, 'max_range'].iloc[0]
    field_format = format_df.loc[format_df['field'] == field_name, 'format'].iloc[0]

    # Instantiate LinearColorMapper that linearly maps numbers in a range, into a sequence of colors.
    color_mapper = LinearColorMapper(palette = palette, low = min_range, high = max_range)

    # Create color bar.
    format_tick = NumeralTickFormatter(format=field_format)
    color_bar = ColorBar(color_mapper=color_mapper, label_standoff=18, formatter=format_tick,
    border_line_color=None, location = (0, 0))

    # Create figure object.
    verbage = format_df.loc[format_df['field'] == field_name, 'verbage'].iloc[0]

    p = figure(title = verbage, 
             plot_height = 550, plot_width = 900,
             toolbar_location = None)
    p.xgrid.grid_line_color = None
    p.ygrid.grid_line_color = None
    p.axis.visible = False

    # Add patch renderer to figure. 
    p.patches('xs','ys', source = geosource, fill_color = {'field' : field_name, 'transform' : color_mapper},
          line_color = 'black', line_width = 0.25, fill_alpha = 1)
  
    # Specify color bar layout.
    p.add_layout(color_bar, 'right')

    # Add the hover tool to the graph
    p.add_tools(hover)
    return p

# Define the callback function: update_plot
def update_plot(attr, old, new):
    
    # The input cr is the criteria selected from the select box
    cr = select.value
    input_field = format_df.loc[format_df['verbage'] == cr, 'field'].iloc[0]
    
    # Update the plot based on the changed inputs
    p = make_plot(input_field)
    
    # Update the layout, clear the old document and display the new document
    layout = column(p, widgetbox(select))
    curdoc().clear()
    curdoc().add_root(layout)



directory = "H:/MyDocuments/IIASA-Felix/DietChange_SocialMedia/"

df_fb = pd.read_excel("H:/MyDocuments/IIASA-Felix/DietChange_SocialMedia/fractions.xlsx")
df_fb.set_index('Unnamed: 0', inplace=True)

df_gt = pd.read_excel(directory+'GoogleTrends/data/Global_byregion_topic_v2.xlsx')
df_gt.set_index('geoName', inplace=True)
df_gt = df_gt[df_gt.index!='Taiwan']
df_gt = df_gt / df_gt.max(axis=0)

df_w = pd.read_excel(directory+'Wikipedia_vegetarians.xlsx', sheet_name='Sheet1')
df_w = df_w[['Country', 'Updated figure', 'FLEXITARIAN', 'Data set year']]
df_w['Country'] = df_w['Country'].str.strip()
df_w = df_w.set_index('Country')
df_w.columns = ['Vegetarian-Survey', 'Flexitarian-Survey', 'Dataset']
df_w = df_w.dropna(how='all')

world = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres'))
world.loc[world.name == 'United States of America','name'] = 'United States'

collist = {'FB_vegetarianism' : 'Jan-veg-mau', 
           'FB_sustainable_living' : 'Jan-sus-mau', 
           'GT_vegetarianism' : 'Vegetarianism', 
           'GT_sustainable_living' : 'Sustainable living', 
           'Surveys' : 'Vegetarian-Survey'}

for index, row in world.iterrows():
    cnt = row['name']
    for key, value in collist.items():
        try:
            if key.startswith('F'):
                world.loc[index, key] = round(df_fb.loc[cnt, value], 2)
            elif key.startswith('G'):
                world.loc[index, key] = round(df_gt.loc[cnt, value], 2)
            else:
                world.loc[index, key] = round(df_w.loc[cnt, value], 2)

        except:
            world.loc[index, key] = 'NA'


data = json_data(world)

# This dictionary contains the formatting for the data in the plots
format_data = [('FB_vegetarianism', 0, 0.25,'0.00', 'Fraction of Facebook audience interested in vegetarianism'),
               ('FB_sustainable_living', 0, 0.1,'0.00', 'Fraction of Facebook audience interested in sustainable living'),
               ('GT_vegetarianism', 0, 1, '0.00', 'GoogleTrends interest in vegetarianism'),
               ('GT_sustainable_living', 0, 1,'0.00', 'GoogleTrends interest in sustainable living'),
               ('Surveys', 0, 0.3,'0.00', 'Survey results on the vegetarian fraction of the population')
              ]
 
#Create a DataFrame object from the dictionary 
format_df = pd.DataFrame(format_data, columns = ['field' , 'min_range', 'max_range' , 'format', 'verbage'])
geosource = GeoJSONDataSource(geojson = data)

input_field = 'FB_vegetarianism'

# Define a sequential multi-hue color palette.
palette = brewer['Blues'][8]

# Reverse color order so that dark blue is highest obesity.
palette = palette[::-1]

# Add hover tool
hover = HoverTool(tooltips = [ ('Country','@name'),
                               ('Fraction of Facebook audience interested in vegetarianism', '@FB_vegetarianism{%0.f}'),
                               ('Fraction of Facebook audience interested in sustainable living', '@FB_sustainable_living{%0.f}'),
                               ('GoogleTrends interest in vegetarianism', '@GT_vegetarianism{0.0f}'),
                               ('GoogleTrends interest in sustainable living', '@GT_sustainable_living{0.0f}'),
                               ('Surveys', '@Surveys{%0.f}')])

# Call the plotting function
p = make_plot(input_field)

# Make a selection object: select
select = Select(title='Select Criteria:', value='Fraction of Facebook audience interested in vegetarianism', 
                options=['Fraction of Facebook audience interested in vegetarianism', 
                         'Fraction of Facebook audience interested in vegetarianism',
                       'GoogleTrends interest in vegetarianism', 'GoogleTrends interest in sustainable living',
                       'Surveys'])
select.on_change('value', update_plot)

# Make a column layout of widgetbox(slider) and plot, and add it to the current document
# Display the current document
layout = column(p, widgetbox(select))
curdoc().add_root(layout)


# In[95]:


# Use the following code to test in a notebook, comment out for transfer to live site
# Interactive features will not show in notebook

# output_notebook()
# show(p)



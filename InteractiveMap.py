#!/usr/bin/env python
# coding: utf-8

# In[32]:


import pandas as pd
import numpy as np
import math

import geopandas as gpd
import json

from bokeh.io import output_notebook, show, output_file, save
from bokeh.plotting import figure
from bokeh.models import GeoJSONDataSource, LinearColorMapper, ColorBar, NumeralTickFormatter
from bokeh.palettes import brewer

from bokeh.io.doc import curdoc
from bokeh.models import Slider, HoverTool, Select
from bokeh.layouts import widgetbox, row, column


# In[2]:


directory = "H:/MyDocuments/IIASA-Felix/DietChange_SocialMedia/"


# In[3]:


# i need to get the FB data, GT data and the survey data

df_fb = pd.read_excel("H:/MyDocuments/IIASA-Felix/DietChange_SocialMedia/fractions.xlsx")
df_fb.set_index('Unnamed: 0', inplace=True)
df_fb.head()


# In[4]:



df_gt = pd.read_excel(directory+'GoogleTrends/data/Global_byregion_topic_v2.xlsx')
df_gt.set_index('geoName', inplace=True)
df_gt = df_gt[df_gt.index!='Taiwan']
df_gt = df_gt / df_gt.max(axis=0)

df_gt.tail()


# In[5]:


df_w = pd.read_excel(directory+'Wikipedia_vegetarians.xlsx', sheet_name='Sheet1')
df_w = df_w[['Country', 'Updated figure', 'FLEXITARIAN', 'Data set year']]
df_w['Country'] = df_w['Country'].str.strip()
df_w = df_w.set_index('Country')
df_w.columns = ['Vegetarian-Survey', 'Flexitarian-Survey', 'Dataset']
df_w = df_w.dropna(how='all')

df_w.head()


# In[6]:


# get the map

world = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres'))
world.loc[world.name == 'United States of America','name'] = 'United States'


# In[7]:


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


# In[8]:


world.head()


# In[9]:


world = world[world['name']!='Antarctica']


# In[10]:


world[world['name']=='Australia']


# In[11]:


world[world['Surveys']!='NA'].max()


# In[12]:


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


# In[13]:


data = json_data(world)


# In[83]:


# This dictionary contains the formatting for the data in the plots
format_data = [('FB_vegetarianism', 0, 0.25,'0.00', 'Fraction of Facebook audience interested in vegetarianism', 'Greens'),
               ('FB_sustainable_living', 0, 0.1,'0.00', 'Fraction of Facebook audience interested in sustainable living', 'Blues'),
               ('GT_vegetarianism', 0, 1, '0.00', 'GoogleTrends interest in vegetarianism', 'Greens'),
               ('GT_sustainable_living', 0, 1,'0.00', 'GoogleTrends interest in sustainable living', 'Blues'),
               ('Surveys', 0, 0.3,'0.00', 'Survey results for vegetarian population', 'Greens')
              ]
 
#Create a DataFrame object from the dictionary 
format_df = pd.DataFrame(format_data, columns = ['field' , 'min_range', 'max_range' , 'format', 'verbage', 'colormap'])


# In[62]:


geosource = GeoJSONDataSource(geojson = data)


# In[97]:


# Create a plotting function
def make_plot(field_name):
    # Set the format of the colorbar
    min_range = format_df.loc[format_df['field'] == field_name, 'min_range'].iloc[0]
    max_range = format_df.loc[format_df['field'] == field_name, 'max_range'].iloc[0]
    field_format = format_df.loc[format_df['field'] == field_name, 'format'].iloc[0]
    cmap = format_df.loc[format_df['field'] == field_name, 'colormap'].iloc[0]
    # Define a sequential multi-hue color palette.
    palette = brewer[cmap][8]
    palette = palette[::-1]

    # Instantiate LinearColorMapper that linearly maps numbers in a range, into a sequence of colors.
    color_mapper = LinearColorMapper(palette = palette, low = min_range, high = max_range)

    # Create color bar.
    format_tick = NumeralTickFormatter(format=field_format)
    color_bar = ColorBar(color_mapper=color_mapper, label_standoff=18, formatter=format_tick,
    border_line_color=None, location = (0, 0))

    # Create figure object.
    verbage = format_df.loc[format_df['field'] == field_name, 'verbage'].iloc[0]

    TOOLS = "hover,save,pan,box_zoom,reset,wheel_zoom,tap"
    
    p = figure(title = verbage, 
             plot_height = 500, plot_width = 900, tools=TOOLS, toolbar_location='below',)
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
  


# In[98]:


# Define the callback function: update_plot
def update_plot(attr, old, new):
    
    # The input cr is the criteria selected from the select box
    cr = select.value
    print(cr)
    input_field = format_df.loc[format_df['verbage'] == cr, 'field'].iloc[0]
    print(input_field)
    # Update the plot based on the changed inputs
    p = make_plot(input_field)
    
    # Update the layout, clear the old document and display the new document
    layout = column(p, widgetbox(select))
    curdoc().clear()
    curdoc().add_root(layout)
    
    p.source.data = data


# In[99]:


# Input geojson source that contains features for plotting for:
# initial year 2018 and initial criteria sale_price_median

input_field = 'FB_vegetarianism'

# Add hover tool
hover = HoverTool(tooltips = [ ('Country','@name'),
                               ('Fraction of Facebook audience interested in vegetarianism', '@FB_vegetarianism{%0.f}'),
                               ('Fraction of Facebook audience interested in sustainable living', '@FB_sustainable_living{%0.f}'),
                               ('GoogleTrends interest in vegetarianism', '@GT_vegetarianism{0.0f}'),
                               ('GoogleTrends interest in sustainable living', '@GT_sustainable_living{0.0f}'),
                               ('Survey results for vegetarian population', '@Surveys{%0.f}')])

# Call the plotting function
p = make_plot(input_field)

# Make a selection object: select
select = Select(title='Select Criteria:', value='Fraction of Facebook audience interested in vegetarianism', 
                options=['Fraction of Facebook audience interested in vegetarianism', 
                         'Fraction of Facebook audience interested in sustainable living',
                       'GoogleTrends interest in vegetarianism', 'GoogleTrends interest in sustainable living',
                       'Survey results for vegetarian population'])
select.on_change('value', update_plot)
#p.add_tools(hover, tap)
# Make a column layout of widgetbox(slider) and plot, and add it to the current document
# Display the current document
layout = column(p, widgetbox(select))
curdoc().add_root(layout)


# In[100]:


# Use the following code to test in a notebook, comment out for transfer to live site
# Interactive features will not show in notebook
output_notebook()
#show(p)
show(layout)


# In[101]:


output_file(directory+'map.html')
save(layout)


# In[44]:




# from bokeh.resources import CDN
# from bokeh.embed import file_html

# #plot = figure()
# #plot.circle([1,2], [3,4])

# html = file_html(column(select, p), CDN, "my plot")

# with open(directory+"map.html", 'w') as f:
#     f.write(html)


# In[40]:


# import bokeh
# bokeh.__version__


# The Local Bokeh Server
# I developed the static map using 2018 data and Median Sales Price in Colab in order to get the majority of the code working prior to adding the interactive portions. In order to test and view the interactive components of Bokeh, we need to follow these steps.
# 
# Install the Bokeh server on your computer.
# 
# Download the .ipynb file to a local directory on your computer.
# 
# From the terminal change the directory to the directory with the .ipynb file.
# 
# From the terminal run the following command: bokeh serve (two dashes)show filename.ipynb
# 
# This should open a local host on your browser and output your interactive graph. If there is an error it should be visible in the terminal.

# Public Access to the Interactive Graph via Heroku
# Once you get the interactive graph working locally, you can let others access it by using a public Bokeh hosting service such as Heroku. Heroku will host the interactive graph allowing you to link to it or use an iframe (as in this article).
# 
# The basic steps to host on Heroku are:
# 
# Change the Colab notebook to comment out the install of fiona and geopandas. Heroku has these items and the build will fail if they are in the code.
# 
# Change the Colab notebook to comment out the last two lines (output_notebook() and show(p)).
# 
# Download the Colab notebook as a .py file and upload it to a GitHub repository.
# 
# Create a Heroku app and connect to your GitHub repository containing your .py file.
# 
# Create a Procfile and requirements.txt file. See mine in my GitHub.
# 
# Run the app!

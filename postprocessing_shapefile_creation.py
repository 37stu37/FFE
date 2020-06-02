# Commented out IPython magic to ensure Python compatibility.
# %%time
# %%capture
# !apt update
# !apt upgrade
# !apt install gdal-bin python-gdal python3-gdal
# # Install rtree - Geopandas requirment
# !apt install python3-rtree
# # Install Geopandas
# !pip install git+git://github.com/geopandas/geopandas.git
# # Install descartes - Geopandas requirment
# !pip install descartes
# !pip install memory_profiler
#
# Commented out IPython magic to ensure Python compatibility.
# %%time
import datetime
import glob
import shutil
from math import sqrt
import os
import matplotlib.pyplot as plt
import bokeh
import numpy as np
import pandas as pd
import geopandas as gpd
from scipy.spatial import distance
from shapely.geometry import box
from shapely.geometry import shape
from shapely.geometry import Point
import networkx as nx
from sys import getsizeof
from numba import jit
import dask.dataframe as dd
import dask.array as da
import dask
from dask.distributed import Client
from dask.diagnostics import ProgressBar
# %matplotlib inline
# %load_ext memory_profiler
# 
# pd.options.mode.chained_assignment = None  # default='warn'

client = Client(processes=False)
client

path_output = '/Volumes/NO NAME'

# @dask.delayed
def read_and_concatenate_parquets(prefix, path=path_output):
  L = []
  files = glob.glob(os.path.join(path_output, 'output', prefix))# output_scenario_0_step_0.parquet
  for file in files:
    pqt = dd.read_parquet(file)
    L.append(pqt)
  df = dd.concat(L)
  return df

def count_fid_occurences(df):
  count = df['source'].value_counts().compute()
  count_df = count.to_frame()
  return count_df

def load_shapefile(file_name, minx, miny, maxx, maxy):
    # crop data
    bbox = box(minx, miny, maxx, maxy)
    # building point dataset
    gdf_buildings = gpd.read_file(os.path.join('shapefile',file_name), bbox=bbox)
    max_extent = gdf_buildings.total_bounds
    data_size = getsizeof(gdf_buildings) /(1024.0**3)
    print("Shapefile extent : {}".format(max_extent))
    print("Asset loaded : {}".format(len(gdf_buildings)))
    # gdf.plot(column='IgnProb_bl', cmap='hsv', legend=True)
    return gdf_buildings

def merge_coordinates_export_shape(ddf, gdf, name_output):
  gdf = gdf[['TARGET_FID', 'geometry']]
  df = pd.DataFrame(gdf)
  # ddf = ddf.compute()
  df_merge = ddf.merge(df, how='left', left_on='source', right_on='TARGET_FID')
  gdf_merge = gpd.GeoDataFrame(df_merge, geometry='geometry')
  gdf_merge.plot(column='count', cmap='seismic', legend=True)
  gdf_merge.to_file(os.path.join(path_output, "results", name_output + ".shp"))
  return gdf_merge


df = read_and_concatenate_parquets("scenario*")
count_df = count_fid_occurences(df)

gdf = load_shapefile("buildings_raw.shp", 1740508, 5420049, 1755776, 5443033) # whole

gdf_count = merge_coordinates_export_shape(count_df, gdf, "burned_buildings")
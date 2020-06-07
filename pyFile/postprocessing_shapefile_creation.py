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
import glob
import os
from sys import getsizeof

import dask.dataframe as dd
import geopandas as gpd
import pandas as pd
from dask.distributed import Client
from shapely.geometry import box


client = Client(processes=False)
client

path_output = '/Volumes/NO NAME'

# @dask.delayed
def read_and_concatenate_parquets(prefix, path=path_output):
  L = []
  files = glob.glob(os.path.join(path_output, 'output', prefix))# output_scenario_0_step_0.parquet
  for file in files:
    print("file loaded : {}".format(file))
    pqt = dd.read_parquet(file)
    L.append(pqt)
  df = dd.concat(L)
  return df

def count_fid_occurences(df):
  count = df['source'].value_counts().compute()
  count_df = pd.DataFrame({'source': count.index, 'count': count.values})
  return count_df

def load_shapefile(file_name, minx, miny, maxx, maxy):
    # crop data
    bbox = box(minx, miny, maxx, maxy)
    # building point dataset
    gdf_buildings = gpd.read_file(os.path.join('../data/shapefile', file_name), bbox=bbox)
    max_extent = gdf_buildings.total_bounds
    data_size = getsizeof(gdf_buildings) /(1024.0**3)
    print("Shapefile extent : {}".format(max_extent))
    print("Asset loaded : {}".format(len(gdf_buildings)))
    gdf_buildings.plot(column='IgnProb_bl', cmap='hsv', legend=True)
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
# count_df = count_fid_occurences(df)
# print(count_df.head(5))
#
# gdf = load_shapefile("buildings_raw.shp", 1740508, 5420049, 1755776, 5443033) # whole
#
# gdf_count = merge_coordinates_export_shape(count_df, gdf, "burned_buildings")
#
# # plot map with background tile
# import contextily as ctx
# gdf_count = gdf_count.to_crs(epsg=3857) # "web mercator"
# ax = gdf_count.plot(column='count', cmap='seismic', legend=True, alpha=0.3)
# ctx.add_basemap(ax) #, zoom=12)


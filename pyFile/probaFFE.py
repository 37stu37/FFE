#%%
import glob
from math import sqrt
import matplotlib.pyplot as plt
from matplotlib.pyplot import imshow
import numpy as np
import pandas as pd
import geopandas as gpd
import geoparquet as gpq
import math
from shapely.geometry import Point

import dask.dataframe as dd
from dask.diagnostics import ProgressBar
import dask_geopandas as dg



from pathlib import Path
import os
import glob

import re
from tqdm import tqdm

# %matplotlib inline
from IPython.core.interactiveshell import InteractiveShell
InteractiveShell.ast_node_interactivity = "all"

pbar = ProgressBar()
pbar.register()

#%%
# district data
sa = gpd.read_file('data/shapefile/Finn_SA2Summary.shp')
sa = sa[['BldgFloo_1', 'PopDensity', 'NumberBldg', 'geometry']] # drop column not used in caluclation of Ignition
sa = gpd.GeoDataFrame(sa, crs="EPSG:2193")
sa_dask = dg.from_geopandas(sa, npartitions=8)
del sa

# pga events
pga = pd.read_parquet('/Users/alex/Dropbox/Work/Repository/OpenQuake/output/PGAxy.parquet')
pgaGeo = gpd.GeoDataFrame(pga, geometry=gpd.points_from_xy(pga.lon, pga.lat, crs="EPSG:2193"))
pga_dask = dg.from_geopandas(pgaGeo, npartitions=8)
del pga
del pgaGeo

#%%
# join both 
def dask_sjoin(dd1, dd2):
    join = gpd.sjoin(dd1, dd2, op="within")
    return join

PGA_SA = dd.map_partitions(dask_sjoin, pga_dask, sa_dask)

#%%
PGA_SA.compute()
#%%
PGA_SA.to_file('/Users/alex/Dropbox/Work/GNS/008_FFE/ProbaFFE/PGA_SA.parquet')
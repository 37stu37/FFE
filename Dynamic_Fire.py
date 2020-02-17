import os
import geopandas as gpd
import matplotlib.pyplot as plt
import rasterio
from rasterio.plot import show
from osgeo import gdal_array
import numpy as np
import pandas as pd
import imageio
import random

path_to_data = ''

fuel_map = gpd.read_file('/content/drive/My Drive/04_Cloud/01_Work/GNS/008_FFE/merge.shp')
fuel_map.plot()
fuel_map.crs
fuel_map.info()
fuel_map.SHAPE_Area.min()


raster = gdal_array.LoadFile('/content/drive/My Drive/04_Cloud/01_Work/GNS/008_FFE/FuelMapRaster.tif')
type(raster)


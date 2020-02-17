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

# Load data needed
# fuel_map = gpd.read_file('/content/drive/My Drive/04_Cloud/01_Work/GNS/008_FFE/merge.shp')
# fuel_map.plot()
# fuel_map.crs
# fuel_map.info()
# fuel_map.SHAPE_Area.min()
def Load_data(path):
    # load building map as a "fuel" map
    fuel_map = gdal_array.LoadFile(os.path.join(path, 'FuelMapRaster.tif'))
    # load probability of building ignition as an array
    ignition_probability_map = gdal_array.LoadFile('FireProba.tif')
    # load wind data
    wind_df = pd.read('WindScenariosCopy.csv')
    return fuel_map, ignition_probability_map, wind_df

fuel_map, ignition_probability_map, wind_df =  Load_data()

def Fire_ignition(ignition_proba_array=ignition_probability_map):
    random_ignition_proba_array = np.zeros_like(ignition_proba_array, float)
    random_ignition_proba_array = np.random.uniform(low=0, high=1, size= ignition_proba_array)
    # get position of fire
    i, j = np.where(ignition_proba_array < random_ignition_proba_array)
    return i, j



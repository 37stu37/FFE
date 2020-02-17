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

path = ''


# Load data needed
# fuel_map = gpd.read_file('/content/drive/My Drive/04_Cloud/01_Work/GNS/008_FFE/merge.shp')
# fuel_map.plot()
# fuel_map.crs
# fuel_map.info()
# fuel_map.SHAPE_Area.min()
def Load_data(path=path):
    # load building map as a "fuel" map
    fuel_map = gdal_array.LoadFile(os.path.join(path, 'FuelMapRaster.tif'))
    # load probability of building ignition as an array
    ignition_probability_map = gdal_array.LoadFile('FireProba.tif')
    # load wind data
    wind_df = pd.read('WindScenariosCopy.csv')
    return fuel_map, ignition_probability_map, wind_df


fuel_map, ignition_probability_map, wind_df = Load_data()

# cells 0 = Clear, 1 = Fuel, 2 = Fire

def Fire_ignition(ignition_proba_array=ignition_probability_map, fuel_map=fuel_map):
    random_ignition_proba_array = np.zeros_like(ignition_proba_array, float)
    random_ignition_proba_array = np.random.uniform(low=0, high=1, size=ignition_proba_array)
    # get position of fire
    difference = ignition_proba_array - random_ignition_proba_array
    difference[difference < 0] = 1
    difference[difference > 0] = 0
    ignition_map = difference + fuel_map
    return ignition_map

def Wind_scenario(wind_data=wind_df):
    i = random(0, wind_data.shape[0])
    wind_direction = wind_data.iloc[i, 2]
    critical_distance = wind_data.iloc[i, 1]
    return wind_direction, critical_distance

def Fire_propagation(fuel_map, wind_direction, critical_distance, ignition_map):
    # states hold the state of each cell
    for time in range(0, 1000):
    time = 0
    states = np.zeros((time, *fuel_map))
    states[0] = states(time, *ignition_map)

    # Make a copy of the original states
    time = time + 1
    states[time] = states[time - 1].copy()

    for x in range(1, fuel_map[0] - 1):
        for y in range(1, fuel_map[1] - 1):

            if states[time - 1, x, y] == 2 and wind_direction == 'buffer':  # It's on fire
                # If there's fuel surrounding it
                # set it on fire!
                if states[time - 1, x + 1, y] == 1:
                    states[time, x + 1, y] = 2
                if states[time - 1, x - 1, y] == 1:
                    states[time, x - 1, y] = 2
                if states[time - 1, x, y + 1] == 1:
                    states[time, x, y + 1] = 2
                if states[time - 1, x, y - 1] == 1:
                    states[time, x, y - 1] = 2
                if states[time - 1, x + 1, y - 1] == 1:
                    states[time, x + 1, y - 1] = 2
                if states[time - 1, x + 1, y + 1] == 1:
                    states[time, x + 1, y + 1] = 2
                if states[time - 1, x - 1 , y - 1] == 1:
                    states[time, x - 1, y - 1] = 2
                if states[time - 1, x - 1 , y - 1] == 1:
                    states[time, x - 1, y - 1] = 2



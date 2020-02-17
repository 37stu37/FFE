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
def load_data(path=path):
    # load building map as a "fuel" map
    fuel_map = gdal_array.LoadFile(os.path.join(path, 'FuelMapRaster.tif'))  # 0 = no fuel; 1 = fuel
    # load probability of building ignition as an array
    ignition_probability_map = gdal_array.LoadFile('FireProba.tif')  # proba from 0 to 1
    # load wind data
    wind_df = pd.read('WindScenariosCopy.csv')
    return fuel_map, ignition_probability_map, wind_df


fuel_map, ignition_probability_map, wind_df = load_data()


def wind_scenario(wind_data=wind_df):
    i = np.random.randint(0, wind_data.shape[0])
    wind_direction = wind_data.iloc[i, 2]
    critical_distance = wind_data.iloc[i, 1]
    return wind_direction, critical_distance


wind_direction, critical_distance = wind_scenario()


def fire_propagation(fuel_map=fuel_map, wind_direction=wind_direction, critical_distance=critical_distance, ignition_probability_map=ignition_probability_map):
    # fire hold the state of each cell
    time_total = 1000
    ignition = np.zeros((time_total, *fuel_map))
    fire = np.zeros((time_total, *fuel_map))

    # initialize fire by creating random ignition from ignition probability map
    ignition[0] = np.random.choice([0, 1], size=fuel_map,
                                   p=ignition_probability_map)  # ignition must not happen in non fuel cells !!
    fire[0] = ignition[0] + fuel_map  # 0 = no fuel, 1 = fuel, 2 = fire

    for time in range(1, time_total, 1):
        # Make a copy of the original fire
        fire[time] = fire[time - 1].copy()
        for x in range(1, fuel_map[0] - 1):
            for y in range(1, fuel_map[1] - 1):
                for d in range(critical_distance, 1, -1):
                    if fire[time - 1, x, y] == 2 and wind_direction == 'buffer':  # It's on fire
                        # If there's fuel surrounding it
                        # set it on fire!
                        if fire[time - 1, x - critical_distance, y + critical_distance] == 1:
                            fire[time, x - critical_distance, y + critical_distance] = 2
                        if fire[time - 1, x, y + critical_distance] == 1:
                            fire[time, x, y + critical_distance] = 2
                        if fire[time - 1, x + critical_distance, y + critical_distance] == 1:
                            fire[time, x + critical_distance, y + critical_distance] = 2
                        if fire[time - 1, x + critical_distance, y] == 1:
                            fire[time, x + critical_distance, y] = 2
                        if fire[time - 1, x + critical_distance, y - critical_distance] == 1:
                            fire[time, x + critical_distance, y - critical_distance] = 2
                        if fire[time - 1, x, y - critical_distance] == 1:
                            fire[time, x, y - critical_distance] = 2
                        if fire[time - 1, x - critical_distance, y - critical_distance] == 1:
                            fire[time, x - critical_distance, y - critical_distance] = 2
                        if fire[time - 1, x - critical_distance, y] == 1:
                            fire[time, x - critical_distance, y] = 2

                    if fire[time - 1, x, y] == 2 and wind_direction == 'N':  # It's on fire
                        # set it on fire!
                        if fire[time - 1, x - critical_distance, y + critical_distance] == 1:
                            fire[time, x - critical_distance, y + critical_distance] = 2
                        if fire[time - 1, x, y + critical_distance] == 1:
                            fire[time, x, y + critical_distance] = 2
                        if fire[time - 1, x + critical_distance, y + critical_distance] == 1:
                            fire[time, x + critical_distance, y + critical_distance] = 2

                    if fire[time - 1, x, y] == 2 and wind_direction == 'NE':  # It's on fire
                        # set it on fire!
                        if fire[time - 1, x, y + critical_distance] == 1:
                            fire[time, x, y + critical_distance] = 2
                        if fire[time - 1, x + critical_distance, y + critical_distance] == 1:
                            fire[time, x + critical_distance, y + critical_distance] = 2
                        if fire[time - 1, x + critical_distance, y] == 1:
                            fire[time, x + critical_distance, y] = 2

                    if fire[time - 1, x, y] == 2 and wind_direction == 'E':  # It's on fire
                        # set it on fire!
                        if fire[time - 1, x + critical_distance, y + critical_distance] == 1:
                            fire[time, x + critical_distance, y + critical_distance] = 2
                        if fire[time - 1, x + critical_distance, y] == 1:
                            fire[time, x + critical_distance, y] = 2
                        if fire[time - 1, x + critical_distance, y - critical_distance] == 1:
                            fire[time, x + critical_distance, y + critical_distance] = 2

                    if fire[time - 1, x, y] == 2 and wind_direction == 'SE':  # It's on fire
                        # set it on fire!
                        if fire[time - 1, x + critical_distance, y] == 1:
                            fire[time, x + critical_distance, y] = 2
                        if fire[time - 1, x + critical_distance, y - critical_distance] == 1:
                            fire[time, x + critical_distance, y + critical_distance] = 2
                        if fire[time - 1, x, y - critical_distance] == 1:
                            fire[time, x, y - critical_distance] = 2

                    if fire[time - 1, x, y] == 2 and wind_direction == 'S':  # It's on fire
                        # set it on fire!
                        if fire[time - 1, x, y - critical_distance] == 1:
                            fire[time, x, y - critical_distance] = 2
                        if fire[time - 1, x - critical_distance, y - critical_distance] == 1:
                            fire[time, x - critical_distance, y - critical_distance] = 2
                        if fire[time - 1, x + critical_distance, y - critical_distance] == 1:
                            fire[time, x + critical_distance, y - critical_distance] = 2

                    if fire[time - 1, x, y] == 2 and wind_direction == 'SW':  # It's on fire
                        # set it on fire!
                        if fire[time - 1, x, y - critical_distance] == 1:
                            fire[time, x, y - critical_distance] = 2
                        if fire[time - 1, x - critical_distance, y - critical_distance] == 1:
                            fire[time, x - critical_distance, y - critical_distance] = 2
                        if fire[time - 1, x - critical_distance, y] == 1:
                            fire[time, x - critical_distance, y] = 2

                    if fire[time - 1, x, y] == 2 and wind_direction == 'W':  # It's on fire
                        # set it on fire!
                        if fire[time - 1, x - critical_distance, y + critical_distance] == 1:
                            fire[time, x - critical_distance, y + critical_distance] = 2
                        if fire[time - 1, x - critical_distance, y - critical_distance] == 1:
                            fire[time, x - critical_distance, y - critical_distance] = 2
                        if fire[time - 1, x - critical_distance, y] == 1:
                            fire[time, x - critical_distance, y] = 2

                    if fire[time - 1, x, y] == 2 and wind_direction == 'NW':  # It's on fire
                        # set it on fire!
                        if fire[time - 1, x - critical_distance, y + critical_distance] == 1:
                            fire[time, x - critical_distance, y + critical_distance] = 2
                        if fire[time - 1, x - critical_distance, y] == 1:
                            fire[time, x - critical_distance, y] = 2
                        if fire[time - 1, x, y + critical_distance] == 1:
                            fire[time, x, y + critical_distance] = 2

                    if np.array_equal(fire[time], fire[time - 1]) == True:
                        pass
                    else:
                        continue

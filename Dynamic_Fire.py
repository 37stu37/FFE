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

path = 'E:\Current_work\FFE\dynamic_fire'


def load_data(path_to_data=path):
    # load building map as a "fuel" map
    fuel = gdal_array.LoadFile(os.path.join(path_to_data, 'FuelMapRaster.tif'))  # 0 = no fuel; 1 = fuel
    # load probability of building ignition as an array
    ignition = gdal_array.LoadFile('FireProba.tif')  # probability from 0 to 1
    # load wind data
    wind = pd.read('WindScenariosCopy.csv')
    return fuel, ignition, wind


fuel_map, ignition_probability_map, wind_df = load_data()


def wind_scenario(wind_data=wind_df):
    i = np.random.randint(0, wind_data.shape[0])
    wind = wind_data.iloc[i, 2]
    distance = wind_data.iloc[i, 1]
    return wind, distance


wind_direction, critical_distance = wind_scenario()


def fire_propagation(scenarios, fuel=fuel_map, wind=wind_direction, distance=critical_distance,
                     ignition_map=ignition_probability_map):

    for scenario in range(scenarios):
        # fire hold the state of each cell
        time_total = 1000
        ignition = np.zeros((time_total, *fuel))
        fire = np.zeros((time_total, *fuel))
        fire_list = []
        # initialize fire by creating random ignition from ignition probability map
        ignition[0] = np.random.choice([0, 1], size=fuel,
                                       p=ignition_map)  # ignition must not happen in non fuel cells !!
        fire[0] = ignition[0] + fuel  # 0 = no fuel, 1 = fuel, 2 = fire

        for time in range(1, time_total, 1):
            # Make a copy of the original fire
            fire[time] = fire[time - 1].copy()
            for x in range(1, fuel[0] - 1):
                for y in range(1, fuel[1] - 1):
                    for d in range(distance, 1, -1):
                        if fire[time - 1, x, y] == 2 and wind == 'buffer':  # It's on fire
                            # If there's fuel surrounding it
                            # set it on fire!
                            if fire[time - 1, x - distance, y + distance] == 1:
                                fire[time, x - distance, y + distance] = 2
                            if fire[time - 1, x, y + distance] == 1:
                                fire[time, x, y + distance] = 2
                            if fire[time - 1, x + distance, y + distance] == 1:
                                fire[time, x + distance, y + distance] = 2
                            if fire[time - 1, x + distance, y] == 1:
                                fire[time, x + distance, y] = 2
                            if fire[time - 1, x + distance, y - distance] == 1:
                                fire[time, x + distance, y - distance] = 2
                            if fire[time - 1, x, y - distance] == 1:
                                fire[time, x, y - distance] = 2
                            if fire[time - 1, x - distance, y - distance] == 1:
                                fire[time, x - distance, y - distance] = 2
                            if fire[time - 1, x - distance, y] == 1:
                                fire[time, x - distance, y] = 2

                        if fire[time - 1, x, y] == 2 and wind == 'N':  # It's on fire
                            # set it on fire!
                            if fire[time - 1, x - distance, y + distance] == 1:
                                fire[time, x - distance, y + distance] = 2
                            if fire[time - 1, x, y + distance] == 1:
                                fire[time, x, y + distance] = 2
                            if fire[time - 1, x + distance, y + distance] == 1:
                                fire[time, x + distance, y + distance] = 2

                        if fire[time - 1, x, y] == 2 and wind == 'NE':  # It's on fire
                            # set it on fire!
                            if fire[time - 1, x, y + distance] == 1:
                                fire[time, x, y + distance] = 2
                            if fire[time - 1, x + distance, y + distance] == 1:
                                fire[time, x + distance, y + distance] = 2
                            if fire[time - 1, x + distance, y] == 1:
                                fire[time, x + distance, y] = 2

                        if fire[time - 1, x, y] == 2 and wind == 'E':  # It's on fire
                            # set it on fire!
                            if fire[time - 1, x + distance, y + distance] == 1:
                                fire[time, x + distance, y + distance] = 2
                            if fire[time - 1, x + distance, y] == 1:
                                fire[time, x + distance, y] = 2
                            if fire[time - 1, x + distance, y - distance] == 1:
                                fire[time, x + distance, y + distance] = 2

                        if fire[time - 1, x, y] == 2 and wind == 'SE':  # It's on fire
                            # set it on fire!
                            if fire[time - 1, x + distance, y] == 1:
                                fire[time, x + distance, y] = 2
                            if fire[time - 1, x + distance, y - distance] == 1:
                                fire[time, x + distance, y + distance] = 2
                            if fire[time - 1, x, y - distance] == 1:
                                fire[time, x, y - distance] = 2

                        if fire[time - 1, x, y] == 2 and wind == 'S':  # It's on fire
                            # set it on fire!
                            if fire[time - 1, x, y - distance] == 1:
                                fire[time, x, y - distance] = 2
                            if fire[time - 1, x - distance, y - distance] == 1:
                                fire[time, x - distance, y - distance] = 2
                            if fire[time - 1, x + distance, y - distance] == 1:
                                fire[time, x + distance, y - distance] = 2

                        if fire[time - 1, x, y] == 2 and wind == 'SW':  # It's on fire
                            # set it on fire!
                            if fire[time - 1, x, y - distance] == 1:
                                fire[time, x, y - distance] = 2
                            if fire[time - 1, x - distance, y - distance] == 1:
                                fire[time, x - distance, y - distance] = 2
                            if fire[time - 1, x - distance, y] == 1:
                                fire[time, x - distance, y] = 2

                        if fire[time - 1, x, y] == 2 and wind == 'W':  # It's on fire
                            # set it on fire!
                            if fire[time - 1, x - distance, y + distance] == 1:
                                fire[time, x - distance, y + distance] = 2
                            if fire[time - 1, x - distance, y - distance] == 1:
                                fire[time, x - distance, y - distance] = 2
                            if fire[time - 1, x - distance, y] == 1:
                                fire[time, x - distance, y] = 2

                        if fire[time - 1, x, y] == 2 and wind == 'NW':  # It's on fire
                            # set it on fire!
                            if fire[time - 1, x - distance, y + distance] == 1:
                                fire[time, x - distance, y + distance] = 2
                            if fire[time - 1, x - distance, y] == 1:
                                fire[time, x - distance, y] = 2
                            if fire[time - 1, x, y + distance] == 1:
                                fire[time, x, y + distance] = 2

                        fire[time].plot()

                        if np.array_equal(fire[time], fire[time - 1]) == True:
                            fire_list.append(fire[time])
                            pass
                        else:
                            continue
        return fire_list


final_fire_maps = fire_propagation(1)

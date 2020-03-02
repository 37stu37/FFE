import math
import os
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import box
import random
from mesa import Model, Agent
from mesa.time import RandomActivation
from mesa.space import Grid
from mesa.datacollection import DataCollector
from mesa.batchrunner import BatchRunner
from mesa_geo import GeoSpace, GeoAgent, AgentCreator
from mesa.visualization.modules import CanvasGrid
from mesa.visualization.ModularVisualization import ModularServer

path = "G:/Sync/FFE/Mesa"


def load_data(file_name):
    # crop data
    minx, miny = 1748570, 5426959
    maxx, maxy = 1748841, 5427115
    bbox = box(minx, miny, maxx, maxy)
    # building point dataset
    gdf_buildings = gpd.read_file(os.path.join(path, file_name), bbox=bbox)
    gdf_buildings.IgnProb_bl = 0.5
    # xmin,ymin,xmax,ymax = gdf_buildings.total_bounds
    return gdf_buildings


def wind_scenario():
    wind_data = pd.read_csv(os.path.join(path, 'GD_wind.csv'))
    i = np.random.randint(0, wind_data.shape[0])
    w = wind_data.iloc[i, 2]
    d = wind_data.iloc[i, 1]
    return w, d


def calculate_distance(point1, point2):
    # need geometry from geopandas
    d = point1.distance(point2)
    return d


def plot(df, column_df):
    fig, ax = plt.subplots(1, 1)
    df.plot(column=column_df, ax=ax, legend=True)
    plt.show()


def build_edge_list(gdf=None):
    source = pd.DataFrame(gdf, copy=True)
    # source = gdf.copy()
    source['id'] = source.index
    target = source.copy()
    source.columns = ['source_' + str(col) for col in source.columns]
    target.columns = ['target_' + str(col) for col in target.columns]
    source.rename(columns={'source_id': 'source'}, inplace=True)
    target.rename(columns={'target_id': 'target'}, inplace=True)
    source = source[
        ['source_IgnProb_bl', 'source_X', 'source_Y', 'source_LON', 'source_LAT', 'source_geometry', 'source']]
    target = target[
        ['target_IgnProb_bl', 'target_X', 'target_Y', 'target_LON', 'target_LAT', 'target_geometry', 'target']]
    list_of_dataframes = []
    tmp = target.copy()
    for index, row in source.iterrows():



    for i in source.index:
        for c in source.columns:
            n = source.columns.get_loc(c)
            tmp[c] = source.iloc[i][n]
            # print(tmp.head(10))
            # tmp['distance'] = np.sqrt(((source.source_X - target.target_X) ** 2) + ((source.source_Y - target.target_Y) ** 2))
            # # tmp = tmp[tmp.distance < 45]
            list_of_dataframes.append(tmp)
            tmp = target.copy()
    c = pd.concat(list_of_dataframes)
    return c, target, source


gdf = load_data("buildings_raw_pts.shp")
edge, target, source = build_edge_list(gdf)

import math
import os
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import box
from pyproj import Geod
import random
from mesa import Model, Agent
from mesa.time import RandomActivation
from mesa.space import Grid
from mesa.datacollection import DataCollector
from mesa.batchrunner import BatchRunner
from mesa_geo import GeoSpace, GeoAgent, AgentCreator
from mesa.visualization.modules import CanvasGrid
from mesa.visualization.ModularVisualization import ModularServer

# path = "G:/Sync/FFE/Mesa"
path = '/Users/alex/Google Drive/05_Sync/FFE/Mesa'

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


# def calculate_distance(point1, point2):
#     # need geometry from geopandas
#     d = point1.distance(point2)
#     return d
def eudistance(v1, v2):
    return np.linalg.norm(v1 - v2)


def plot(df, column_df):
    fig, ax = plt.subplots(1, 1)
    df.plot(column=column_df, ax=ax, legend=True)
    plt.show()


def build_edge_list(geodataframe, maximum_distance):
    # create arrays for different id combination
    n = np.arange(0, len(geodataframe))
    target = [n] * len(geodataframe)
    target = np.hstack(target)
    source = np.repeat(n, len(geodataframe))
    # put arrays in dataframe
    df = pd.DataFrame()
    df['source_id'] = source
    df['target_id'] = target
    # merge source attributes with source index
    geo_df = geodataframe.copy()
    geo_df['id'] = geo_df.index
    # create source / target gdf from gdf.columns of interest
    geo_df = geo_df[['id', 'TARGET_FID', 'X', 'Y', 'LON', 'LAT', 'geometry', 'IgnProb_bl']]
    geo_df_TRG = geo_df.copy()
    geo_df_TRG.columns = ['target_' + str(col) for col in geo_df_TRG.columns]
    geo_df_SRC = geo_df.copy()
    geo_df_SRC.columns = ['source_' + str(col) for col in geo_df_SRC.columns]
    # merge data
    merged_data = pd.merge(df, geo_df_SRC, left_on='source_id', right_on='source_id', how='outer')
    merged_data = pd.merge(merged_data, geo_df_TRG, left_on='target_id', right_on='target_id', how='outer')
    merged_data.rename(columns={'source_id': 'source', 'target_id': 'target'}, inplace=True)
    # calculate distance for each source / target pair
    merged_data['v1'] = merged_data.source_X - merged_data.target_X
    merged_data['v2'] = merged_data.source_Y - merged_data.target_Y
    merged_data['euc_distance'] = np.hypot(merged_data.v1, merged_data.v2)
    # remove when distance "illegal"
    valid_distance = merged_data['euc_distance'] < maximum_distance
    not_same_node = merged_data['euc_distance'] != 0
    data = merged_data[valid_distance & not_same_node]
    return data

def create_network(edge_list):


gdf = load_data("buildings_raw_pts.shp")
edge_list = build_edge_list(gdf, 45)

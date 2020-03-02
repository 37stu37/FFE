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
    n = np.arange(0, len(gdf))
    target = [n] * len(gdf)
    target = np.hstack(target)
    source = np.repeat(n, len(gdf))
    # put arrays in dataframe
    df = pd.DataFrame()
    df['id'] = df.index
    df['source_idx'] = source
    df['target_idx'] = target
    # merge source attributes with source index
    gdf = geodataframe.copy()
    gdf['id'] = gdf.index
    # create source / target gdf from gdf.columns of interest
    gdf = gdf[['TARGET_FID','X', 'Y', 'LON', 'LAT', 'geometry', 'IgnProb_bl']]
    gdf_TRG = gdf.copy()
    gdf_TRG.columns = ['target_' + str(col) for col in target.columns]
    gdf_SRC = gdf.copy()
    gdf_SRC.columns = ['source_' + str(col) for col in source.columns]
    # merge data
    merged_data = pd.merge(df, gdf, left_on='id', right_on='source_idx', how='outer', suffixes=('', '_SRC'))
    merged_data = pd.merge(merged_data, gdf, left_on='id', right_on='target_idx', how='outer', suffixes=('', '_TRG'))
    # calculate distance for each source / target pair
    merged_data['distance'] =


    source = pd.DataFrame(geodataframe, copy=True)
    gdf = geodataframe.copy()
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

    target_copy = target.copy()
    for i in source.index:
        for c in source.columns:
            target_copy[c] = source[c][i]
            # calculate distance and filter
            # join['Vx'] = join.source_X - join.target_X
            # join['Vy'] = join.source_Y - join.target_Y
            # join['distance'] = eudistance(join.Vx, join.Vy)
            # join = join[(join.distance < maximum_distance) & (join.distance != 0)]
            list_of_dataframes.append(target_copy)
            target_copy = target.copy()

    concat_df = pd.concat(list_of_dataframes)
    return concat_df


gdf = load_data("buildings_raw_pts.shp")
edge_list = build_edge_list(gdf, 45)

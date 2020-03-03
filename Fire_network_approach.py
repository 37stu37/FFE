import math
import os
from enum import Enum

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import geopandas as gpd
import pyproj
from shapely.geometry import box
import networkx as nx
# from time
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
from mesa.space import NetworkGrid

pd.options.mode.chained_assignment = None  # default='warn'

path = "G:/Sync/FFE/Mesa"
path_output = "G:\Sync\FFE\FireNetwork"


# path = '/Users/alex/Google Drive/05_Sync/FFE/Mesa'

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
    b = wind_data.iloc[i, 3]
    return w, d, b


def eudistance(v1, v2):
    return np.linalg.norm(v1 - v2)


def calculate_initial_compass_bearing(pointA, pointB):
    """
    Calculates the bearing between two points.
    The formulae used is the following:
        θ = atan2(sin(Δlong).cos(lat2),
                  cos(lat1).sin(lat2) − sin(lat1).cos(lat2).cos(Δlong))
    :Parameters:
      - `pointA: The tuple representing the latitude/longitude for the
        first point. Latitude and longitude must be in decimal degrees
      - `pointB: The tuple representing the latitude/longitude for the
        second point. Latitude and longitude must be in decimal degrees
    :Returns:
      The bearing in degrees
    :Returns Type:
      float
    """
    if (type(pointA) != tuple) or (type(pointB) != tuple):
        raise TypeError("Only tuples are supported as arguments")

    lat1 = math.radians(pointA[0])
    lat2 = math.radians(pointB[0])

    diffLong = math.radians(pointB[1] - pointA[1])

    x = math.sin(diffLong) * math.cos(lat2)
    y = math.cos(lat1) * math.sin(lat2) - (math.sin(lat1)
                                           * math.cos(lat2) * math.cos(diffLong))

    initial_bearing = math.atan2(x, y)

    # Now we have the initial bearing but math.atan2 return values
    # from -180° to + 180° which is not what we want for a compass bearing
    # The solution is to normalize the initial bearing as shown below
    initial_bearing = math.degrees(initial_bearing)
    compass_bearing = (initial_bearing + 360) % 360

    return compass_bearing


def calculate_azimuth(x1, y1, x2, y2):
    azimuth = math.degrees(math.atan2((x2 - x1), (y2 - y1)))
    return 360 + azimuth


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
    # calculate azimuth
    data['azimuth'] = np.degrees(np.arctan2(merged_data['v2'], merged_data['v1']))
    data['bearing'] = (data.azimuth + 360) % 360
    return data


def create_network(edge_list_dataframe):
    graph = nx.from_pandas_edgelist(edge_list_dataframe, edge_attr=True)
    options = {'node_color': 'red', 'node_size': 100, 'width': 1, 'alpha': 0.7,
               'with_labels': True, 'font_weight': 'bold'}
    nx.draw_kamada_kawai(graph, **options)
    plt.show()
    return graph


# set up
gdf = load_data("buildings_raw_pts.shp")
plot(gdf, gdf.IgnProb_bl)
edges = build_edge_list(gdf, 45)
G = create_network(edges)


# run model
# w_speed, w_direction = wind_scenario()

# run model
def set_initial_fire_to(df):
    """Fine = 0, Fire = 1, Burned = 2"""
    df['state'] = 0
    df['RNG'] = np.random.uniform(0, 1, df.shape[0])
    df['onFire'] = df['source_IgnProb_bl'] < df['RNG']
    df['state'] = df['onFire'].apply(lambda x: 1 if x == True else 0)
    ignitions = df[df.state == 1]
    if ignitions.empty:
        print('No ignition!')
        return
    # source nodes ignited
    return ignitions


def fire_spreading(df, wind_speed, wind_bearing, suppression_threshold, step=None, fire_df=None):
    if fire_df.empty:
        print('No Fire!')
        return
    # set up factor for fire spreading
    # suppression
    df['suppression'] = np.random.uniform(0, 1)
    are_not_suppressed = df['suppression'] < suppression_threshold
    # neighbors
    are_neighbors = df['euc_distance'] < wind_speed
    # wind
    wind_bearing_max = wind_bearing + 45
    wind_bearing_min = wind_bearing - 45
    if wind_bearing == 360:
        wind_bearing_max = 45
    if wind_bearing == 999:
        wind_bearing_max = 999
        wind_bearing_min = -999
    under_the_wind = (df['bearing'] < wind_bearing_max) & (df['bearing'] > wind_bearing_min)
    # spread fire based on condition
    fire = df[are_neighbors & under_the_wind & are_not_suppressed]
    fire.to_csv(os.path.join(path_output, "fire_step{}.csv".format(step)))
    return fire


for scenario in range():
    step = 0
    ini_fire = set_initial_fire_to(edges)
    w_speed, w_direction, w_bearing = wind_scenario()
    fire = fire_spreading(ini_fire, w_speed, w_bearing, 0.1, step)
    for step in range(len(edges)):
        fire = fire_spreading(fire, w_speed, w_bearing, 0.1, step)
        if fire.empty:
            break
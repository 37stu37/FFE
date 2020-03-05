import datetime
import glob
import math
import os
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import box
import networkx as nx

pd.options.mode.chained_assignment = None  # default='warn'

path = "G:/Sync/FFE/Mesa"
path_output = "G:\Sync\FFE\FireNetwork"

# path = '/Users/alex/Google Drive/05_Sync/FFE/Mesa'
# path_output = '/Users/alex/Google Drive/05_Sync/FFE/Mesa/output'


# path = '/Users/alex/Google Drive/05_Sync/FFE/Mesa'

def load_data(file_name):
    # crop data
    minx, miny = 1748570, 5426959
    maxx, maxy = 1748841, 5427115
    bbox = box(minx, miny, maxx, maxy)
    # building point dataset
    gdf_buildings = gpd.read_file(os.path.join(path, file_name), bbox=bbox)
    gdf_buildings.IgnProb_bl = 0.02
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
print("{} assets loaded".format(len(gdf)))
# plot(gdf, gdf.IgnProb_bl)
edges = build_edge_list(gdf, 45)
G = create_network(edges)


# run model
def set_initial_fire_to(df):
    """Fine = 0, Fire = 1, Burned = 2"""
    df['RNG'] = np.random.uniform(0, 1, size=len(df))  # add for random suppression per building, df.shape[0])
    onFire = df['source_IgnProb_bl'] > df['RNG']
    ignitions = df[onFire]
    # source nodes ignited
    sources_on_fire = list(ignitions.source)
    sources_on_fire = list(dict.fromkeys(sources_on_fire))
    return sources_on_fire


def set_fire_to(df, existing_fires):
    are_set_on_fire = (df['source'].isin(existing_fires))
    spark = df[are_set_on_fire]
    # source nodes ignited
    sources_on_fire = list(spark.source)
    sources_on_fire = list(dict.fromkeys(sources_on_fire))
    return sources_on_fire


def fire_spreading(list_fires, list_burn, wind_speed, wind_bearing, suppression_threshold, step_value, data=edges):
    # print("fire list in START def fire_spreading : {}".format(list_fires))
    # print("fire burn in START def fire_spreading : {}".format(list_burn))
    # check the fire potential targets
    print(list_fires)
    are_potential_targets = (data['source'].isin(list_fires))
    are_not_already_burned = (~data['target'].isin(list_burn))
    df = data[are_potential_targets & are_not_already_burned]
    # print(df.head(5))
    if df.empty:
        print("no fires")
        list_burn.extend(list(list_fires))
        list_burn = list(dict.fromkeys(list_burn))
        return [], list_burn  # to break the step loop
    # set up additional CONDITIONS for fire spreading
    # suppression
    df['random'] = np.random.uniform(0, 1, size=len(df))
    are_not_suppressed = df['random'] > suppression_threshold
    # neighbors distance
    are_neighbors = df['euc_distance'] < wind_speed
    # wind direction
    wind_bearing_max = wind_bearing + 45
    wind_bearing_min = wind_bearing - 45
    if wind_bearing == 360:
        wind_bearing_max = 45
    if wind_bearing <= 0:  # should not be necessary
        wind_bearing_min = 0
    if wind_bearing == 999:
        wind_bearing_max = 999
        wind_bearing_min = 0
    are_under_the_wind = (df['bearing'] < wind_bearing_max) & (df['bearing'] > wind_bearing_min)
    # spread fire based on condition
    fire_df = df
    # fire_df = df[are_neighbors & are_under_the_wind & are_not_suppressed]  # issues with "are_under_the_wind
    # print(len(fire_df.head(5)))
    # print(len(fire_df))
    list_burn.extend(list(list_fires))
    fire_df['step'] = step_value
    fire_df.to_csv(os.path.join(path_output, "step{}_fire.csv".format(step_value)))
    list_fires = list(dict.fromkeys(list(fire_df.target)))
    list_burn.extend(list(fire_df.target))
    list_burn = list(dict.fromkeys(list_burn))
    # print("fire list in END def fire_spreading : {}".format(list_fires))
    # print("fire burn in END def fire_spreading : {}".format(list_burn))
    return list_fires, list_burn


def log_files_concatenate(prefix, scenario_count):
    list_df = []
    files = glob.glob(os.path.join(path_output, prefix))
    if files:
        for file in files:
            # print(file)
            df = pd.read_csv(os.path.join(path_output, file))
            list_df.append(df)
            os.remove(file)
        data = pd.concat(list_df)
        data['scenario'] = scenario_count
        data.to_csv(os.path.join(path_output, "fire_scenario_{}.csv".format(scenario_count)))
    else:
        print("no files to concatenate")


def clean_up_file(prefix, path_path=path_output):
    files = glob.glob(os.path.join(path_path, prefix))
    for file in files:
        # print(file)
        os.remove(file)


#################################
clean_up_file("*csv")
number_of_scenarios = 1
log_burned = []
# --- SCENARIOS
t = datetime.datetime.now()
for scenario in range(number_of_scenarios):
    t0 = datetime.datetime.now()
    burn_list = []
    print("--- SCENARIO : {}".format(scenario))
    print("initiate fire")
    fire_list = set_initial_fire_to(edges)
    x = fire_list
    print("fire list : {}, length : {}".format(fire_list, len(fire_list)))
    # print("fires list in scenario loop: {}, length : {}".format(fire_list, len(fire_list)))
    if len(fire_list) == 0:
        print("no fire")
        continue
    w_direction, w_speed, w_bearing = wind_scenario()
    # print(("critical distance : {}, wind bearing : {}".format(w_speed, w_bearing)))
    # --------- STEPS
    for step in range(len(edges)):
        print("--------- STEP : {}".format(step))
        fire_list = set_fire_to(edges, fire_list)
        y = fire_list
        print("fire datasets are identical with initial fire : {}".format(set(x) == set(y)))
        print("fire list : {}, length : {}".format(fire_list, len(fire_list)))
        print("burn list : {}, length : {}".format(burn_list, len(burn_list)))
        print("spread fire")
        fire_list, burn_list = fire_spreading(fire_list, burn_list, w_speed, w_bearing, 0, step, edges)
        if len(fire_list) == 0:
            print("no fires")
            break
        # burn_list.extend(fire_list)
        # burn_list = list(dict.fromkeys(burn_list))
        print("fires list : {}, length : {}".format(fire_list, len(fire_list)))
        print("burn list : {}, length : {}".format(burn_list, len(burn_list)))
        log_burned.extend(burn_list)

    log_files_concatenate('step*', scenario)
    t1 = datetime.datetime.now()
    print("..... took : {}".format(t1 - t0))
print("total time : {}".format(t1 - t))

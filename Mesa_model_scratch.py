import math
import os
import numpy as np
import pandas as pd
import geopandas as gpd
from mesa.datacollection import DataCollector
from shapely.geometry import box
from geopy.distance import distance
import random

from mesa import Agent, Model
from mesa.time import RandomActivation
from mesa_geo import GeoSpace, GeoAgent, AgentCreator

path = '/Users/alex/Google Drive/05_Sync/FFE/Mesa'


# path = "G:/Sync/FFE/Mesa"


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


# def calculate_distance(pointA, pointB):
#     # need geometry from geopandas
#     pointA.distance(pointB)


# pointA = list(zip(gdf_buildings.LAT, gdf_buildings.LON))
# pointB = ist(zip(gdf_buildings.LAT, gdf_buildings.LON))
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


building_df = load_data("buildings_raw_pts.shp")
direction, fire_distance = wind_scenario()


class ExposureAgent(GeoAgent):
    """ An agent with fixed initial wealth."""

    def __init__(self, unique_id, model, shape):
        super().__init__(unique_id, model, shape)
        self.state = "fine"

    def step(self):
        if self.state == "fire":
            other_agents = self.model.schedule.agents
            for agent in other_agents:
                if fire_distance < self.model.grid.get_distance(self, self, agent):
                    agent.state = "fire"
            self.state = "burned"



class FireModel(Model):
    """A model with geoagents."""

    def __init__(self):
        self.grid = GeoSpace()
        ac = AgentCreator(agent_class=ExposureAgent, agent_kwargs=dict(model=self))
        buildings = ac.from_GeoDataFrame(building_df, unique_id="TARGET_FID")
        self.grid.add_agents(buildings)
        self.schedule = RandomActivation(self)
        self.running = True
        self.grid.add_agents(buildings)

        self.datacollector = DataCollector( model_reporters={"Total Burned": "Burned"})#, agent_reporters={"Fine": "fine", "Fire": "fire", "Burned": "burned"})

        # Set up agents
        for b in buildings:
            if random.random() < b.IgnProb_bl:
                b.condition = "On Fire"
                # self.schedule.add(agent)
                print("building on fire: {}".format(b.unique_id))
            else:
                b.condition = "Fine"
                # self.schedule.add(agent)

            self.schedule.add(b)

    def step(self):
        '''Advance the model by one step.'''
        self.schedule.step()
        all_agents = self.schedule.agents
        list_state = [a.state for a in all_agents]
        if "fire" not in list_state:
            self.running = False
        for a in all_agents:
            self.schedule.add(a)
        self.schedule.step()
        self.datacollector.collect(self)


fire = FireModel()
fire.run_model()
results_model = fire.datacollector.get_model_vars_dataframe()
results_agents = fire.datacollector.get_agent_vars_dataframe()

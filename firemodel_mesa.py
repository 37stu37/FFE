# -*- coding: utf-8 -*-
"""FireModel_mesa.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1h4VIAr0c-kP5Z6t_ZjaVd9JlejQb95qF
"""

import os
import sys
import matplotlib.pyplot as plt
from osgeo import gdal_array
import numpy as np
import pandas as pd
import geopandas as gpd
import shapely
from shapely.geometry import box
import random
from PIL import Image
from matplotlib.pyplot import imshow
from mesa import Model, Agent
from mesa.time import RandomActivation
from mesa.space import Grid
from mesa.datacollection import DataCollector
from mesa.batchrunner import BatchRunner
from mesa_geo import GeoSpace, GeoAgent, AgentCreator
from mesa.visualization.modules import CanvasGrid
from mesa.visualization.ModularVisualization import ModularServer

# pip install Pillow
# pip install descartes
# conda install fiona pyproj rtree shapely
# pip install mesa-geo
# pip install PyDrive

# path = '/Users/alex/Google Drive/05_Sync/FFE/Mesa'
path = "G:/Sync/FFE/Mesa"

# crop data
minx, miny = 1748570, 5426959
maxx, maxy = 1748841, 5427115
bbox = box(minx, miny, maxx, maxy)

gdf_buildings = gpd.read_file(os.path.join(path, "buildings_raw.shp"), bbox=bbox)
# gdf_buildings.plot()
gdf_buildings['IgnProb_bl'] = 0.1

# plot map of agents
# fig, ax = plt.subplots(1, 1)
# gdf_buildings.plot(column='IgnProb_bl', ax=ax, legend=True)

# wind scenario
wind = pd.read_csv(os.path.join(path, 'GD_wind.csv'))


def wind_scenario(wind_data=wind):
    i = np.random.randint(0, wind_data.shape[0])
    w = wind_data.iloc[i, 2]
    d = wind_data.iloc[i, 1]
    return w, d


class Buildings(GeoAgent):
    """
    building footprint.
    Conditions: "Fine", "On Fire", "Burned Out"
    """

    def __init__(self, unique_id, model, shape):
        super().__init__(unique_id, model, shape)
        self.condition = "Fine"
        wind_direction, critical_distance = wind_scenario()
        self.direction = wind_direction
        self.distance = critical_distance

    def step(self):
        '''
        if building is on fire, spread it to buildings according to wind conditions
        '''
        neighbors = self.model.grid.get_neighbors_within_distance(self, distance=self.distance, center=False)
        neighbors_id = [agent.unique_id for agent in neighbors if agent.condition == "Fine" and agent.unique_id != self.unique_id]
        for i in neighbors_id:
            print('self unique_id: {} & neighbor unique_id: {}'.format(self.unique_id, i))
            if self.unique_id == i:
                self.condition = "On Fire"
                print('condition:{} {}'.format( self.unique_id, self.condition))
        self.condition = "Burned Out"
        print('condition:{} {}'.format(self.unique_id, self.condition))

        # print('unique_id: {} condition:{}'.format(self.unique_id, self.condition))
        # if self.condition == "On Fire":
        #     print('{} neighbor(s) of {}'.format( len(neighbors), self.unique_id ))
        #     for neighbor in neighbors:
        #         print('neighbor:{} condition:{}'.format( neighbor.unique_id, neighbor.condition))
        #         if self.unique_id == neighbor.unique_id: continue
        #         if neighbor.condition == "Fine":
        #             # if 0.9 < random.uniform(0.01, 1.0):
        #                 print("neighbor {} Set on Fire !!!!".format(neighbor.unique_id))
        #                 neighbor.condition = "On Fire"
        #     self.condition = "Burned Out"
        #     print('condition:{} {}'.format( self.unique_id, self.condition))


class WellyFire(Model):
    def __init__(self):
        self.grid = GeoSpace()
        self.schedule = RandomActivation(self)
        # agent located from shapefile
        buildings_agent_kwargs = dict(model=self)
        ac = AgentCreator(agent_class=Buildings, agent_kwargs=buildings_agent_kwargs)
        agents = ac.from_GeoDataFrame(gdf_buildings, unique_id="TARGET_FID")
        print("{} in the WellyFire".format(len(agents)))
        self.grid.add_agents(agents)
        self.dc = DataCollector({"Fine": lambda m: self.count_type(m, "Fine"),
                                 "On Fire": lambda m: self.count_type(m, "On Fire"),
                                 "Burned Out": lambda m: self.count_type(m, "Burned Out")})
        self.running = True

        # Set up agents
        print("{} set up agents in the WellyFire".format(len(agents)))
        alreadySet = False
        for agent in agents:
            if not alreadySet:
                agent.condition = 'On Fire'
                alreadySet = True
            self.schedule.add(agent)
        # for agent in agents:
        #     if random.random() < agent.IgnProb_bl:
        #         agent.condition = "On Fire"
        #         # print("{} started".format(agent.condition))
        #         self.schedule.add(agent)
        #     else:
        #         agent.condition = "Fine"
        #         self.schedule.add(agent)

    def step(self):
        """
        Advance the model by one step.
        if no building on Fire, stop the model
        """
        self.schedule.step()
        self.dc.collect(self)
        # Halt if no more fire
        if self.count_type(self, "On Fire") == 0:
            self.running = False

    @staticmethod
    def count_type(model, agent_condition):
        '''
        Helper method to count agents in a given condition in a given model.
        '''
        count = 0
        for agent in model.schedule.agents:
            if agent.condition == agent_condition:
                count += 1
        return count


# Run model
fire = WellyFire()
fire.run_model()
# fire.step()
# for i in range(2):
#     fire.step()


# plot output
results = fire.dc.get_model_vars_dataframe()
results.head()
results.plot()

from mesa.visualization.modules import CanvasGrid
from mesa.visualization.ModularVisualization import ModularServer


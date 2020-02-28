import math
import os
import sys
import matplotlib.pyplot as plt
from numpy.distutils.system_info import gdk_2_info
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

path = '/Users/alex/Google Drive/05_Sync/FFE/Mesa'
# path = "G:/Sync/FFE/Mesa"

# crop data
minx, miny = 1748570, 5426959
maxx, maxy = 1748841, 5427115
bbox = box(minx, miny, maxx, maxy)

# building point dataset
gdf_buildings = gpd.read_file(os.path.join(path, "buildings_raw_pts.shp"), bbox=bbox)
gdf_buildings.IgnProb_bl = 0.5
# xmin,ymin,xmax,ymax = gdf_buildings.total_bounds

# wind scenario
wind = pd.read_csv(os.path.join(path, 'GD_wind.csv'))


def wind_scenario(wind_data=wind):
    i = np.random.randint(0, wind_data.shape[0])
    w = wind_data.iloc[i, 2]
    d = wind_data.iloc[i, 1]
    return w, d


direction, distance = wind_scenario()


# plot map of agents
def plot(column):
    fig, ax = plt.subplots(1, 1)
    gdf_buildings.plot(column=column, ax=ax, legend=True)


plot('IgnProb_bl')


def agent_value():
    state_value = fine + fire
    return state_value


def model_value():
    # number of burned asset
    model_value = burned / 2
    return model_value


def count_fire(model):
    count = 0
    for building in model.schedule.agents:
        if building.state == fire:
            count += 1
    return count


# ABM Model
fine = 0
fire = 1
burned = 2


class Building(GeoAgent):
    def __init__(self, unique_id, model, shape, init_state=fine):
        super().__init__(unique_id, model, shape)
        self.shape = shape
        self.state = init_state
        self.spread = distance

    def step(self):
        if self.state == fire:
            # propagate fire
            for neighbor in self.model.grid.get_neighbors(self, moore=True, radius=distance):
                if neighbor.state == fine:
                    neighbor.state = fire
            self.state = burned


class Fire(Model):
    def __init__(self):
        self.count_fire = 0
        self.grid = GeoSpace()
        self.schedule = RandomActivation(self)
        self.running = True

        # add agents to grid
        ac = AgentCreator(agent_class=Building, agent_kwargs=dict(model=self))
        buildings = ac.from_GeoDataFrame(gdf_buildings, unique_id="TARGET_FID")
        self.grid.add_agents(buildings)

        self.dc = DataCollector(model_reporters={"Burned": count_fire})

        # set buildings on fire
        for building in buildings:
            if random.random() < building.IgnProb_bl:
                building.state = fire
            else:
                building.state = fine
            self.schedule.add(building)

    def step(self):
        # advance model
        self.schedule.step()
        # collect data
        self.dc.collect(self)
        if self.count_fire == 0:
            self.running = False


# plot results
fire = Fire()
fire.run_model()
results = fire.dc.get_model_vars_dataframe()
results.plot()

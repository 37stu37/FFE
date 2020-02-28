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

# path = '/Users/alex/Google Drive/05_Sync/FFE/Mesa'
path = "G:/Sync/FFE/Mesa"

# crop data
minx, miny = 1748570, 5426959
maxx, maxy = 1748841, 5427115
bbox = box(minx, miny, maxx, maxy)

# building point dataset
gdf_buildings = gpd.read_file(os.path.join(path, "buildings_raw_pts.shp"), bbox=bbox)
xmin,ymin,xmax,ymax = gdf_buildings.total_bounds
# grid proportion
height = math.ceil(ymax-ymin)
width = math.ceil(xmax-xmin)

# wind scenario
wind = pd.read_csv(os.path.join(path, 'GD_wind.csv'))

def wind_scenario(wind_data=wind):
    i = np.random.randint(0, wind_data.shape[0])
    w = wind_data.iloc[i, 2]
    d = wind_data.iloc[i, 1]
    return w, d

direction, distance = wind_scenario()

# plot map of agents
fig, ax = plt.subplots(1, 1)
gdf_buildings.plot(column='IgnProb_bl', ax=ax, legend=True)

# counting set up
# def state_count(model):
#     count_fine = [len(Building.state == "Fine") for Building in Fire.schedule.agents]
#     count_on_fire = [len(Building.state == "OnFire") for Building in Fire.schedule.agents]
#     count_burned = [len(Building.state == "Burned") for Building in Fire.schedule.agents]
#     return count_fine, count_on_fire, count_burned


# ABM Model

class Building(Agent):
    def __init__(self, model, init_state="Fine"):
        super().__init__(model)
        self.ignition = gdf_buildings.IgnProb_bl
        self.X = math.ceil(xmax - gdf_buildings.X)
        self.Y = math.ceil(ymax - gdf_buildings.Y)
        self.state = init_state
        self.spread = distance

    def step(self):
        if self.state == "OnFire":
            # propagate fire
            for neighbor in self.model.grid.neighbor_iter(self, radius=distance):
                if neighbor.state == "Fine":
                    neighbor.state = "OnFire"
            self.state = "Burned"


class Fire(Model):
    def __init__(self, Height=height, Width=width):
        self.schedule = RandomActivation(self)
        self.grid = Grid(Height, Width, torus=False)
        self.datacollector = DataCollector({"Fine": lambda m: self.count_type(m, "Fine"), "OnFire": lambda m: self.count_type(m, "OnFire"), "Burned": lambda m: self.count_type(m, "Burned")})



        # def place_agents(self):
        for (contents, x, y) in self.grid.coord_iter():
            building = Building((x, y), model)
            for Xcoo, Ycoo in zip(gdf_buildings.X, gdf_buildings.Y):
                # create building
                if (Xcoo == x) and (Ycoo == y):
                    self.grid._place_agent(building, (x, y))
                    # ignition
                    if random.random() < building.ignition:
                        building.state = "OnFire"
                    else:
                        building.state = "Fine"
                    self.schedule.add(building)


    def step(self):
        # advance model
        self.schedule.step()
        # collect data
        self.datacollector.collect(self)

    def count_type(model, agent_condition):
        count = 0
        for building in model.schedule.agents:
            if building.state == agent_condition:
                count += 1
        return count

# plot results
fire = Fire()
fire.run_model()
results = fire.dc.get_model_vars_dataframe()
results.plot()
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

# path = '/Users/alex/Google Drive/05_Sync/FFE/Mesa'
path = "G:/Sync/FFE/Mesa"

# crop data
minx, miny = 1748570, 5426959
maxx, maxy = 1748841, 5427115
bbox = box(minx, miny, maxx, maxy)

gdf_buildings = gpd.read_file(os.path.join(path, "buildings_raw.shp"), bbox=bbox)

# plot map of agents
fig, ax = plt.subplots(1, 1)
gdf_buildings.plot(column='IgnProb_bl', ax=ax, legend=True)


class Agent(GeoAgent):
    def __init__(self, unique_id, model, shape):
        super().__init__(unique_id, model, shape)


class GeoModel(Model):
    def __init__(self):
        self.grid = GeoSpace()

        state_agent_kwargs = dict(model=self)
        AC = AgentCreator(agent_class=Agent, agent_kwargs=state_agent_kwargs)
        agents = AC.from_GeoDataFrame(gdf_buildings, unique_id="TARGET_FID")
        self.grid.add_agents(agents)
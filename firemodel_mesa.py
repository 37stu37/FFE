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

# pip install Pillow
# pip install descartes
# conda install fiona pyproj rtree shapely
# pip install mesa-geo
# pip install PyDrive

path = '/Users/alex/Google Drive/05_Sync/FFE/Mesa'

# crop data
minx, miny = 1748347, 5426740
maxx, maxy = 1749151, 5427195
bbox = box(minx, miny, maxx, maxy)

gdf_buildings = gpd.read_file(os.path.join(path, "buildings_raw.shp"), bbox=bbox)


class Buildings(GeoAgent):
    def __init__(self, unique_id, model, shape):
        super().__init__(unique_id, model, shape)


#
# class AgentCreator:
#     """Create GeoAgents from files, GeoDataFrames, GeoJSON or Shapely objects."""
#
#     def __init__(self, agent_class, agent_kwargs, crs={"init": "epsg:2193"}):
#         """Define the agent_class and required agent_kwargs.
#         Args:
#             agent_class: Reference to a GeoAgent class
#             agent_kwargs: Dictionary with required agent creation arguments.
#                 Must at least include 'model' and must NOT include unique_id
#             crs: Coordinate reference system. If shapes are loaded from file
#                 they will be converted into this crs automatically.
#         """
#         if "unique_id" in agent_kwargs:
#             agent_kwargs.remove("unique_id")
#             warnings.warn("Unique_id should not be in the agent_kwargs")
#
#         self.agent_class = agent_class
#         self.agent_kwargs = agent_kwargs
#         self.crs = crs
#
#     def create_agent(self, shape, unique_id):
#         """Create a single agent from a shape and a unique_id
#         Shape must be a valid Shapely object."""
#
#         if not isinstance(shape, BaseGeometry):
#             raise TypeError("Shape must be a Shapely Geometry")
#
#         new_agent = self.agent_class(
#             unique_id=unique_id, shape=shape, **self.agent_kwargs
#         )
#
#         return new_agent
#
#     def from_GeoDataFrame(self, gdf, unique_id="index", set_attributes=True):
#         """Create a list of agents from a GeoDataFrame.
#         Args:
#             unique_id: Column to use for the unique_id.
#                 If "index" use the GeoDataFrame index
#             set_attributes: Set agent attributes from GeoDataFrame columns.
#         """
#
#         if unique_id != "index":
#             gdf = gdf.set_index(unique_id)
#
#         gdf = gdf.to_crs(self.crs)
#
#         agents = list()
#
#         for index, row in gdf.iterrows():
#             shape = row.geometry
#             new_agent = self.create_agent(shape=shape, unique_id=index)
#
#             if set_attributes:
#                 for col in row.index:
#                     if not col == "geometry":
#                         setattr(new_agent, col, row[col])
#             agents.append(new_agent)
#         return agents
#
#     def from_file(self, filename, unique_id="index", set_attributes=True):
#         """Create agents from vector data files (e.g. Shapefiles).
#         Args:
#             filename: The filename of the vector data
#             unique_id: The field name of the data to use as the agents unique_id
#             set_attributes: Set attributes from data records
#         """
#         gdf = gpd.read_file(filename)
#         agents = self.from_GeoDataFrame(
#             gdf, unique_id=unique_id, set_attributes=set_attributes
#         )
#         return agents
#
#     def from_GeoJSON(self, GeoJSON, unique_id="index", set_attributes=True):
#         """Create agents from a GeoJSON object or string.
#         Args:
#             GeoJSON: The GeoJSON object or string
#             unique_id: The fieldfeature name of the data to use as the agents unique_id
#             set_attributes: Set attributes from features
#         """
#         if type(GeoJSON) is str:
#             gj = json.loads(GeoJSON)
#         else:
#             gj = GeoJSON
#
#         gdf = gpd.GeoDataFrame.from_features(gj)
#         gdf.crs = "+init=epsg:4326"
#         agents = self.from_GeoDataFrame(
#             gdf, unique_id=unique_id, set_attributes=set_attributes
#         )
#         return agents
#

class GeoModel(Model):
    def __init__(self):
        self.grid = GeoSpace()

        buildings_agent_kwargs = dict(model=self)
        AC = AgentCreator(agent_class=Buildings, agent_kwargs=buildings_agent_kwargs, )
        agents = AC.from_GeoDataFrame(gdf_buildings, unique_id="TARGET_FID")
        self.grid.add_agents(agents)


model = GeoModel()
agent = model.grid.agents[0]
print(agent.unique_id)
agent.shape

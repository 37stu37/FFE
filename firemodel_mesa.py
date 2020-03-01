import os
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import box
import random
from mesa import Model, Agent
from mesa.time import RandomActivation
from mesa.space import Grid
from mesa.datacollection import DataCollector
from mesa.batchrunner import BatchRunner
from mesa_geo import GeoSpace, GeoAgent, AgentCreator
from mesa.visualization.modules import CanvasGrid
from mesa.visualization.ModularVisualization import ModularServer


path = "G:/Sync/FFE/Mesa"

# crop data
minx, miny = 1748570, 5426959
maxx, maxy = 1748841, 5427115
bbox = box(minx, miny, maxx, maxy)

gdf_buildings = gpd.read_file(os.path.join(path, "buildings_raw.shp"), bbox=bbox)
# gdf_buildings.plot()
gdf_buildings['IgnProb_bl'] = 0.1

# plot map of agents
fig, ax = plt.subplots(1, 1)
gdf_buildings.plot(column='IgnProb_bl', ax=ax, legend=True)

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
        # option 1
        # print("STEP AGENT")
        neighbors = self.model.grid.get_neighbors_within_distance(self, center=False, distance=self.distance)
        if self.condition == "On Fire":
            for n in neighbors:
                if n.condition == "Fine":
                    n.condition = "On Fire"
            self.condition = "Burned Out"

        # option 2 (display but no model step either)
        # other_agents = self.model.schedule.agents
        # if self.condition == "Fine":
        #     for agent in other_agents:
        #         if self.distance < self.model.grid.distance(self, agent):
        #             if agent.condition == "On Fire":
        #                 self.condition = "On Fire"


class Fire(Model):
    def __init__(self):
        self.grid = GeoSpace()
        self.schedule = RandomActivation(self)
        # agent located from shapefile
        buildings_agent_kwargs = dict(model=self)
        ac = AgentCreator(agent_class=Buildings, agent_kwargs=buildings_agent_kwargs)
        agents = ac.from_GeoDataFrame(gdf_buildings, unique_id="TARGET_FID")
        self.grid.add_agents(agents)
        self.dc = DataCollector({"Fine": lambda m: self.count_type(m, "Fine"),
                                 "On Fire": lambda m: self.count_type(m, "On Fire"),
                                 "Burned Out": lambda m: self.count_type(m, "Burned Out")})
        self.running = True

        # Set up agents
        print("{} agents set up in the Fire model".format(len(agents)))
        for agent in agents:
            agent.condition = "Fine"
            if random.random() < agent.IgnProb_bl:
                agent.condition = "On Fire"
                print("building on fire: {}".format(agent.unique_id))

            self.schedule.add(agent)

    def step(self):
        """
        Advance the model by one step.
        if no building on Fire, stop the model
        """
        # collect data
        self.dc.collect(self)
        # step in time
        print("STEP MODEL")
        self.schedule.step()


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
fire = Fire()
fire.run_model()

# plot output
results = fire.dc.get_model_vars_dataframe()
results.head()
results.plot()


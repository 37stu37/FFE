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
import imageio
import random
from PIL import Image
from matplotlib.pyplot import imshow
from mesa import Model, Agent
from mesa.time import RandomActivation
from mesa.space import Grid
from mesa.datacollection import DataCollector
from mesa.batchrunner import BatchRunner


path = 'E:\Current_work\FFE\dynamic_fire\Mesa'

def load_data(path_to_data=path):
    # load building map as a "fuel" map
    fuel = gdal_array.LoadFile(os.path.join(path_to_data, 'GD_fuel_map_crop.tif'))  # 0 = no fuel; 1 = fuel
    fuel[fuel < 0] = 0
    # load probability of building ignition as an array
    ignition = gdal_array.LoadFile(os.path.join(path_to_data, 'GD_ignit_prob_crop.tif'))  # probability from 0 to 1
    ignition[ignition < 0] = 0
    # load wind data
    wind = pd.read_csv(os.path.join(path_to_data, 'GD_wind.csv'))
    return fuel, ignition, wind

fuel_map, ignition_probability_map, wind_df = load_data()

def wind_scenario(wind_data=wind_df):
    i = np.random.randint(0, wind_data.shape[0])
    wind = wind_data.iloc[i, 2]
    distance = wind_data.iloc[i, 1]
    return wind, distance

def plot(title, map1, map2):
    fig, ax = plt.subplots(ncols=2)
    im0 = ax[0].imshow(map1, cmap='jet', aspect='auto')
    im1 = ax[1].imshow(map2, cmap='jet', aspect='auto')
    plt.colorbar(im0, ax=ax[0])
    plt.colorbar(im1, ax=ax[1])
    plt.show()

plot("test initial map", fuel_map, ignition_probability_map)

class TreeCell(Agent):
    '''
    A tree cell.
    
    Attributes:
        x, y: Grid coordinates
        condition: Can be "Fine", "On Fire", or "Burned Out"
        unique_id: (x,y) tuple. 
    
    unique_id isn't strictly necessary here, but it's good practice to give one to each
    agent anyway.
    '''
    def __init__(self, model, pos):
        '''
        Create a new tree.
        Args:
            pos: The tree's coordinates on the grid. Used as the unique_id
        '''
        super().__init__(pos, model)
        self.pos = pos
        self.unique_id = pos
        self.condition = "Fine"
        
    def step(self):
        '''
        If the tree is on fire, spread it to fine trees nearby.
        '''
        if self.condition == "On Fire":
            neighbors = self.model.grid.get_neighbors(self.pos, moore=False)
            for neighbor in neighbors:
                if neighbor.condition == "Fine":
                    neighbor.condition = "On Fire"
            self.condition = "Burned Out"

class TreeCell(Agent):
    '''
    A tree cell.
    
    Attributes:
        x, y: Grid coordinates
        condition: Can be "Fine", "On Fire", or "Burned Out"
        unique_id: (x,y) tuple. 
    
    unique_id isn't strictly necessary here, but it's good practice to give one to each
    agent anyway.
    '''
    def __init__(self, model, pos):
        '''
        Create a new tree.
        Args:
            pos: The tree's coordinates on the grid. Used as the unique_id
        '''
        super().__init__(pos, model)
        self.pos = pos
        self.unique_id = pos
        self.condition = "Fine"
        
    def step(self):
        '''
        If the tree is on fire, spread it to fine trees nearby.
        '''
        if self.condition == "On Fire":
            neighbors = self.model.grid.get_neighbors(self.pos, moore=False)
            for neighbor in neighbors:
                if neighbor.condition == "Fine":
                    neighbor.condition = "On Fire"
            self.condition = "Burned Out"
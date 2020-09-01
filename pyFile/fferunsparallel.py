# -*- coding: utf-8 -*-
"""FFErunsParallel.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/github/37stu37/FFE/blob/master/FFErunsParallel.ipynb
"""

# from google.colab import drive
# drive.mount('/content/drive')

"""**Imports**
---
"""

import numpy as np
import pandas as pd
import os
import glob


pd.options.mode.chained_assignment = None  # default='warn'

os.chdir('Z:\FFE')

edge_file = 'FinnShapeEdges.parquet'
wind_file = 'Copy of GD_wind.csv'
folder = 'output'

# load data
wind_data = pd.read_csv(wind_file) 
edgelist = pd.read_parquet(edge_file, engine='auto')

## variable created to sample probabilities properly
FreqCorrection = edgelist[["source"]]
FreqCorrection['freq'] = edgelist.groupby('source')['source'].transform('count')
FreqCorrection.drop_duplicates(inplace=True)
edgelist = edgelist.merge(FreqCorrection, on=['source'], how='left')
edgelist['IgnProbBld'] = edgelist['IgnProbBld'] / edgelist['freq']
# corrected edgelist with proper Ignition probability
edgelist.drop("freq", axis=1, inplace=True)

# definitions
def wind_scenario(wind_data):
      i = np.random.randint(0, wind_data.values.shape[0])
      w = wind_data.values[i, 2]
      dist = wind_data.values[i, 1]
      b = wind_data.values[i, 3]
      bear_max = b + 45  # wind direction
      bear_min = b - 45
      if b == 360:
          bear_max = 45
      if b <= 0:  # should not be necessary
          bear_min = 0
      if b == 999:
          bear_max = 999
          bear_min = 0
      return bear_max, bear_min, dist # wind characteristics, bearing and distance


def ignition(edges=edgelist):
    rng = np.random.uniform(0, 1, size=edges.values.shape[0])
    mask = rng < edges.IgnProbBld.values
    NewActiveEdges = edges[mask]
    return NewActiveEdges


def mask(t, activeEdges_d, listActivatedSources_d, w_b_max, w_b_min, w_d):
    if t==0: # special case at time=0
        return activeEdges_d
    else:
        mask = (activeEdges_d.bearing.values < w_b_max) & (activeEdges_d.bearing.values < w_b_min) & (activeEdges_d.distance < w_d)
        NewActiveEdges = activeEdges_d[mask]
        NewActiveEdges = NewActiveEdges[~NewActiveEdges.source.isin(listActivatedSources_d)]
        return NewActiveEdges


def propagation(activeEdges_d, edges=edgelist):
    NewActiveEdges = edges[edges.source.isin(activeEdges_d.target)]
    return NewActiveEdges


def clean_up(path):
    files = glob.glob(path)
    print(" {} files removed".format(len(files)))
    for f in files:
      os.remove(f)


def ffe_runs(n):
    for scenario in range(n):
        # initial setup
        listActivatedSources = []
        listScenarioDataframes = []
        condition = True
        time = 0 
        # wind conditions
        w_bearing_max, w_bearing_min, w_distance = wind_scenario(wind_data)
        # ignition / initial state and edges selection
        ActiveEdges = ignition()
        # print(f"{len(ActiveEdges)} ignitions")
        if ActiveEdges.empty:
            continue
        while condition: # spread burn zone
            ActiveEdges = mask(time, ActiveEdges, listActivatedSources, w_bearing_max, w_bearing_min, w_distance)
            ActiveEdges['time'] = time
            if ActiveEdges.empty: #no more buildings to burn
                break
            listScenarioDataframes.append(ActiveEdges)
            listActivatedSources.extend(ActiveEdges.source.values)
            ActiveEdges = propagation(ActiveEdges)
            time += 1
        
        print(f'finishing pid {os.getpid()} scenario --- {scenario} time ---- {time}')

        Activations = pd.concat(listScenarioDataframes)
        Activations["scenario"] = scenario
        Activations["pid"] = os.getpid()
        Activations.to_parquet(str(folder) + '/' + f'scenario{scenario}_pid{os.getpid()}.parquet', engine='auto', compression="GZIP")

# Main
ffe_runs(100)
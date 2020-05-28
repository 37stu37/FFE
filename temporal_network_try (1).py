import numpy as np
import pandas as pd
from pathlib import Path
import memory_profiler as mem_profile
import sys
import os
import glob
import multiprocessing as mp
from zipfile import ZipFile

pd.options.mode.chained_assignment = None  # default='warn'

"""
**Load data from zip file**
---
"""

# import data from zip file
# folder = Path('/Users/alex/Desktop/runs')
# with ZipFile(folder / 'ffe_data.zip', 'r') as zip:
#     edge_file = zip.extract('Copy of edge_data.parquet')
#     wind_file = zip.extract('Copy of GD_wind.csv')
edge_file = "Copy of edge_data.parquet"
wind_file = "Copy of GD_wind.csv"
# load data
wind_data = pd.read_csv(wind_file)
edgelist = pd.read_parquet(edge_file, engine='pyarrow')

"""
**Definitions**
---
"""


# %%timeit
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
    return bear_max, bear_min, dist  # wind characteristics, bearing and distance


def ignition(edges=edgelist):
    rng = np.random.uniform(0, 1, size=edges.values.shape[0])
    mask = rng < edges.IgnProb_bl.values
    NewActiveEdges = edges[mask]
    return NewActiveEdges


def mask(t, activeEdges_d, listActivatedSources_d, w_b_max, w_b_min, w_d):
    if t == 0:  # special case at time=0
        return activeEdges_d
    else:
        mask = (activeEdges_d.bearing.values < w_b_max) & (activeEdges_d.bearing.values < w_b_min) & (
                    activeEdges_d.distance < w_d)
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


"""
**Main**
---


---
"""


def ffe_runs(n):
    listScenarioDataframes = []
    for scenario in range(n):
        # initial setup
        condition = True
        # listScenarioDataframes = []
        listActivatedSources = []
        time = 0
        # wind conditions
        w_bearing_max, w_bearing_min, w_distance = wind_scenario(wind_data)
        # ignition / initial state and edges selection
        ActiveEdges = ignition()
        if ActiveEdges.empty:
            continue
        while condition:
            ActiveEdges = mask(time, ActiveEdges, listActivatedSources, w_bearing_max, w_bearing_min, w_distance)
            if ActiveEdges.empty:
                break
            listScenarioDataframes.append(ActiveEdges)
            listActivatedSources.extend(ActiveEdges.source.values)
            ActiveEdges = propagation(ActiveEdges)
            time += 1

        print("scenario : {}, process id: {}".format(scenario, os.getpid()))
        Activations = pd.concat(listScenarioDataframes)
        Activations["scenario"] = scenario
        Activations["pid"] = os.getpid()
        Activations.to_parquet('/Volumes/NO NAME/output/scenario{}_pid{}_Activations.parquet'.format(scenario, os.getpid()),
                               engine='pyarrow')


# run in parallel using the available cores
n_scenario = range(10)
pool = mp.Pool()
results = pool.map(ffe_runs, n_scenario)

"""
**Backup**
---



---
"""

clean_up('/Volumes/NO NAME/output/*')

# pqt = pd.read_parquet("/content/drive/My Drive/04_Cloud/01_Work/GNS/008_FFE/runs/output/scenario0_pid1998_Activations.parquet")

# num_cores = multiprocessing.cpu_count()
# print(num_cores)

# -*- coding: utf-8 -*-
"""FFEpostProcessingRAPIDS.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/github/37stu37/FFE/blob/master/FFEpostProcessingRAPIDS.ipynb

#Installation
---
"""

from pathlib import Path
import os
import re
from datetime import date

import pandas as pd
import numpy as np
import geopandas as gpd
import dask.dataframe as dd
pd.options.mode.chained_assignment = None

# Paths
path = Path.cwd()
pathShapefile = path / 'shapefile'
pathParquets = path / 'output'

print(len(os.listdir(pathParquets)))

# definitions
def read_and_concatenate_parquets(nscenarios, nparallel, path=pathParquets):
  L = []
  pidList = []
  updtScenariolist = []
  files = pathParquets.glob('*.parquet')
  for file in files:
    regex = r"pid\d*"
    pidNames = re.findall(regex, str(file))
    for pidName in pidNames:
      print(f" file pid {pidName}")
      pidList.append(pidName)
    pidList = list(set(pidList))
    updtScenariolist = np.repeat(nscenarios, nparallel)
    updtScenariolist = list(np.cumsum(updtScenariolist))

  for file in files:
    pqt = pd.read_parquet(file, engine='auto')
    regex = r"pid\d*"
    pidNames = re.findall(regex, str(file))
    pqt["pid"] = pidName
    for idx, value in enumerate(pidList):
      if pqt.pid == value:
        pqt["scenarioUpdt"] = pqt["scenario"] + updtScenariolist[idx]
    L.append(pqt)
  df = dd.concat(L)
  return df, pidList


def merge_parallel_update_scenario_count(ddf, pids):
  conditions = []
  results = []
  sco = 0
  for p in pids:
    conditions.append((ddf.pid == p))
    results.append(ddf['scenario'] + sco)
  ddf["scenarioUpdt"] = np.select(conditions, results)
  return ddf


def count_fid_occurences(df):
  count = df['source'].value_counts().compute()
  count_df = pd.DataFrame({'source': count.index, 'count': count.values})
  count_df.to_parquet(str(pathShapefile) + '/' + f'CountBurn-{str(date.today())}.parquet', engine='auto', compression="GZIP")# could be datetime.now
  return count_df


def Merge(countDf,nameShapefile):
  # Shapefile
  gdfShape = gpd.read_file(pathShapefile / nameShapefile)
  gdfShape.insert(0, 'FID', range(0, len(gdfShape)))
  gdfShape.rename(columns={'FID': 'source'}, inplace=True)
  gdfShape = gdfShape[['source', 'geometry']]
  # merge
  merged = countDf.merge(gdfShape, on=['source'], how='left')
  return merged


def createShapefile(df):
  gdf = gpd.GeoDataFrame(df, geometry='geometry')
  gdf.to_file(os.path.join(str(pathShapefile) + "/" + "Burn3000scenarioWellington.shp"))
  return gdf


# Main
concatDf = read_and_concatenate_parquets()
# countConcatDf = count_fid_occurences(concatDf)
# mergedDf = Merge(countConcatDf, 'WellWHV_Buildings.shp')
# countShape = createShapefile(mergedDf)

# Plot
import matplotlib.pyplot as plt
import contextily as ctx
plt.style.use('seaborn-whitegrid')

FinnMeshblockShape = gpd.read_file(pathShapefile / 'Finn_MeshBlockSummary.shp')
countShape = gpd.read_file(pathShapefile / 'Burn3000scenarioWellington.shp')

fig, (ax1, ax2) = plt.subplots(nrows=1, ncols=2, sharex=True, sharey=True, figsize=(12, 10))

p1 = FinnMeshblockShape.plot(ax=ax1, column='WellWHV_Bu', cmap='YlOrRd', alpha=0.7, legend=True)
ctx.add_basemap(ax1, crs=2193)
p2 = countShape.plot(ax=ax2, column='count', cmap='YlOrRd', alpha=0.7, legend=True)
ctx.add_basemap(ax2, crs=2193)

ax1.set_title('Original burn count at meshblock level')
ax1.ticklabel_format(useOffset=False, style='plain')
ax2.set_title('Network burn count at individual building level')
ax2.ticklabel_format(useOffset=False, style='plain')
ax1.tick_params(direction='out', length=6)
ax2.tick_params(direction="out", length=6)

fig.autofmt_xdate()
plt.tight_layout()
plt.savefig(pathShapefile / 'ComparisonGISvsNetwork_3000Burn.png', dpi=600)
plt.show()

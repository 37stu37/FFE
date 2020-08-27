# %%
import os
import pandas as pd
import time
import datetime
import numpy as np
import random
import glob
import math
import shutil
pd.options.mode.chained_assignment = None  # default='warn'

# path and data

## parallel computing akatea
path = '/scratch/alexd/FFE/output'

# %%
def clean_up_file(prefix):
    files = glob.glob(os.path.join(path, prefix))
    for file in files:
        print(file)
        os.remove(file)
        
def clean_up_folder(prefix):
    folders = glob.glob(os.path.join(path, prefix))
    for folder in folders:
        print(folder)
        files = glob.glob(os.path.join(path, folder, '*csv'))
        for file in files:
            print(file)
            os.remove(file)
        shutil.rmtree(folder, ignore_errors=True)
        # os.rmdir(folder)
        
clean_up_file('scenario*')
# clean_up_folder('res*')
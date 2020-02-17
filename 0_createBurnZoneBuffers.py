# Import system modules
import pandas as pd
import os, sys
import arcpy

# Set inputs
workDir =  r'D:\_Working\FFE_Modelling'
GDB = os.path.join(workDir, "IgnitionModel.gdb")
inFile = os.path.join(workDir, "Data", "WindDistributionTable.csv")
bldgFC = "Buildings"
combField = "Combustible"           # field used to determine if the building is combustible/non-combustible (1/0)

# Set enviroments
arcpy.env.workspace = os.path.join(workDir, GDB)
arcpy.env.overwriteOutput = True

# Read csv into data frame
df = pd.read_csv(inFile)
df.drop_duplicates(subset="CriticalStep", keep="first",inplace=True) # remove duplicates
df.reset_index(drop=True, inplace=True) # reset index

numc = df.shape[1]
numr = df.shape[0]

for i in range(0, numr):
    if int(df.at[i,"Variable"]) > 0:
        critical = df.at[i,"CriticalStep"]
        print (critical)
        buffFC = "BuildingBuffer" + str(int(critical))
        buff_dist = critical / 2.0
        print " Buffering..."
        where_clause = combField + " = 1"
        arcpy.MakeFeatureLayer_management(bldgFC, "comb", where_clause)  # buffer only combustible buildings
        arcpy.Buffer_analysis("comb", "buff_all", buff_dist, "", "", "ALL")
        arcpy.MultipartToSinglepart_management("buff_all", buffFC)

# Delete temporary fiel
arcpy.Delete_management("buff_all")

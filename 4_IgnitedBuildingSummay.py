"""
The script randomly set buildings based on their ignition probability calculated
using Khorasani Fire Ignition model (based on one PGA scenario)

Wind direction and strenght (critical separation) are randomly choosen from
the wind summary file for Wellington Region


"""

# Import system modules
import arcpy
import random
import os, sys
from datetime import datetime

# ------------------------------------------------------------------------------
# Set initial values
workDir = r'D:\_Working\FFE_Modelling'
workGDB = "IgnitionModel.gdb"

buildFC = "Buildings"               # building footprint feature class
buildRS = "BuildingsRS"             # RS building points (used for summarising)
combField = "Combustible"           # field used to determine if the building is combustible/non-combustible (1/0)

# Set outputs
sumFile = os.path.join(workDir, "Outputs", "IgnitedBuildingSummary.csv") # scenario summary file
randField = "RandProb"              # field to hold a random number to be compared with probability

# Set enviroments
arcpy.env.workspace = os.path.join(workDir, workGDB)
arcpy.env.overwriteOutput = True

# Get start time
start_time = datetime.now()

# Writing header into summary file
with open(sumFile, "w") as scen_f:
    scen_f.write("Scenario,FP_Comb_Ini,FP_NonComb_Ini,FP_Comb_Total,FP_NonComb_Total,RS_Comb_Total,RS_NonComb_Total\n")

for scenario in range(1,101):

    print "Scenario: " + str(scenario)

    # Input field
    ignField = "Ignited" + str(scenario)


    where_clause = ignField + " = 1 and " + combField + " = 1"
    arcpy.MakeFeatureLayer_management(buildFC, "fp_ign_comb", where_clause)
    comb_ini = int(arcpy.GetCount_management("fp_ign_comb")[0])

    where_clause = ignField + " = 1 and " + combField + " = 0"
    arcpy.MakeFeatureLayer_management(buildFC, "fp_ign_noncomb", where_clause)
    noncomb_ini = int(arcpy.GetCount_management("fp_ign_noncomb")[0])

    where_clause = ignField + " > 0 and " + combField + " = 1"

    arcpy.MakeFeatureLayer_management(buildFC, "fp_ign_comb", where_clause)
    fp_comb_tot = int(arcpy.GetCount_management("fp_ign_comb")[0])

    arcpy.MakeFeatureLayer_management(buildRS, "rs_ign_comb", where_clause)
    rs_comb_tot = int(arcpy.GetCount_management("rs_ign_comb")[0])

    where_clause = ignField + " > 0 and " + combField + " = 0"

    arcpy.MakeFeatureLayer_management(buildFC, "fp_ign_noncomb", where_clause)
    fp_noncomb_tot = int(arcpy.GetCount_management("fp_ign_noncomb")[0])

    arcpy.MakeFeatureLayer_management(buildRS, "rs_ign_noncomb", where_clause)
    rs_noncomb_tot = int(arcpy.GetCount_management("rs_ign_noncomb")[0])


    # Writing scenario info
    print " Writing scenario info"
    with open(sumFile, "a") as scen_f:
        scen_f.write("{0},{1},{2},{3},{4},{5},{6}\n".format(scenario, comb_ini, noncomb_ini, fp_comb_tot, fp_noncomb_tot, rs_comb_tot, rs_noncomb_tot))

# Get total time
total_time = datetime.now() - start_time
print "---Total running time: " + str(total_time)
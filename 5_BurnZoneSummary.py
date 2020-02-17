"""
The script randomly set buildings based on their ignition probability calculated
using Khorasani Fire Ignition model (based on one PGA scenario)

Wind direction and strenght (critical separation) are randomly choosen from
the wind summary file for Wellington Region


"""

# Import system modules
import arcpy
import os, sys
from datetime import datetime

# ------------------------------------------------------------------------------
# Set initial values
workDir = r'D:\_Working\FFE_Modelling'
workGDB = "IgnitionModel.gdb"

buildRS = "BuildingsRS"             # RS building points (used for summarising)
combField = "Combustible"           # field used to determine if the building is combustible/non-combustible (1/0)

# sum fields
dwlVal = "Replace_1"
contVal = "CONT_V_1"
plantVal = "Plant_V_1"
occD = "OCCUPD_1"
occN = "OCCUPN_1"

# Set outputs
sumFile = os.path.join(workDir, "Outputs", "BurnZoneSummary.csv") # scenario summary file
sumFileComb = os.path.join(workDir, "Outputs", "BurnZoneSummaryCombustible.csv") # scenario summary file

# Set enviroments
arcpy.env.workspace = os.path.join(workDir, workGDB)
arcpy.env.overwriteOutput = True

# Get start time
start_time = datetime.now()

# Opening summary files
scen_f = open(sumFile, "w")
scen_f_c = open(sumFileComb, "w")

# writing headers
scen_f.write("Scenario,BLD_CNT,PopD,PopN,Dwl_Val,Cont_Val,Plant_Val\n")
scen_f_c.write("Scenario,BLD_Comb_CNT,PopD_Comb,PopN_Comb,Dwl_Comb_Val,Cont_Comb_Val,Plant_Comb_Val\n")


for scenario in range(1,101):

    print "Scenario: " + str(scenario)

    # Input field
    burnZone = "BurnZone" + str(scenario)

    start_time_s = datetime.now()

    print " Muliti to single part"
    arcpy.MultipartToSinglepart_management(burnZone, "temp")

    # total
    print " Total:"
    print "  Intersecting with buildings"
    arcpy.Intersect_analysis(["temp", buildRS], "temp_tot")
    print "  Statistics"
    arcpy.Statistics_analysis("temp_tot", "temp_stat_tot", [[occD, "SUM"], [occN, "SUM"], [dwlVal, "SUM"], [contVal, "SUM"], [plantVal, "SUM"]], "FID_temp")
    print "  Writing"
    with arcpy.da.SearchCursor("temp_stat_tot", ["FREQUENCY", "SUM_" + occD, "SUM_" + occN, "SUM_" + dwlVal, "SUM_" + contVal, "SUM_" + plantVal]) as curs_tot:
        for row in curs_tot:
            scen_f.write(str(scenario) + "," + ",".join(map(str,[val for val in row])) + "\n")

    # comb
    print " Combustible only:"
    print "  Intersecting with buildings"
    arcpy.MakeFeatureLayer_management(buildRS, "comb", combField + " = 1")
    arcpy.Intersect_analysis(["temp", "comb"], "temp_comb")
    print "  Statistics"
    arcpy.Statistics_analysis("temp_comb", "temp_stat_comb", [[occD, "SUM"], [occN, "SUM"], [dwlVal, "SUM"], [contVal, "SUM"], [plantVal, "SUM"]], "FID_temp")
    print "  Writing"
    with arcpy.da.SearchCursor("temp_stat_comb", ["FREQUENCY", "SUM_" + occD, "SUM_" + occN, "SUM_" + dwlVal, "SUM_" + contVal, "SUM_" + plantVal]) as curs_tot:
        for row in curs_tot:
            scen_f_c.write(str(scenario) + "," + ",".join(map(str,[val for val in row])) + "\n")

    print " Time: " + str(datetime.now() - start_time_s)

scen_f.close()
scen_f_c.close()

print "Total time: " + str(datetime.now() - start_time)

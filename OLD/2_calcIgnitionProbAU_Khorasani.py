# Calculate AU ignition probability, probability per building within AU and number of ignitions
# No differentiation between combustable and non-combustable buildings

# Import system modules
import arcpy
import math
import random
from arcpy.sa import *
import os, sys

# Import custom toolbox
arcpy.ImportToolbox("J:\_All_GNS_Info\GIS_Support\GISTools\ArcGIS_Toolboxes\JoinField\Join Field.tbx", "mytbx")

def add_field(fc, fld, fld_type):
    if fld in [f.name for f in arcpy.ListFields(fc)]:
        arcpy.DeleteField_management(fc, fld)
    arcpy.AddField_management(fc, fld, fld_type)
def delete_field(fc, fld):
    if fld in [f.name for f in arcpy.ListFields(fc)]:
        arcpy.DeleteField_management(fc, fld)

# Set initial values
workDir = r'D:\_Working\FFE_Modelling'
workGDB = "IgnitionModel.gdb"

# Set enviroments
arcpy.env.workspace = os.path.join(workDir, workGDB)
arcpy.env.overwriteOutput = True

# Set FC
inFC = "AreaUnitData"
probFC = "IgnAU_Khorasani"
bldgFC = "Buildings"
auID = "AU2013Num"

# set coeff
const = -6.755
pgaC = 8.463
pdC = 0.0000984
sfC = 0.0001523

# Set fields
popDens = "PopDensity_perKm2"
bldgArea = "BldgFloor_1000ft2"
pgaField = "PGA_Mean"
num_bld = "NumberBldgFP"# number of footprints used for calculating probability for buildings

# Prob fields
probField = "IgnProb_AU"
probFieldBld = "IgnProb_bldg"
noIgnF = "NoIgn"

# Copy input feature classes
print "Copying area units"
arcpy.CopyFeatures_management(inFC, probFC)

# Remove field if exist and add new one
add_field(probFC, probField, "DOUBLE")

# Calculate probability
print "Calculating probability of ignition for AU"
expression = "1 / (1 + math.exp(-1 * (" + str(const) + " + " + str(pgaC) + " * !" + pgaField + "! + " + str(pdC) + " * !" + popDens + "! + " + str(sfC) + " * !" + bldgArea + "!)))"
arcpy.CalculateField_management(probFC, probField, expression, "PYTHON")


print "Calculting ignition probability for buildings within AU"
# Remove field if exist and add new one
add_field(probFC, probFieldBld, "DOUBLE")
# Calculate probability
expression = "1 - math.pow(1 - !" + probField + "!, 1.0 / !" + num_bld + "!)"
arcpy.CalculateField_management(probFC, probFieldBld, expression, "PYTHON")

print "Calculting number of ignitions within AU"
# Remove field if exist and add new one
add_field(probFC, noIgnF, "LONG")
# Calculate probability
expression = "!" + probFieldBld + "! * !" + num_bld + "!"
arcpy.CalculateField_management(probFC, noIgnF, expression, "PYTHON")

print "Attaching probability to buildings"
arcpy.JoinField_mytbx(bldgFC, auID, probFC, auID, probFieldBld)

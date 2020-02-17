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
dataGDB = "IgnitionModelData.gdb"
workGDB = "IgnitionModel.gdb"

# Inputs
bldgRS = os.path.join(workDir, dataGDB, "WellingtonBuildingsRS") # building points from RiskScape
floorArea = "FloorArea" # field holding floor area
bldgPol = os.path.join(workDir, dataGDB, "WellingtonFootprints_RS")  # current building footprints with Combustible field calculated from RS using the Near tool
bldgID = "TARGET_FID"

inAU = os.path.join(workDir, dataGDB, "WellingtonAU")
auID ="AU2013Num"
auPop = "CensusPop"

pgaFC = os.path.join(workDir, dataGDB, "WellingtonFaultPGA")
inPgaField = "PGA_g"
inMMIField = "MMI"

# Create GDB if it doesn't exist
if not arcpy.Exists(os.path.join(workDir,workGDB)):
    print "Creating work GDB"
    arcpy.CreateFileGDB_management(workDir, workGDB)

# Set enviroments
arcpy.env.workspace = os.path.join(workDir, workGDB)
arcpy.env.overwriteOutput = True

# Set output FC
bldgFP = "Buildings" # building footprints
bldgFPpt = "BuildingPoints" # centroids of building footprints
auFC = "AreaUnitData"

# Set output fields
auPopDens = "PopDensity_perKm2"
bldgAreaFt2 = "BldgFloor_1000ft2"
bldgAreaM2 = "BldgFloor_millm2"
pgaField = "PGA_Mean"
mmiField = "MMI_Mean"
num_bld = "NumberBldgFP"
num_bld_rs = "NumberBldgRS"

# Copy input feature classes
print "Copying feature classes to the working GDB"
print " " + auFC
arcpy.CopyFeatures_management(inAU, auFC)
# copy building footpeints if they don't exist
if not arcpy.Exists(bldgFP):
    print " " + bldgFP
    arcpy.CopyFeatures_management(bldgPol, bldgFP)
# Converting building footprints to points (if they don't exist)
if not arcpy.Exists(bldgFPpt):
    print "Creating centroids for building footprints"
    arcpy.FeatureToPoint_management(bldgFP, bldgFPpt, "INSIDE") # to be used to determine number of buildings within area unit

# Calculating population density
print "Calculating population density"
add_field(auFC, auPopDens, "LONG")  # add field using function
arcpy.CalculateField_management(auFC, auPopDens, "!" + auPop + "! / (!Shape_Area! / 1000000)", "PYTHON")

# Calculating floor area within an area unit (getting the number of buildings as well)
print "Calculating floor area within each area unit (in thousands of square feet)"
arcpy.Identity_analysis(bldgRS, auFC, "bldg_au") # attaching area unit to building RS points
arcpy.Statistics_analysis("bldg_au", "floor_area", [[floorArea, "SUM"]], auID) # floor area summarised for each AU
sumField = "SUM_" + floorArea # the name of generated SUM field
add_field(auFC, bldgAreaFt2, "DOUBLE") # add field for summarised floor area (using function)
delete_field(auFC, sumField) # delete SUM field if exists in output table(using function)
arcpy.JoinField_mytbx(auFC, auID, "floor_area", auID, sumField) # join SUM field from statistics table
arcpy.CalculateField_management(auFC, bldgAreaFt2, "!" + sumField + "! / 0.3048 / 0.3048 / 1000.0", "PYTHON")  # calculate (convert to square feet)
arcpy.DeleteField_management(auFC, sumField) # delete joined SUM field (after the required field is calculated from it)

# Setting zeros for AU with no buildings
arcpy.MakeFeatureLayer_management(auFC, "zero_lyr", bldgAreaFt2 + " IS NULL")
numNoBldg = int(arcpy.GetCount_management("zero_lyr")[0])
if numNoBldg > 0:
    print " " + str(numNoBldg) + " area units with no RS buildings; floor area set to 0"
    arcpy.CalculateField_management("zero_lyr", bldgAreaFt2, "0")

# Calculating building area within an area unit (in millions of square metres) - requires area in 1000 ft2
print "Calculating building area within each area unit (in millions of square metres)"
add_field(auFC, bldgAreaM2, "DOUBLE") # add field using function
arcpy.CalculateField_management(auFC, bldgAreaM2, "!" + bldgAreaFt2 + "! * 0.3048 * 0.3048 / 1000.0", "PYTHON")  # convert from 1000 feet2 to 1000000 m2

print "Calculating mean PGA and MMI for each area unit"
# attach mesh block ID to PGA points
arcpy.Identity_analysis(pgaFC, auFC, "pga_au") # pga points used and intersected with mesh blocks
# calculate Mean PGA within area units
arcpy.Statistics_analysis("pga_au", "pga_mean", [[inPgaField, "MEAN"]], auID) # mean value calculated for each AU
# calculate Mean MMI within area units
arcpy.Statistics_analysis("pga_au", "mmi_mean", [[inMMIField, "MEAN"]], auID) # mean value calculated for each AU
# remove fields if they exist
delete_field(auFC, "MEAN_" + inPgaField)
delete_field(auFC, pgaField)
delete_field(auFC, "MEAN_" + inMMIField)
delete_field(auFC, mmiField)
# join mean PGA field
arcpy.JoinField_mytbx(auFC, auID, "pga_mean", auID, "MEAN_" + inPgaField)
# rename the field
arcpy.AlterField_management(auFC, "MEAN_" + inPgaField, pgaField, "", "", "", "", "TRUE")
# join mean MMI field
arcpy.JoinField_mytbx(auFC, auID, "mmi_mean", auID, "MEAN_" + inMMIField)
# rename the field
arcpy.AlterField_management(auFC, "MEAN_" + inMMIField, mmiField, "", "", "", "", "TRUE")

# Attach the nearest PGA/MMI to the area unit without any PGA point
delete_field(auFC, inPgaField)
delete_field(auFC, inMMIField)
arcpy.MakeFeatureLayer_management(auFC, "no_pga", pgaField + " IS NULL")
if int(arcpy.GetCount_management("no_pga")[0]) > 0:
    print " Attaching nearest value for area unit with no PGA point"
    arcpy.CopyFeatures_management("no_pga", "pga_near")
    arcpy.Near_analysis("pga_near", pgaFC)
    arcpy.JoinField_mytbx("pga_near", "NEAR_FID", pgaFC, "OBJECTID", [inPgaField, inMMIField])
    arcpy.JoinField_mytbx("no_pga", auID, "pga_near", auID, [inPgaField, inMMIField])
    arcpy.CalculateField_management("no_pga", pgaField, "!" + inPgaField + "!", "PYTHON")
    arcpy.CalculateField_management("no_pga", mmiField, "!" + inMMIField + "!", "PYTHON")
    arcpy.DeleteField_management("no_pga", inPgaField)
    arcpy.DeleteField_management("no_pga", inMMIField)

# Attach area unit ID to buildings
print "Attaching Area Unit ID to buildings"
arcpy.Identity_analysis(bldgFPpt, auFC, "bldg_pt_au")
# to footprints
delete_field(bldgFP, auID)
arcpy.JoinField_mytbx(bldgFP, bldgID, "bldg_pt_au", bldgID, auID)
# to building points
delete_field(bldgFPpt, auID)
arcpy.JoinField_mytbx(bldgFPpt, bldgID, "bldg_pt_au", bldgID, auID)

print " Removing buildings not within an area unit"
# footprints
arcpy.MakeFeatureLayer_management(bldgFP, "del_lyr", auID + " = 0")
numNoAU = int(arcpy.GetCount_management("del_lyr")[0])
if numNoAU > 0:
    print " " + str(numNoAU) + " building footprints deleted as there is no area unit associated"
    arcpy.DeleteRows_management("del_lyr")
    # building points
    arcpy.MakeFeatureLayer_management(bldgFPpt, "del_ptlyr", auID + " = 0")
    arcpy.DeleteRows_management("del_ptlyr")

# Calculate number of building footprints within each area unit
print "Calculating number of buildings"
arcpy.MakeTableView_management(bldgFP, "bldg_table")
arcpy.Frequency_analysis("bldg_table", "num_bldg", [auID])

print " Attaching number of building footprints to area units"
delete_field(auFC, "FREQUENCY")
delete_field(auFC, num_bld)
arcpy.JoinField_mytbx(auFC, auID, "num_bldg", auID, "FREQUENCY")
arcpy.AlterField_management(auFC, "FREQUENCY", num_bld, "", "", "", "", "TRUE")
# Calculate NULLs to zeros
arcpy.MakeFeatureLayer_management(auFC, "bldg_null", num_bld + " IS NULL")
if int(arcpy.GetCount_management("bldg_null")[0]) > 0:
    arcpy.CalculateField_management("bldg_null", num_bld, "0")

# Calculate number of RS building points within each area unit using frequency from "floor_area" table)

print " Attaching number of RS building points to area units"
delete_field(auFC, "FREQUENCY")
delete_field(auFC, num_bld_rs)
arcpy.JoinField_mytbx(auFC, auID, "floor_area", auID, "FREQUENCY")
arcpy.AlterField_management(auFC, "FREQUENCY", num_bld_rs, "", "", "", "", "TRUE")
# Calculate NULLs to zeros
arcpy.MakeFeatureLayer_management(auFC, "bldg_null", num_bld_rs + " IS NULL")
if int(arcpy.GetCount_management("bldg_null")[0]) > 0:
    arcpy.CalculateField_management("bldg_null", num_bld_rs, "0")

# Cleaning workspace
print "Cleaning workspace"
for lyr in ["bldg_au", "bldg_pt_au", "floor_area", "num_bldg", "pga_mean", "mmi_mean", "pga_au", "pga_near", "temp"]:
    if arcpy.Exists(lyr):
        arcpy.Delete_management(lyr)

sys.exit()

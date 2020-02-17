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

# Import custom toolbox (arcpy.JoinField_mytbx(inTable, join_field, joinTable, join_field, [field list to join]) to call the tool)
arcpy.ImportToolbox("J:\_All_GNS_Info\GIS_Support\GISTools\ArcGIS_Toolboxes\JoinField\Join Field.tbx", "mytbx")


# ------------------------------------------------------------------------------
def add_field(fc, fld, fld_type):
    if fld in [f.name for f in arcpy.ListFields(fc)]:
        arcpy.DeleteField_management(fc, fld)
    arcpy.AddField_management(fc, fld, fld_type)
def delete_field(fc, fld):
    if fld in [f.name for f in arcpy.ListFields(fc)]:
        arcpy.DeleteField_management(fc, fld)
def shift_features(in_features, x_shift=None, y_shift=None):
    """
    Shifts features by an x and/or y value. The shift values are in
    the units of the in_features coordinate system.

    Parameters:
    in_features: string
        An existing feature class or feature layer.  If using a
        feature layer with a selection, only the selected features
        will be modified.

    x_shift: float
        The distance the x coordinates will be shifted.

    y_shift: float
        The distance the y coordinates will be shifted.
    """

    with arcpy.da.UpdateCursor(in_features, ['SHAPE@XY']) as cursor:
        for row in cursor:
            cursor.updateRow([[row[0][0] + (x_shift or 0),
                               row[0][1] + (y_shift or 0)]])

    return

# ------------------------------------------------------------------------------
# Set initial values
workDir = r'D:\_Working\FFE_Modelling'
workGDB = "IgnitionModel.gdb"
windFile = os.path.join(workDir, "Data", "WindScenarios.csv")

buildFC = "Buildings"               # building footprint feature class
buildRS = "BuildingsRS"             # RS building points (used for summarising)
buildProbField = "IgnProb_bldg"     # Field containing ignition probability for a building (Khorasani, using AU)
combField = "Combustible"           # field used to determine if the building is combustible/non-combustible (1/0)
buff_dist_calm = 12                 # critical separation for calm condition

windDict = {'N': 180,'NE': 225,'E': 270,'SE': 315,'S': 0,'SW': 45,'W': 90,'NW': 135}

# Set outputs
scenFile = os.path.join(workDir, "Outputs", "ScenarioSummary.csv") # scenario summary file
randField = "RandProb"              # field to hold a random number to be compared with probability

# Set enviroments
arcpy.env.workspace = os.path.join(workDir, workGDB)
arcpy.env.overwriteOutput = True

# Get start time
start_time = datetime.now()

# Writing header into summary file
with open(scenFile, "w") as scen_f:
    scen_f.write("Scenario,NumberOfIgnitions,WindRecord,WindDirection,CriticalSeparation,NumberOfWindSteps,ProcessingTime\n")

# Getting number of records in wind file
with open(windFile, "r") as wind_f:
    num_winds = len(wind_f.readlines())

for scenario in range(1,101):

    print "Scenario: " + str(scenario)
    start_time_scen = datetime.now()

    # Outputs
    burn_scen = "BurnZone" + str(scenario)
    ignField = "Ignited" + str(scenario)

    # Initial ignition
    print " Calculating initial ignition..."
    if not randField in [f.name for f in arcpy.ListFields(buildFC)]:
        arcpy.AddField_management(buildFC, randField, "DOUBLE")
    add_field(buildFC, ignField, "LONG")
    # Determining if a building is ignited by comparing random number with building ignition probability
    num_ign = 0
    with arcpy.da.UpdateCursor(buildFC, [buildProbField, randField, ignField]) as cursor:
        for row in cursor:
            row[1] = random.uniform(0,1)
            if row[1] <= row[0]:
                row[2] = 1
                num_ign += 1
            else:
                row[2] = 0
            cursor.updateRow(row)

    print "  " + str(num_ign) + " buildings initially ignited"

    # Adding ignited field to RS buildings
    print " Adding ignited field to RS buildings"
    add_field(buildRS, ignField, "LONG")

    # Getting wind caracteristics from the file
    print " Getting wind caracteristics from the file"
    wind_record = random.randrange(1,num_winds+1)
    with open(windFile, "r") as wind_f:
        for line in wind_f.readlines():
            line_list = [elem.strip(" \n\r") for elem in line.split(",")]
            if line_list[0] == str(wind_record):
                critical = int(line_list[1])
                wind_dir = line_list[2]


    # Checking wind and choosing a method of processing
    # Processing with no wind direction
    if wind_dir == "buffer" or critical == buff_dist_calm:

        print " Critical separation the same as for calm condition or no distinctive wind direction; pre-processed buffer used"

        print "  Critical separation for calm condition: " + str(buff_dist_calm)
        print "  Critical separation for chosen wind: " + str(critical)

        stepVal = 0
        pre_buffer = "BuildingBuffer" + str(critical)
        print "  Creating burn zone by selecting buffers created for critical separation with ignited buildings"
        where_clause = ignField + " = 1 and " + combField + " = 1" # use only combustible buildings
        arcpy.MakeFeatureLayer_management(buildFC, "ign_comb", where_clause) # select ignited buildings
        # Create a layer from buffers
        arcpy.MakeFeatureLayer_management(pre_buffer, "buffers")
        # Select buffers that intersect ignited buildings
        arcpy.SelectLayerByLocation_management("buffers", 'INTERSECT', "ign_comb")
        arcpy.CopyFeatures_management("buffers", burn_scen)

        print "  Selecting buildings within the burn zone"

        # combustible
        print "  - combustible (RS buildings)" # (ignited set to 1 for all combustible within a zone)
        arcpy.MakeFeatureLayer_management(buildRS, "rs_comb", combField + " = 1") # layer of combustible RS buildings
        arcpy.SelectLayerByLocation_management("rs_comb", 'INTERSECT', burn_scen) # selection using burn zones
        if int(arcpy.GetCount_management("rs_comb")[0]) > 0:
            arcpy.CalculateField_management("rs_comb", ignField, "1", "PYTHON")

        print "  - combustible (building footprints)" # (ignited set to 2 for all combustible within a zone as 1 is used for initially ignited)
        arcpy.MakeFeatureLayer_management(buildFC, "foot_comb", combField + " = 1") # layer of combustible RS buildings
        arcpy.SelectLayerByLocation_management("foot_comb", 'INTERSECT', burn_scen) # selection using burn zones
        arcpy.SelectLayerByAttribute_management('foot_comb','SUBSET_SELECTION', ignField + ' = 0')
        if int(arcpy.GetCount_management("foot_comb")[0]) > 0:
            arcpy.CalculateField_management("foot_comb", ignField, "2", "PYTHON")

        # non-combustible
        print "  - non-combustible (within the zone)"  # using only footprints not initially ignited
        arcpy.MakeFeatureLayer_management(buildFC, "fp_non_comb", combField + " = 0 and " + ignField + " = 0") # layer of non-combustible building footprints
        search_rad = critical / 2.0
        arcpy.SelectLayerByLocation_management("fp_non_comb", 'INTERSECT', burn_scen, search_rad) # selection using burn zones (intersects or within half critical distance)
        if int(arcpy.GetCount_management("fp_non_comb")[0]) > 0:

            # calculate ignition field to 2 for all footprints that intersect buffers
            arcpy.CalculateField_management("fp_non_comb", ignField, "2", "PYTHON") # calculate field to be 2 (for footprints)

            arcpy.MakeFeatureLayer_management(buildRS, "rs_non_comb", combField + " = 0") # only non-combustible buildings from RS buildings
            # Using NEAR to find the closest non-combustible RS building to non-combustible building footprint in the burn zone
            arcpy.Near_analysis("fp_non_comb", "rs_non_comb") # find the nearest RS building to the footprint
            arcpy.JoinField_mytbx("rs_non_comb", "OBJECTID", "fp_non_comb", "NEAR_FID", "NEAR_DIST")  # attach near distances back to RS buildings
            arcpy.MakeFeatureLayer_management(buildRS, "rs_spread_ign", "NEAR_DIST IS NOT NULL") # select RS buildings nearest to footprints
            arcpy.CalculateField_management("rs_spread_ign", ignField, "1", "PYTHON") # calculate field to be 1
            # remove near fields
            arcpy.DeleteField_management(buildRS, "NEAR_DIST")
            arcpy.DeleteField_management(buildFC, "NEAR_DIST")
            arcpy.DeleteField_management(buildFC, "NEAR_FID")

        # Tagging non-combustible RS buildings initially ignited (they don't have to have a buffer associated)
        print "  - non-combustable (initially ignited)"
        arcpy.MakeFeatureLayer_management(buildFC, "ign_non_comb", ignField + " = 1 and " + combField + " = 0") # use only initially ignited non-combustible buildings
        if int(arcpy.GetCount_management("ign_non_comb")[0]) > 0:   # if there is any non-combustible building initially ignited
            print "   (" + str(int(arcpy.GetCount_management("ign_non_comb")[0])) + ")"
            arcpy.MakeFeatureLayer_management(buildRS, "rs_non_comb", combField + " = 0") # get non-combustible buildings from RS buildings
            # Using NEAR to find the closest non-combustible RS buildings to non-combustible initially ignited building footprints
            arcpy.Near_analysis("ign_non_comb", "rs_non_comb") # find the nearest RS building to the footprint
            arcpy.JoinField_mytbx("rs_non_comb", "OBJECTID", "ign_non_comb", "NEAR_FID", "NEAR_DIST")  # attach near distances back to RS buildings
            arcpy.MakeFeatureLayer_management(buildRS, "rs_ini_ign", "NEAR_DIST IS NOT NULL") # select RS buildings nearest to footprints
            arcpy.CalculateField_management("rs_ini_ign", ignField, "2", "PYTHON") # calculate field to be 2 (for initially ignited)
            # remove near fields
            arcpy.DeleteField_management(buildRS, "NEAR_DIST")
            arcpy.DeleteField_management(buildFC, "NEAR_DIST")
            arcpy.DeleteField_management(buildFC, "NEAR_FID")
        else:
            print "    (none)"


    # Processing using wind direction
    else:
        print " Wind direction given; buffering in steps, in direction of the wind"
        print "  Creating burn zone"
        # Set outputs
        buff_final = burn_scen
        # Set temporary
        processFC = "temp_ign"
        buff_ini = "temp_buff_ini"
        buff_process = "temp_buff"
        buff_done = "temp_buff_done"

        # get wind azi
        wind_azi = windDict[wind_dir]

        # Calculate number of buffering steps for large critical separations
        move_total = critical - buff_dist_calm
        num_steps = 1
        if move_total > buff_dist_calm:
            num_steps = int(move_total / buff_dist_calm) + num_steps
        move = move_total / num_steps

        print "   Critical separation for calm condition: " + str(buff_dist_calm)
        print "   Critical separation for chosen wind: " + str(critical)
        print "   Chosen wind direction: " + wind_dir
        print "   Number of internal steps: " + str(int(num_steps))
        print "   Internal move: " + str(move)

        # Calculate x and y of move
        move_x = math.sin(math.radians(wind_azi)) * move
        move_y = math.cos(math.radians(wind_azi)) * move

        # Start processing
        stepVal = 1
        switch = 0

        while switch == 0:

            print "   Step " + str(stepVal) + ":"

            # Select features that are on fire (and combustable) and create a new FC
            where_clause = ignField + " = " + str(stepVal) + " and " + combField + " = 1"
            arcpy.MakeFeatureLayer_management(buildFC, "layer", where_clause)
            arcpy.CopyFeatures_management("layer", processFC)

            # set list of buffers for each internal step to be merged together
            if stepVal == 1:
                buffList = []
            else:
                buffList = [buff_done] # previously created buffer (only newly ignited buildings added)

            dictBuff = {i : "temp_buff" + str(i) for i in range(0,num_steps)} # variable with counter

            # Initial buffer
#            print "   - Initial buffering"
            arcpy.Buffer_analysis(processFC, buff_ini, buff_dist_calm, "", "", "ALL")
            buffList.append(buff_ini)

            for i in range(0,num_steps):

                # Shift features
#                print "   - Shifting features: " + str(i + 1)
                shift_features(processFC, x_shift=move_x, y_shift=move_y)

                # Buffer
#                print "   - Buffering: " + str(i + 1)
                arcpy.Buffer_analysis(processFC, dictBuff[i], buff_dist_calm, "", "", "ALL")
                buffList.append(dictBuff[i])

            # Merge buffers
#            print "   - Merging buffers"
            arcpy.Merge_management(buffList, buff_process)

            # Select affected buildings and calculate the Ignited field
#            print "   - Updating buildings; adding ignited by spread"
            arcpy.MakeFeatureLayer_management(buildFC, "bld_lyr")
            # Select using buffer
            arcpy.SelectLayerByLocation_management("bld_lyr", 'INTERSECT', buff_process)
            # Select buildings not ignited
            arcpy.SelectLayerByAttribute_management('bld_lyr','SUBSET_SELECTION', ignField + ' = 0 and ' + combField + " = 1")
            numNewBld = int(arcpy.GetCount_management('bld_lyr')[0])
            if numNewBld > 0:
                # Calculate ignited field
#                print "      (new buildings ignited)"
                stepVal += 1
                arcpy.CalculateField_management('bld_lyr', ignField, stepVal, "PYTHON")  # add the number of step into ignited field
                # save existing buffer
#                print "   - Saving the buffer to append to in the next step"
                if arcpy.Exists(buff_done):
                    arcpy.Delete_management(buff_done)
                arcpy.Rename_management(buff_process, buff_done)
            else:
#                print "      (no more buildings ignited)"
#                print "   - Dissolving buffers"
                arcpy.Dissolve_management(buff_process, buff_final)
                switch = 1

        print "   Cleaning workspace"
        for layer in ["temp_buff" + str(i) for i in range(0,num_steps)] + [processFC, buff_ini, buff_process, buff_done]:
            if arcpy.Exists(layer):
#                print "    Deleting " + layer
                arcpy.Delete_management(layer)


        print "  Selecting buildings within the burn zone"

        # combustible (only in RS point layer, ignition field in footprints is calculated during buffering)
        print "  - combustible (RS buildings)"
        arcpy.MakeFeatureLayer_management(buildRS, "rs_comb", combField + " = 1") # layer of combustible RS buildings
        arcpy.SelectLayerByLocation_management("rs_comb", 'INTERSECT', burn_scen) # selection using burn zones
        if int(arcpy.GetCount_management("rs_comb")[0]) > 0:
            arcpy.CalculateField_management("rs_comb", ignField, "1", "PYTHON")

        # non-combustible
        print "  - non-combustible (within the zone)"
        arcpy.MakeFeatureLayer_management(buildFC, "fp_non_comb", combField + " = 0 and " + ignField + " = 0") # layer of non-combustible RS footprints not initially ignited
        search_rad = critical / 2.0
        arcpy.SelectLayerByLocation_management("fp_non_comb", 'INTERSECT', burn_scen, search_rad) # selection using burn zones (intersects or within half critical distance)
        if int(arcpy.GetCount_management("fp_non_comb")[0]) > 0:

            # calculate ignition field to 2 for all non-conbustible footprints that intersect buffers
            arcpy.CalculateField_management("fp_non_comb", ignField, "2", "PYTHON") # calculate field to be 2 (for footprints)
            arcpy.MakeFeatureLayer_management(buildRS, "rs_non_comb", combField + " = 0") # only non-combustible buildings from RS buildings
            # Using NEAR to find the closest non-combustible RS building to non-combustible building footprint in the burn zone
            arcpy.Near_analysis("fp_non_comb", "rs_non_comb") # find the nearest RS building to the footprint
            arcpy.JoinField_mytbx("rs_non_comb", "OBJECTID", "fp_non_comb", "NEAR_FID", "NEAR_DIST")  # attach near distances back to RS buildings
            arcpy.MakeFeatureLayer_management(buildRS, "rs_spread_ign", "NEAR_DIST IS NOT NULL") # select RS buildings nearest to footprints
            arcpy.CalculateField_management("rs_spread_ign", ignField, "1", "PYTHON") # calculate field to be 1
            # remove near fields
            arcpy.DeleteField_management(buildRS, "NEAR_DIST")
            arcpy.DeleteField_management(buildFC, "NEAR_DIST")
            arcpy.DeleteField_management(buildFC, "NEAR_FID")

        # Tagging non-combustible RS buildings initially ignited (they don't have to have a buffer associated)
        print "  - non-combustable (initially ignited)"
        where_clause = ignField + " = 1 and " + combField + " = 0" # use only initially ignited non-combustible buildings
        arcpy.MakeFeatureLayer_management(buildFC, "ign_non_comb", where_clause)
        if int(arcpy.GetCount_management("ign_non_comb")[0]) > 0:   # if there is any non-combustible building initially ignited
            print "   (" + str(int(arcpy.GetCount_management("ign_non_comb")[0])) + ")"
            arcpy.MakeFeatureLayer_management(buildRS, "rs_non_comb", combField + " = 0") # only non-combustible buildings from RS buildings
            # Using NEAR to find the closest non-combustible RS buildings to non-combustible initially ignited building footprints
            arcpy.Near_analysis("ign_non_comb", "rs_non_comb") # find the nearest RS building to the footprint
            arcpy.JoinField_mytbx("rs_non_comb", "OBJECTID", "ign_non_comb", "NEAR_FID", "NEAR_DIST")  # attach near distances back to RS buildings
            arcpy.MakeFeatureLayer_management(buildRS, "rs_ini_ign", "NEAR_DIST IS NOT NULL") # select RS buildings nearest to footprints
            arcpy.CalculateField_management("rs_ini_ign", ignField, "2", "PYTHON") # calculate field to be 2
            # remove near fields
            arcpy.DeleteField_management(buildRS, "NEAR_DIST")
            arcpy.DeleteField_management(buildFC, "NEAR_DIST")
            arcpy.DeleteField_management(buildFC, "NEAR_FID")
        else:
            print "    (none)"

    stepProcessTime = datetime.now() - start_time_scen
    print " ---Running time: " + str(stepProcessTime)

    # Writing scenario info
    print " Writing scenario info"
    with open(scenFile, "a") as scen_f:
        scen_f.write("{0},{1},{2},{3},{4},{5},{6}\n".format(scenario, num_ign, wind_record, wind_dir, critical, stepVal, stepProcessTime))

# Get total time
total_time = datetime.now() - start_time
print "---Total running time: " + str(total_time)
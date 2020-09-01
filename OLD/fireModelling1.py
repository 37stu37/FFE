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
def SelectRandomByNumber(layer, count):
    #layer with features to be selected
    #number of selection
    oids = [oid for oid, in arcpy.da.SearchCursor (layer, "OID@")]
    oidFldName = arcpy.Describe(layer).OIDFieldName
    delimOidFld = arcpy.AddFieldDelimiters(layer, oidFldName)
    randOids = random.sample(oids, count)
    oidsStr = ", ".join (map (str, randOids))
    sql = "{0} IN ({1})".format (delimOidFld, oidsStr)
    arcpy.SelectLayerByAttribute_management (layer, "", sql)

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

start_time = datetime.now()

# The ID of the output geodatabase (based on the name of the python script)
out_num = os.path.basename(__file__).replace("fireModelling","").replace(".py","")

#Number of scenarios to be run
num_scen = 100

# Set initial values
workDir = r'D:\_Working\FFE_Modelling'
dataGDB = os.path.join(workDir, "FFE_ModellingData.gdb")
workGDB = os.path.join(workDir, "FFE_Model" + out_num + ".gdb")
windFile = os.path.join(workDir, "InputData", "WindScenarios.csv")

# suppression
sup_perc = 30                       # percent of initial fires that are supppressed

# PGA inputs
pga_table = "PGA_HikWgtnMin"
pga_field = "Mean"

### EQ scenarios dictionary
##pgaDict = {1:["PGA_HikWgtnMin", 3000],2:["PGA_HikWgtnMax", 3000],3:["PGA_WairarapNich", 15000],4:["PGA_Wairau", 15000],5:["PGA_WellWHV", 15000]}

# Set input FC
inSA = os.path.join(dataGDB, "SA2_Input")
bldg = os.path.join(dataGDB, "BuildingFootprints")

# Set input fields
areaID ="SA2_ID"
pgaAreaID = "SA2"                  # SA ID field in the PGA tables
popDens = "PopDensity_perKm2"
floorArea = "BldgFloor_1000ft2"
num_bld = "NumberBldg"              # Number of buildings within SA

combField = "Combustible"           # field used to determine if the building is combustible/non-combustible (1/0)
valField = "ReplacementVal"         # Building replacement value
occField = "NightOccupants"         # field in the building layer showing number of occupants

# critical distance for calm
buff_dist_calm = 12                 # critical separation for calm condition

# wind dictionary
windDict = {'N': 180,'NE': 225,'E': 270,'SE': 315,'S': 0,'SW': 45,'W': 90,'NW': 135}

# ignition probability coeff
const = -6.755
pgaC = 8.463
pdC = 0.0000984
sfC = 0.0001523

# Set output scenario file
scenFile = os.path.join(workDir, "Outputs", "ScenarioSummary" + out_num + ".csv") # scenario summary file

# set output FC
saFC = "SA2_Model" + out_num
bldgFC = "Bldg_Model" + out_num

# Output temp
randField = "RandProb"

# Getting number of records in wind file
with open(windFile, "r") as wind_f:
    num_winds = len(wind_f.readlines())

# Create output GDB if it doesn't exist
if not arcpy.Exists(workGDB):
    print "Creating GDB"
    arcpy.CreateFileGDB_management(os.path.dirname(workGDB), os.path.basename(workGDB))

# Set enviroments
arcpy.env.workspace = workGDB
arcpy.env.overwriteOutput = True

# Copy statistical areas and buildings
arcpy.CopyFeatures_management(inSA, saFC)
arcpy.CopyFeatures_management(bldg, bldgFC)

# Writing header into summary file
with open(scenFile, "w") as scen_f:
    scen_f.write("Scenario,PGA_fault,PGA_column,NumberOfIgnitions,NumberOfSuppressions,WindRecord,WindDirection,WindSpeed,CriticalSeparation,NumberOfWindSteps,ProcessingTime,ReplacementValue,NightOccupants\n")

'''
The following block moved out of the scenario loop
as only one PGA file and one PGA field are used
'''
# Output prob fields
ignProbF = "IgnProb"
ignProbBldgF = "IgnProbBldg"
noIgnF = "NoIgn"

# Add probability fields (remove field if exist and add new one)
add_field(saFC, ignProbF, "DOUBLE")
add_field(saFC, ignProbBldgF, "DOUBLE")
add_field(saFC, noIgnF, "DOUBLE")

# join pga_field to SA FC
print (" Join PGA")
arcpy.JoinField_mytbx(saFC, areaID, os.path.join(dataGDB, pga_table), pgaAreaID, pga_field)

# Calculate probability and number of ignitions

print " Calculating probability of ignition for SA"
expression = "1 / (1 + math.exp(-1 * (" + str(const) + " + " + str(pgaC) + " * !" + pga_field + "! + " + str(pdC) + " * !" + popDens + "! + " + str(sfC) + " * !" + floorArea + "!)))"
arcpy.CalculateField_management(saFC, ignProbF, expression, "PYTHON")

print " Calculting ignition probability for buildings within SA"
expression = "1 - math.pow(1 - !" + ignProbF + "!, 1.0 / !" + num_bld + "!)"
arcpy.CalculateField_management(saFC, ignProbBldgF, expression, "PYTHON")

print " Calculting number of ignitions within SA"
expression = "!" + ignProbBldgF + "! * !" + num_bld + "!"
arcpy.CalculateField_management(saFC, noIgnF, expression, "PYTHON")

print " Attaching probability to buildings"
arcpy.JoinField_mytbx(bldgFC, areaID, saFC, areaID, ignProbBldgF)
'''
END of the block
'''

for scenario in range(1,num_scen+1):

    print ("Scenario: " + str(scenario))
    start_time_scen = datetime.now()

    # Outputs ign fields
    ignField = "Ignited" + str(scenario)
    # output burn zone for scenario
    burn_scen = "BurnZone" + out_num + "_" + str(scenario)

    '''
    The following block moved out of the scenario loop
    as only one PGA file and one PGA fieled is used
    '''
##    # Output prob fields
##    ignProbF = "IgnProb" + str(scenario)
##    ignProbBldgF = "IgnProbBldg" + str(scenario)
##    noIgnF = "NoIgn" + str(scenario)
##
##    # Add probability fields (remove field if exist and add new one)
##    add_field(saFC, ignProbF, "DOUBLE")
##    add_field(saFC, ignProbBldgF, "DOUBLE")
##    add_field(saFC, noIgnF, "DOUBLE")
##
##    # get PGA
##    # randomly choose pga file
##    pga_file_num = random.randrange(1,6)
##    pga_table = pgaDict[pga_file_num][0]
##    print " " + pga_table + " fault file chosen"
##
##    # get PGA mean field
##    pga_field = "Mean"
##    # randomly choose the PGA column
##    pga_column = random.randrange(1, pgaDict[pga_file_num][1] + 1)
##    pga_field = "V" + str(pga_column)
##
##    # join pga_field to SA FC
##    print (" Join PGA")
##    arcpy.JoinField_mytbx(saFC, areaID, os.path.join(dataGDB, pga_table), pgaAreaID, pga_field)
##
##    # Calculate probability and number of ignitions
##
##    print " Calculating probability of ignition for SA"
##    expression = "1 / (1 + math.exp(-1 * (" + str(const) + " + " + str(pgaC) + " * !" + pga_field + "! + " + str(pdC) + " * !" + popDens + "! + " + str(sfC) + " * !" + floorArea + "!)))"
##    arcpy.CalculateField_management(saFC, ignProbF, expression, "PYTHON")
##
##    print " Calculting ignition probability for buildings within SA"
##    expression = "1 - math.pow(1 - !" + ignProbF + "!, 1.0 / !" + num_bld + "!)"
##    arcpy.CalculateField_management(saFC, ignProbBldgF, expression, "PYTHON")
##
##    print " Calculting number of ignitions within SA"
##    expression = "!" + ignProbBldgF + "! * !" + num_bld + "!"
##    arcpy.CalculateField_management(saFC, noIgnF, expression, "PYTHON")
##
##    print " Attaching probability to buildings"
##    arcpy.JoinField_mytbx(bldgFC, areaID, saFC, areaID, ignProbBldgF)
##
##    print " Removing PGA field"
##    arcpy.DeleteField_management(saFC, pga_field)
    '''
    END of the block
    '''

    # Initial ignition
    print " Calculating initial ignition..."
    add_field(bldgFC, ignField, "LONG") # add field showing ignited buildings
    # Determining if a building is ignited by comparing random number with building ignition probability
    num_ign = 0
    with arcpy.da.UpdateCursor(bldgFC, [ignProbBldgF, ignField]) as cursor:
        for row in cursor:
            rand_prob = random.uniform(0,1)
            if rand_prob <= row[0]:
                row[1] = 1
                num_ign += 1
            else:
                row[1] = 0
            cursor.updateRow(row)

    print "  " + str(num_ign) + " buildings initially ignited"

    # Suppression
    num_sup = int(round(num_ign * float(sup_perc) / 100))
    print "  " + str(num_sup) + " initial fires suppressed"

    if num_sup > 0:
        where_clause = ignField + " = 1"
        arcpy.MakeFeatureLayer_management(bldgFC, "ignited", where_clause) # select ignited buildings
        SelectRandomByNumber("ignited", num_sup) # select buildings where fires are going to be suppressed (function)
        arcpy.CalculateField_management("ignited", ignField, "-1", "PYTHON")

    # Number of initial fires
    num_fires = num_ign - num_sup
    print "  " + str(num_fires) + " initial fires spread"
    if num_fires > 0:

        # Getting wind caracteristics from the file
        print " Getting wind caracteristics from the file"
        wind_record = random.randrange(1,num_winds+1)
        with open(windFile, "r") as wind_f:
            for line in wind_f.readlines():
                line_list = [elem.strip(" \n\r") for elem in line.split(",")]
                if line_list[0] == str(wind_record):
                    critical = int(line_list[1])
                    wind_dir = line_list[2]
                    wind_speed = line_list[3]

        # Checking wind and choosing a method of processing
        # Processing with no wind direction
        if wind_dir == "buffer" or critical == buff_dist_calm:

            print " Critical separation the same as for calm condition or no distinctive wind direction; pre-processed buffer used"

            print "  Critical separation for calm condition: " + str(buff_dist_calm)
            print "  Critical separation for chosen wind: " + str(critical)

            stepVal = 0

            pre_buffer = os.path.join(dataGDB, "BuildingBuffer" + str(critical))
            print "  Creating burn zone by selecting pre-created buffers (for critical separation) with ignited buildings"
            where_clause = ignField + " = 1 and " + combField + " = 1" # use only combustible buildings
            arcpy.MakeFeatureLayer_management(bldgFC, "ign_comb", where_clause) # select ignited buildings
            # Create a layer from buffers
            arcpy.MakeFeatureLayer_management(pre_buffer, "buffers")
            # Select buffers that intersect ignited buildings
            arcpy.SelectLayerByLocation_management("buffers", 'INTERSECT', "ign_comb")
            arcpy.CopyFeatures_management("buffers", burn_scen)

            print "  Selecting buildings within the burn zone"

            # combustible
            print "  - combustible (building footprints)" # (ignited set to 2 for all combustible within a zone as 1 is used for initially ignited)
            arcpy.MakeFeatureLayer_management(bldgFC, "foot_comb", combField + " = 1") # layer of combustible RS buildings
            arcpy.SelectLayerByLocation_management("foot_comb", 'INTERSECT', burn_scen) # selection using burn zones
            arcpy.SelectLayerByAttribute_management('foot_comb','SUBSET_SELECTION', ignField + ' <= 0')
            if int(arcpy.GetCount_management("foot_comb")[0]) > 0:
                arcpy.CalculateField_management("foot_comb", ignField, "2", "PYTHON")

            # non-combustible
            print "  - non-combustible (within the zone)"  # using only footprints not initially ignited
            arcpy.MakeFeatureLayer_management(bldgFC, "fp_non_comb", combField + " = 0 and " + ignField + " <= 0") # layer of non-combustible building footprints
            search_rad = critical / 2.0 # must be added as the burn zones were created with combustible buildings only and buffer of half the critical distance
            arcpy.SelectLayerByLocation_management("fp_non_comb", 'INTERSECT', burn_scen, search_rad) # selection using burn zones (intersects or within half critical distance)
            if int(arcpy.GetCount_management("fp_non_comb")[0]) > 0:

                # calculate ignition field to 2 for all footprints that intersect buffers (plus 1/2 critical sep)
                arcpy.CalculateField_management("fp_non_comb", ignField, "2", "PYTHON") # calculate field to be 2 (for footprints)
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
            print "   Chosen wind speed: " + wind_speed
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
                arcpy.MakeFeatureLayer_management(bldgFC, "layer", where_clause)
                arcpy.CopyFeatures_management("layer", processFC)

                # set list of buffers for each internal step to be merged together
                if stepVal == 1:
                    buffList = []
                else:
                    buffList = [buff_done] # previously created buffer (only newly ignited buildings added)

                dictBuff = {i : "temp_buff" + str(i) for i in range(0,num_steps)} # variable with counter

                # Initial buffer
                #print "   - Initial buffering"
                arcpy.Buffer_analysis(processFC, buff_ini, buff_dist_calm, "", "", "ALL")
                buffList.append(buff_ini)

                for i in range(0,num_steps):

                    # Shift features
                    #print "   - Shifting features: " + str(i + 1)
                    shift_features(processFC, x_shift=move_x, y_shift=move_y)

                    # Buffer
                    #print "   - Buffering: " + str(i + 1)
                    arcpy.Buffer_analysis(processFC, dictBuff[i], buff_dist_calm, "", "", "ALL")
                    buffList.append(dictBuff[i])

                # Merge buffers
                #print "   - Merging buffers"
                arcpy.Merge_management(buffList, buff_process)

                # Select affected buildings and calculate the Ignited field
                #print "   - Updating buildings; adding ignited by spread"
                arcpy.MakeFeatureLayer_management(bldgFC, "bld_lyr")
                # Select using buffer
                arcpy.SelectLayerByLocation_management("bld_lyr", 'INTERSECT', buff_process)
                # Select buildings not already ignited
                arcpy.SelectLayerByAttribute_management('bld_lyr','SUBSET_SELECTION', ignField + ' <= 0 and ' + combField + " = 1")
                numNewBld = int(arcpy.GetCount_management('bld_lyr')[0])
                if numNewBld > 0:
                    # Calculate ignited field
                    #print "      (new buildings ignited)"
                    stepVal += 1
                    arcpy.CalculateField_management('bld_lyr', ignField, stepVal, "PYTHON")  # add the number of step into ignited field
                    # save existing buffer
                    #print "   - Saving the buffer to append to in the next step"
                    if arcpy.Exists(buff_done):
                        arcpy.Delete_management(buff_done)
                    arcpy.Rename_management(buff_process, buff_done)
                else:
                    #print "      (no more buildings ignited)"
                    #print "   - Dissolving buffers"
                    arcpy.Dissolve_management(buff_process, buff_final)
                    switch = 1

            print "   Cleaning workspace"
            for layer in ["temp_buff" + str(i) for i in range(0,num_steps)] + [processFC, buff_ini, buff_process, buff_done]:
                if arcpy.Exists(layer):
                    print "    Deleting " + layer
                    arcpy.Delete_management(layer)


            print "  Selecting buildings within the burn zone"

            # non-combustible
            print "  - non-combustible (within the zone)"
            arcpy.MakeFeatureLayer_management(bldgFC, "fp_non_comb", combField + " = 0 and " + ignField + " <= 0") # layer of non-combustible footprints not initially ignited
            arcpy.SelectLayerByLocation_management("fp_non_comb", 'INTERSECT', burn_scen) # selection using created burn zones
            if int(arcpy.GetCount_management("fp_non_comb")[0]) > 0:

                # calculate ignition field to 2 for all non-conbustible footprints that intersect burn zone
                arcpy.CalculateField_management("fp_non_comb", ignField, "2", "PYTHON") # calculate field to be 2 (for footprints)
            else:
                print "    (none)"

    # get totals
    tot_val = 0
    tot_occ = 0
    where_clause = ignField + " > 0 and " + combField + " = 1"
    arcpy.MakeFeatureLayer_management(bldgFC, "total", where_clause)
    with arcpy.da.SearchCursor ("total", [valField, occField]) as tot_cur:
        for tot_row in tot_cur:
            tot_val = tot_val + int(tot_row[0])
            tot_occ= tot_occ + int(tot_row[1])


    finish_time_scen = datetime.now()
    stepProcessTime = finish_time_scen - start_time_scen
    print " ---Running time: " + str(stepProcessTime)

    # Writing scenario info
    print " Writing scenario info"
    with open(scenFile, "a") as scen_f:
        scen_f.write("{0},{1},{2},{3},{4},{5},{6},{7},{8},{9},{10},{11},{12}\n".format(scenario, pga_table, pga_field, num_ign, num_sup, wind_record, wind_dir, wind_speed, critical, stepVal, stepProcessTime,tot_val,tot_occ))

# Get total time
total_time = datetime.now() - start_time
print "---Total running time: " + str(total_time)

# Import system modules
import pandas as pd
import os, sys

inFile = r'D:\_Working\FFE_Modelling\Data\WindDistributionTable.csv'
outFile = r'D:\_Working\FFE_Modelling\Data\WindScenarios.csv'

out_f = open(outFile, "w")

df = pd.read_csv(inFile, index_col = "WindSpeed")

numc = df.shape[1]
numr = df.shape[0]

cnt = 0
for i in range(0, numr):
    row = df.iloc[i]
    sep = row[numc-1]
    for j in range(0,numc-1):
        wind = df.columns[j]
        if wind == "Variable":
            wind = "buffer"
        num_winds = int(row[j])
        for k in range(0,num_winds):
            cnt += 1
            out_line = '{0}, {1}, {2}\n'.format(cnt, sep, wind)
            out_f.write(out_line)

out_f.close()

# The following prt repalces wind direction with angle or buffer (not used)

##windDict = {'Variable':'buffer', 'N': 180,'NE': 225,'E': 270,'SE': 315,'S': 0,'SW': 45,'W': 90,'NW': 135}
##
##cnt = 0
##for i in range(0, numr):
##    row = df.iloc[i]
##    sep = row[numc-1]
##    for j in range(0,numc-1):
##        wind = windDict[df.columns[j]]
##        num_winds = int(row[j])
##        for k in range(0,num_winds):
##            cnt += 1
##            out_line = '{0}, {1}, {2}\n'.format(cnt, sep, wind)
##            out_f.write(out_line)
##
##out_f.close()
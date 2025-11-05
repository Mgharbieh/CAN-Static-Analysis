import os
from sys import argv
import IDAnalyzer 

### FILE PATH TO THE GITHUB FOLDER TITLED 'MaskFilter'                        ###
### Should be something along the line of:                                    ###
### {SAVE_LOCATION}/CAN-Static-AnalysisSrc/AnalysisSrc/IDBitLength/Test_Cases/ ###
FOLDER = "/Users/abrahamabdulkarim/Documents/code/CAN_bus_research/Src/Modules/IDBitLength/Test_Cases/"
analyzer = IDAnalyzer.IDBitLength()

for item in os.listdir(FOLDER):
    if(item[:5] == "test_"):
        path1 = FOLDER + item
        print('_'*100)
        print(f'Testing {item[5:]}\n')
        for file in os.listdir(path1):
            if(file[-4:] == '.ino' or file[-4:] == '.cpp'):
                print(f'Test: {file}')
                path2 = path1 + '/' + file
                analyzer.checkIDBitLength(path2)
                print()
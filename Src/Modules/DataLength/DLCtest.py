import os
from sys import argv
import dlc_analyzer


FOLDER = "//Users/moeab/CAN_bus_research/Src/Modules/DataLength/Test_Cases/"
#/Users/moeab/CAN_bus_research/Src/Modules/DataLength/Test_Cases/
analyzer = dlc_analyzer.DLCAnalyzer()

for item in os.listdir(FOLDER):
    if(item[:5] == "test_"):
        path1 = FOLDER + item
        print('_' * 100)
        print(f'Testing {item[5:]}\n')
       
        for file in sorted(os.listdir(path1)):
            if(file[-4:] == '.ino' or file[-4:] == '.cpp'):
                print(f'Test: {file}')
                path2 = path1 + '/' + file
                analyzer.checkDLC(path2)
                print()

        
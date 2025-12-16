import os
from sys import argv
import RTRBit

import tree_sitter as TreeSitter
import tree_sitter_cpp as _CPP
CPP_LANGUAGE = TreeSitter.Language(_CPP.language())

### USAGE #######################################################################

# Run in terminal.  
#   argument 1 (argv[1]) is mode, use one of the following
#   - testAll: Runs through all test cases in the Test_Cases folder
#   - testFolder: Tests the test case files in the specified child folder of Test_Cases
#   - testOne: Tests the specified file for the test case.
#
#   argument 2 (argv[2]) is path
#   - Should be path to parent folder or specific file, depending on mode
#
#################################################################################

### FILE PATH TO THE GITHUB FOLDER TITLED 'MaskFilter'                        ###
### Should be something along the line of:                                    ###
### {SAVE_LOCATION}/CAN-Static-AnalysisSrc/AnalysisSrc/MaskFilter/Test_Cases/ ###

#################################################################################

MODE = "testALl"
PATH = "/Users/abrahamabdulkarim/Documents/code/CAN_bus_research/Src/Modules/RTRBit/Test_Cases/"
analyzer = RTRBit.RTRBitChecker()

def testAll():
    for item in os.listdir(PATH):
        if(item[:5] == "test_"):
            path1 = PATH + item
            print('_'*100)
            print(f'Testing {item[5:]}\n')
            for file in os.listdir(path1):
                if(file[-4:] == '.ino' or file[-4:] == '.cpp'):
                    print(f'Test: {file}')
                    path2 = path1 + '/' + file
                    
                    with(open(path2, 'r', encoding='utf-8') as inFile):
                        sourceCode = inFile.read()
                    
                    parser = TreeSitter.Parser(CPP_LANGUAGE)
                    tree = parser.parse(bytes(sourceCode, "utf8"))
                    root = tree.root_node
                    
                    analyzer.checkRTRmode(root)
                    print()

def testFolder(folderPath):
    
    print('_'*100)
    for file in os.listdir(folderPath):
        if(file[-4:] == '.ino' or file[-4:] == '.cpp'):
            print(f'Test: {file}')
            path2 = folderPath + '/' + file
            
            with(open(path2, 'r', encoding='utf-8') as inFile):
                sourceCode = inFile.read()
            
            parser = TreeSitter.Parser(CPP_LANGUAGE)
            tree = parser.parse(bytes(sourceCode, "utf8"))
            root = tree.root_node
            
            analyzer.checkRTRmode(root)
            print()

def testOne(filepath):

    with(open(filepath, 'r', encoding='utf-8') as inFile):
        sourceCode = inFile.read()

    parser = TreeSitter.Parser(CPP_LANGUAGE)
    tree = parser.parse(bytes(sourceCode, "utf8"))
    root = tree.root_node

    analyzer.checkRTRmode(root)
    print()    

###########################################################################################################################################################

if not (os.path.exists(PATH)):
    print("Please enter a valid file path.")
    exit(0)

if(MODE.lower() == "testall"):
    testAll()
elif(MODE.lower() == "testfolder"):
    testFolder(PATH)
elif(MODE.lower() == "testone"):
    testOne(PATH)
else:
    print("Please enter a valid mode.")
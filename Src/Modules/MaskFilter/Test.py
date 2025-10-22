import os
import MaskFilterAnalyzer 

import tree_sitter as TreeSitter
import tree_sitter_cpp as _CPP
CPP_LANGUAGE = TreeSitter.Language(_CPP.language())

### FILE PATH TO THE GITHUB FOLDER TITLED 'MaskFilter'                        ###
### Should be something along the line of:                                    ###
### {SAVE_LOCATION}/CAN-Static-AnalysisSrc/AnalysisSrc/MaskFilter/Test_Cases/ ###
FOLDER = "//100.83.44.15/shared/Michael/UMich/Research/Static_Analysis_Research/Src/Modules/MaskFilter/Test_Cases/"
FOLDER2 = "//100.83.44.15/shared/Michael/UMich/Research/Static_Analysis_Research/Src/Modules/MaskFilter/Test_Cases/test_arduino-mcp2515/"

analyzer = MaskFilterAnalyzer.MaskAndFilter()

def testAll():
    for item in os.listdir(FOLDER):
        if(item[:5] == "test_"):
            path1 = FOLDER + item
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
                    
                    analyzer.checkMaskFilter(root)
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
            
            analyzer.checkMaskFilter(root)
            print()

def testOne(filepath):
    analyzer.checkMaskFilter(filepath)
    print()    

###########################################################################################################################################################

testAll()
#testFolder(FOLDER2)
#testOne("//100.83.44.15/shared/Michael/UMich/Research/Static_Analysis_Research/Src/Modules/MaskFilter/Test_Cases/test_MCP_CAN_lib/testCase-7-8.ino")

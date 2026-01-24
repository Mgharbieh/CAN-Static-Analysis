import platform
import json
import tree_sitter as TreeSitter

import tree_sitter_cpp as _CPP
CPP_LANGUAGE = TreeSitter.Language(_CPP.language())

import Modules.MaskFilter.MaskFilterAnalyzer as mask_filt
import Modules.RTRBit.RTRBit as RTR_Check
import Modules.IDBitLength.IDAnalyzer as id_analyzer
import Modules.DataBytePacking.DataByte_Analyzer as data_byte_packing
import Modules.DataLength.dlc_analyzer as dlc_analyzer

class IssueChecker:

    def __init__(self):
        self.mask_filt_analyzer = mask_filt.MaskAndFilter()
        self.rtr_check_analyzer = RTR_Check.RTRBitChecker()
        self.id_bit_length_analyzer = id_analyzer.IDBitLength()
        self.data_byte_packing_analyzer = data_byte_packing.DataBytePackingAnalyzer()
        self.data_length_analyzer = dlc_analyzer.DLCAnalyzer()
    
    def analyzeFile(self, inputFile):
        dataStream = {}
        issuesFound = 0
        
        if(platform.system() == 'Windows'):
            with(open(inputFile[1:], 'r', encoding='utf-8') as inFile):
                sourceCode = inFile.read()
        else:
            with(open(inputFile, 'r', encoding='utf-8') as inFile):
                    sourceCode = inFile.read()
    
        parser = TreeSitter.Parser(CPP_LANGUAGE)
        tree = parser.parse(bytes(sourceCode, "utf8"))
        RootCursor = tree.root_node

        maskIssuesFound, maskIssueMessages = self.mask_filt_analyzer.checkMaskFilter(RootCursor)
        issuesFound += maskIssuesFound
        dataStream["mask_filt"] = {"mf_issues":maskIssuesFound, "mf_messages":maskIssueMessages}

        rtrIssuesFound, rtrIssueMessages = self.rtr_check_analyzer.checkRTRmode(RootCursor)
        issuesFound += rtrIssuesFound
        dataStream["rtr"] = {"rtr_issues":rtrIssuesFound, "rtr_messages":rtrIssueMessages}

        idLenIssuesFound, idLenIssueMessages = self.id_bit_length_analyzer.checkIDBitLength(RootCursor)
        issuesFound += idLenIssuesFound
        dataStream["idLen"] = {"idLen_issues":idLenIssuesFound, "idLen_messages":idLenIssueMessages}

        self.data_byte_packing_analyzer.checkDataPack(RootCursor)

        dlcIssuesFound, dlcIssueMessages = self.data_length_analyzer.checkDLC(RootCursor)
        issuesFound += dlcIssuesFound
        dataStream["dlc"] = {"dlc_issues":dlcIssuesFound, "dlc_messages":dlcIssueMessages}

        dataStream["totalIssues"] = issuesFound
        dataStream = json.dumps(dataStream)
        return issuesFound, dataStream, sourceCode


'''
mask_filt_analyzer = mask_filt.MaskAndFilter()
rtr_check_analyzer = RTR_Check.RTRBitChecker()
id_bit_length_analyzer = id_analyzer.IDBitLength()
data_byte_packing_analyzer = data_byte_packing.DataBytePackingAnalyzer() 
data_length_analyzer = dlc_analyzer.DLCAnalyzer()

INPUT_FILE = argv[1]

### READ FILE AND BUILD TREE #####################################################################
##################################################################################################

with(open(INPUT_FILE, 'r', encoding='utf-8') as inFile):
    print("-"*100)
    print()
    print("Reading file: '", INPUT_FILE, "'\n", flush=True)
    sourceCode = inFile.read()

print("Analyzing file...\n", flush=True)

parser = TreeSitter.Parser(CPP_LANGUAGE)
tree = parser.parse(bytes(sourceCode, "utf8"))
RootCursor = tree.root_node

##################################################################################################

### ADD CHECKS HERE ##############################################################################

print("-"*100)
print("\nMASK AND FILTER CHECK: \n")
mask_filt_analyzer.checkMaskFilter(RootCursor)
print("-"*100)
print("\nRTR BIT CHECK: \n")
rtr_check_analyzer.checkRTRmode(RootCursor)
print("-"*100)
print("\nID BIT LENGTH CHECK: \n")
id_bit_length_analyzer.checkIDBitLength(RootCursor)
print("-"*100)
print("\nDATA BYTE PACKING CHECK: \n")
data_byte_packing_analyzer.checkDataPack(RootCursor)
print("-"*100)
print("-"*100)
print("\nDLC CHECK: \n")
data_length_analyzer.checkDLC(RootCursor)
##################################################################################################
'''
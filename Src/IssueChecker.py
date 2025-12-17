import tree_sitter as TreeSitter
from sys import argv

import tree_sitter_cpp as _CPP
CPP_LANGUAGE = TreeSitter.Language(_CPP.language())

import Modules.MaskFilter.MaskFilterAnalyzer as mask_filt
import Modules.RTRBit.RTRBit as RTR_Check
import Modules.IDBitLength.IDAnalyzer as id_analyzer
#import Modules.DataBytePacking.DataByte_Analyzer as data_byte_packing

mask_filt_analyzer = mask_filt.MaskAndFilter()
rtr_check_analyzer = RTR_Check.RTRBitChecker()
id_bit_length_analyzer = id_analyzer.IDBitLength()
#data_byte_packing_analyzer = data_byte_packing.DataBytePackingAnalyzer() 

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
#print("\nDATA BYTE PACKING CHECK: \n")
#data_byte_packing_analyzer.checkDataPack(RootCursor)
#print("-"*100)

##################################################################################################

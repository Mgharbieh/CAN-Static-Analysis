import tree_sitter as TreeSitter
from sys import argv

import tree_sitter_cpp as _CPP
CPP_LANGUAGE = TreeSitter.Language(_CPP.language())

import Modules.MaskFilter.MaskFilterAnalyzer as mask_filt

mask_filt_analyzer = mask_filt.MaskAndFilter()
INPUT_FILE = argv[1]

### READ FILE AND BUILD TREE #####################################################################
##################################################################################################

with(open(INPUT_FILE, 'r', encoding='utf-8') as inFile):
    print("Reading file: ", INPUT_FILE, "\n")
    sourceCode = inFile.read()

parser = TreeSitter.Parser(CPP_LANGUAGE)
tree = parser.parse(bytes(sourceCode, "utf8"))
RootCursor = tree.root_node

##################################################################################################

### ADD CHECKS HERE ##############################################################################

mask_filt_analyzer.checkMaskFilter(RootCursor)

##################################################################################################

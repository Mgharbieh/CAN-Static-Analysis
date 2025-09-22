import tree_sitter as TreeSitter
from sys import argv

import tree_sitter_cpp as _CPP
CPP_LANGUAGE = TreeSitter.Language(_CPP.language())

### FILE PATH TO THE GITHUB FOLDER TITLED 'AnalysisSrc' ###
### Should be something along the line of:              ###
### {SAVE_LOCATION}/CAN-Static-AnalysisSrc/AnalysisSrc/ ###
FOLDER = argv[1]

TEST_FILE1 = FOLDER + "MaskFilter/testFile_CJF/testFile.ino"
SAVE_FILE1 = FOLDER + "MaskFilter/testFile_CJF/testFileTree.txt"

TEST_FILE2 = FOLDER + "MaskFilter/testFile_autowp/testFile.ino"
SAVE_FILE2 = FOLDER + "MaskFilter/testFile_autowp/testFileTree.txt"

strList = []
def visit_node(node, level=0):
    indent = "—" * level
    if node.type != "translation_unit" and node.type != "comment":
        strList.append(f"|{indent}Node:{node.type} Text: {node.text.decode()}\n")
    else:
       strList.append(f"|{indent}Node:{node.type}\n")
    for child in node.children:
        visit_node(child, level + 1)

maskList = []
setupFilterList = []
loopFilterList = []

def maskSearch(root):
    
    maskQuery = '''
    (function_definition
        (function_declarator 
            (identifier) @func_Decl
                (#eq? @func_Decl "setup")
        )
        (compound_statement
            (expression_statement
                (call_expression
                    (field_expression
                        (field_identifier) @fd_Name
                    )
                    arguments: (argument_list) @args
                    (#match? @fd_Name "[mM]ask")
                )
            )
        )
    )
    '''

    query = TreeSitter.Query(CPP_LANGUAGE, maskQuery)
    queryCursor = TreeSitter.QueryCursor(query)
    captures = queryCursor.captures(root)
    for cap in captures:
        if cap == 'args':
            argList = captures[cap]
            for args in argList:
                for node in args.children:
                    if(node.type == "number_literal" and ('0x' in node.text.decode())):
                        maskList.append(node.text.decode())

def filterSetupSearch(root):

    setupFilterQuery = '''
    (function_definition
        (function_declarator 
            (identifier) @func_Decl
                (#eq? @func_Decl "setup")
        )
        (compound_statement
            (expression_statement
                (call_expression
                    (field_expression
                        (field_identifier) @fd_Name
                    )
                    arguments: (argument_list) @args
                    (#match? @fd_Name "[fF]ilt")
                    (#not-match? @fd_Name "[mM]ask")  
                )
            )
        )
    )
    '''

    query = TreeSitter.Query(CPP_LANGUAGE, setupFilterQuery)
    queryCursor = TreeSitter.QueryCursor(query)
    captures = queryCursor.captures(root)
    for cap in captures:
        if cap == 'args':
            argList = captures[cap]
            for args in argList:
                for node in args.children:
                    if(node.type == "number_literal" and ('0x' in node.text.decode())):
                        setupFilterList.append(node.text.decode())

def loopFilterSearch(root):

    HEX_CHARS = ['x', 'A', 'B', 'C', 'D', 'E', 'F']
    loopFilterQuery = '''
    (function_definition
        (function_declarator 
            (identifier) @func_Decl
                (#eq? @func_Decl "loop")
        )
        body: (compound_statement) @function.body
    )
    '''

    query = TreeSitter.Query(CPP_LANGUAGE, loopFilterQuery)
    queryCursor = TreeSitter.QueryCursor(query)
    captures = queryCursor.captures(root)
    for cap in captures:
        if(cap == 'function.body'):
            loopText = captures[cap][0].text.decode()

    loopText = loopText.splitlines()
    for line in loopText:
        if(('if' in line) or ('case' in line)):
            if('0x' in line):
                chars = list(line)
                hexVal = ''
                idx = 0
                while(idx < len(chars)):
                    if((chars[idx] == '0') and (chars[idx+1] == 'x')):
                        hexVal += chars[idx]
                        hexVal += chars[idx+1]
                        idx += 2
                        continue
                    elif((len(hexVal) >= 2) and ((chars[idx].isdigit()) or (chars[idx] in HEX_CHARS))):
                        hexVal += chars[idx]
                    else:
                        if('0x' in hexVal[:2] and (len(hexVal) > 2 and len(hexVal) < 6)): #Only works for standard IDs now, will figure out extended later
                            if(hexVal not in loopFilterList):
                                loopFilterList.append(hexVal)
                                hexVal = ''
                    idx += 1
                    
def maskFilterCheck(root):

    maskSearch(root)
    filterSetupSearch(root)
    loopFilterSearch(root)
   
    maskWarn = False
    usageWarn = False
    unusedList = []

    excludedWarn = False
    excludeList = []

    for filter in setupFilterList:
        for mask in maskList:
            if(mask and filter != filter):
                maskWarn = True 
        
        if(filter not in loopFilterList):
            usageWarn = True
            unusedList.append(filter)
    
    for filt in loopFilterList:
        if(filt not in setupFilterList):
            excludedWarn = True
            excludeList.append(filt)

    print("#"*100,'\n')
    if(maskWarn):   
        print("Mask(s) set aren't applied across the full filter value. Is that intentional?")
    if(usageWarn and (len(setupFilterList) > 1)):
        print(unusedList, "were setup in the filter but never explicitly used.")
    else:
        usageWarn = False 
    if(excludedWarn):
         print(excludeList, "were being checked but are excluded from the filter.") if len(excludeList) > 1 else print(excludeList, "was being checked but is excluded from the filter.")

    if((not maskWarn) and (not usageWarn) and (not excludedWarn)):
        print("No issues detected!")
    print()
    print("#"*100)
            
############################################################################################################################################################

with(open(TEST_FILE2, 'r', encoding='utf-8') as inFile):
    sourceCode = inFile.read()

parser = TreeSitter.Parser(CPP_LANGUAGE)
tree = parser.parse(bytes(sourceCode, "utf8"))
RootCursor = tree.root_node
maskFilterCheck(RootCursor)


#FOR MANUAL PATTERN DETECTION, IGNORE THIS
'''
visit_node(RootCursor)
with(open(SAVE_FILE2, 'w', encoding='utf-8') as inFile):
    for line in strList:
        inFile.write(line)
'''
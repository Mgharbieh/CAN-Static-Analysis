import tree_sitter as TreeSitter
from sys import argv

import tree_sitter_cpp as _CPP
CPP_LANGUAGE = TreeSitter.Language(_CPP.language())

class MaskAndFilter():
    def __init__(self):
        self.strList = []
        self.maskList = []
        self.setupFilterList = []
        self.loopFilterList = []

    def _reset(self):
        self.strList = []
        self.maskList = []
        self.setupFilterList = []
        self.loopFilterList = []

    #############################################################################
    def _maskSearch(self, root):    
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
                            self.maskList.append(node.text.decode())
    #############################################################################
    def _filterSetupSearch(self, root):
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
                            self.setupFilterList.append(node.text.decode())
    #############################################################################
    def _loopFilterSearch(self, root):

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
        loopText = ""
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
                                if(hexVal not in self.loopFilterList):
                                    self.loopFilterList.append(hexVal)
                                    hexVal = ''
                        idx += 1
    #############################################################################
    def _maskFilterCheck(self, root):

        self._maskSearch(root)
        self._filterSetupSearch(root)
        self._loopFilterSearch(root)
    
        maskWarn = False
        usageWarn = False
        unusedList = []

        excludedWarn = False
        excludeList = []

        if(len(self.maskList) == 0 and len(self.setupFilterList) == 0 and len(self.loopFilterList) == 0):
            print("#"*100,'\n')
            print("No Mask/Filter usage found\n")
            print("#"*100,'\n')
            return
        elif(len(self.maskList) == 0 and len(self.setupFilterList) > 0):
            print(f'{self.setupFilterList} was set up during initialization but no masks were set!')
    

        for filter in self.setupFilterList:
            for mask in self.maskList:
                if((int(mask, 16) & int(filter, 16)) != int(filter, 16)):
                    maskWarn = True 
            
            if(filter not in self.loopFilterList):
                usageWarn = True
                unusedList.append(filter)
        
        for filt in self.loopFilterList:
            if(filt not in self.setupFilterList):
                excludedWarn = True
                excludeList.append(filt)

        print("#"*100,'\n')
        if(maskWarn):   
            print("Mask(s) set aren't applied across the full filter value. Is that intentional?")
        if(usageWarn and (len(self.setupFilterList) > 1)):
            print(unusedList, "were setup in the filter but never explicitly used.")
        else:
            usageWarn = False 
        if(excludedWarn):
            print(excludeList, "were being checked but are excluded from the filter.") if len(excludeList) > 1 else print(excludeList, "was being checked but is excluded from the filter.")

        if((not maskWarn) and (not usageWarn) and (not excludedWarn)):
            print("No Mask/Filter issues detected!")
        print()
        print("#"*100)
    #############################################################################
    def checkMaskFilter(self, file_input):

        with(open(file_input, 'r', encoding='utf-8') as inFile):
            sourceCode = inFile.read()

        parser = TreeSitter.Parser(CPP_LANGUAGE)
        tree = parser.parse(bytes(sourceCode, "utf8"))
        RootCursor = tree.root_node
        self._maskFilterCheck(RootCursor)
        self._reset()




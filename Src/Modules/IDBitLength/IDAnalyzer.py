import tree_sitter as TreeSitter
from sys import argv
 
import tree_sitter_cpp as _CPP
CPP_LANGUAGE = TreeSitter.Language(_CPP.language())

class IDBitLength():
    def __init__(self):
        self.mode = ""
        self.frameIDList = []

    def _reset(self):
        self.mode = ""
        self.frameIDList = []

    #############################################################################
    def _modeSearch(self, root):  

        setupQuery = '''
            (function_definition
                body: (compound_statement
                        [(expression_statement
                            (assignment_expression
                                (field_expression
                                    (identifier) @fd_id
                                    (field_identifier) @func_name
                                ) @fd_ex
                                (binary_expression 
                                    (number_literal) @ids
                                    (identifier) @flag
                                ) @b_ex
                            ) @a_ex
                        )
                        (expression_statement
                            (assignment_expression
                                (field_expression
                                    (identifier) @fd_id
                                    (field_identifier) @func_name
                                ) @fd_ex
                                (number_literal)@ids
                            ) @a_ex
                        )
                        (if_statement
                            (condition_clause
                                (binary_expression
                                    (call_expression
                                        (field_expression
                                            (identifier) @fd_id
                                            (field_identifier) @fd_Name
                                        ) @fd_ex
                                        arguments: (argument_list) @args
                                    )
                                )
                            )
                        )
                        (if_statement
                            (else_clause
                                (compound_statement
                                    (expression_statement
                                        (call_expression
                                            (field_expression 
                                                (identifier) @fd_id
                                                (field_identifier) @fd_Name
                                            ) @fd_ex
                                            arguments: (argument_list) @args
                                        )
                                    )
                                )
                            )
                        )]
                    ) @func_body (#eq? @func_name "can_id")
            )
        '''

        query = TreeSitter.Query(CPP_LANGUAGE, setupQuery)
        queryCursor = TreeSitter.QueryCursor(query)
        captures = queryCursor.captures(root)
        
        for cap in captures:
            #get the frame name, id, and count the bits (7ff vs 1fffffff)
            if cap == 'a_ex':
                pair = []
                idList = captures[cap]
                for id in idList:
                    for node in id.children:
                        if(node.type == "binary_expression"):
                            for field in node.children:
                                if(field.type == "number_literal" and ('0x' in node.text.decode())):
                                    pair.append(field.text.decode()) #idList
                                    if(int(field.text.decode(),16) > 0x7FF):
                                        self.mode = "extended"
                                        pair.append("extended")
                                    elif(int(field.text.decode(),16) <= 0x7FF):
                                        self.mode = "standard"
                                        pair.append("standard")
                                if(field.type == "identifier"):
                                    if(field.text.decode() == "CAN_EFF_FLAG"):
                                        pair.append("extended") #frameIDList
                                    else:
                                        pair.append("standard")
                            self.frameIDList.append(pair)
                            pair = []
                        elif(node.type == "number_literal"):
                            pair.append(node.text.decode())
                            if(int(node.text.decode(),16) > 0x7FF):
                                self.mode = "extended"
                                pair.append("extended")
                                pair.append("standard")
                            elif(int(node.text.decode(),16) <= 0x7FF): 
                                self.mode = "standard"
                                pair.append("standard")
                                pair.append("standard")
                            self.frameIDList.append(pair)
                            #print(self.frameIDList)
                            pair = []

        #Create Booleans for std and ext and set true when it sees them


    #############################################################################

    def _modeSearch2(self, root):  

        setupQuery = '''
            (function_definition
                body: (compound_statement
                        [(expression_statement
                            (assignment_expression
                                (field_expression
                                    (identifier) @fd_id2
                                    (field_identifier) @func_name2
                                ) @fd_ex2
                                (number_literal)@ids2
                            ) @a_ex2 
                        )
                        (expression_statement
                            (assignment_expression
                                (field_expression
                                    (identifier) @fd_id2
                                    (field_identifier) @func_name2
                                ) @fd_ex2
                                (identifier) @modes2
                            ) @a_ex2
                        )]
                    ) @func_body2 (#match? @func_name2 "^(id|extended)$")
            )
        '''

        query = TreeSitter.Query(CPP_LANGUAGE, setupQuery)
        queryCursor = TreeSitter.QueryCursor(query)
        captures = queryCursor.captures(root)

        for cap in captures:
            #get the frame name, id, and count the bits (7ff vs 1fffffff)
            if cap == 'a_ex2':
                pair = []
                sorted_caps = sorted(captures['a_ex2'], key=lambda n: n.start_byte)
                assignmentList = sorted_caps
                for assignment in assignmentList:
                    for node in assignment.children:
                        if(node.type == "number_literal"):
                            pair.append(node.text.decode())
                            if(int(node.text.decode(),16) > 0x7FF):
                                self.mode = "extended"
                                pair.append("extended")
                            elif(int(node.text.decode(),16) <= 0x7FF):
                                self.mode = "standard"
                                pair.append("standard")
                        elif(node.type == "identifier"):
                            if(node.text.decode() == "CAN_STANDARD_FRAME"):
                                pair.append("standard")
                            elif(node.text.decode() == "CAN_EXTENDED_FRAME"):
                                pair.append("extended")
                            self.frameIDList.append(pair)
                            #print(self.frameIDList)
                            pair = []
                            
                                
                            
                        

                        


                        # if(node.type == "binary_expression"):
                        #     for field in node.children:
                        #         if(field.type == "number_literal" and ('0x' in node.text.decode())):
                        #             pair.append(field.text.decode()) #idList
                        #             if(int(field.text.decode(),16) > 0x7FF):
                        #                 self.mode = "extended"
                        #                 pair.append("extended")
                        #             elif(int(field.text.decode(),16) <= 0x7FF):
                        #                 self.mode = "standard"
                        #                 pair.append("standard")
                        #         if(field.type == "identifier"):
                        #             if(field.text.decode() == "CAN_EFF_FLAG"):
                        #                 pair.append("extended") #frameIDList
                        #             else:
                        #                 pair.append("standard")
                        #     self.frameIDList.append(pair)
                        #     pair = []
                        # elif(node.type == "number_literal"):
                        #     pair.append(node.text.decode())
                        #     if(int(node.text.decode(),16) > 0x7FF):
                        #         self.mode = "extended"
                        #         pair.append("extended")
                        #         pair.append("standard")
                        #     elif(int(node.text.decode(),16) <= 0x7FF): 
                        #         self.mode = "standard"
                        #         pair.append("standard")
                        #         pair.append("standard")
                        #     self.frameIDList.append(pair)
                        #     pair = []

        #Create Booleans for std and ext and set true when it sees them


    #############################################################################

    def _modeSearch3(self, root):  

        setupQuery = '''
            (function_definition
                body: (compound_statement
                        [(expression_statement
                            (call_expression
                                (field_expression
                                    (identifier) @fd_id3
                                    (field_identifier) @func_name3
                                ) @fd_ex3
                                (argument_list
                                    (number_literal) @fd_id3
                                    (number_literal) @fd_flag3
                                    (number_literal) @fd_dlc3
                                    (identifier) @fd_data3
                                ) @arg_list3
                            ) @c_ex3
                        )
                        
                        (declaration
                            (init_declarator
                                (call_expression
                                    (field_expression
                                        (identifier) @fd_id3
                                        (field_identifier) @func_name3
                                    ) @fd_ex3
                                    (argument_list
                                        (number_literal) @fd_id3
                                        (number_literal) @fd_flag3
                                        (number_literal) @fd_dlc3
                                        (identifier) @fd_data3
                                    ) @arg_list3
                                ) @c_ex3
                            )
                        )
                        (if_statement
                            (condition_clause
                                (binary_expression
                                    (call_expression
                                        (field_expression
                                            (identifier) @fd_id3
                                            (field_identifier) @func_name3
                                        ) @fd_ex3
                                        (argument_list
                                            (number_literal) @fd_id3
                                            (number_literal) @fd_flag3
                                            (number_literal) @fd_dlc3
                                            (identifier) @fd_data3
                                        ) @arg_list3
                                    ) @c_ex3
                                )
                            )
                        )]
                    ) @func_body3   (#match? @func_name3 "sendMsgBuf")
            )
        '''

        query = TreeSitter.Query(CPP_LANGUAGE, setupQuery)
        queryCursor = TreeSitter.QueryCursor(query)
        captures = queryCursor.captures(root)
        
        for cap in captures:
            #get the frame name, id, and count the bits (7ff vs 1fffffff)
            if cap == 'c_ex3':
                pair = []
                sendList = captures[cap]
                for send in sendList:
                    for node in send.children:
                        if(node.type == "field_expression"):
                            for field in node.children:
                                if(field.type =="identifier"):
                                    #pair.append(field.text.decode())
                                    continue
                        if(node.type == "argument_list"):
                            pair.append(node.children[1].text.decode())
                            if(int(node.children[1].text.decode(),16) <= 0x7FF):
                                pair.append("standard")
                            elif(int(node.children[1].text.decode(),16) > 0x7FF):
                                pair.append("extended")
                            
                            if(node.children[3].text.decode() == "0"):
                                pair.append("standard")
                            elif(node.children[3].text.decode() == "1"):
                                pair.append("extended")

                            self.frameIDList.append(pair)
                            #print(self.frameIDList)
                            pair = []


                        #         if(field.type == "number_literal" and ('0x' in node.text.decode())):
                        #             pair.append(field.text.decode()) #idList
                        #             if(int(field.text.decode(),16) > 0x7FF):
                        #                 self.mode = "extended"
                        #                 pair.append("extended")
                        #             elif(int(field.text.decode(),16) <= 0x7FF):
                        #                 self.mode = "standard"
                        #                 pair.append("standard")
                        #         if(field.type == "identifier"):
                        #             if(field.text.decode() == "CAN_EFF_FLAG"):
                        #                 pair.append("extended") #frameIDList
                        #             else:
                        #                 pair.append("standard")
                        #     self.frameIDList.append(pair)
                        #     pair = []
                        # elif(node.type == "number_literal"):
                        #     pair.append(node.text.decode())
                        #     if(int(node.text.decode(),16) > 0x7FF):
                        #         self.mode = "extended"
                        #         pair.append("extended")
                        #         pair.append("standard")
                        #     elif(int(node.text.decode(),16) <= 0x7FF): 
                        #         self.mode = "standard"
                        #         pair.append("standard")
                        #         pair.append("standard")
                        #     self.frameIDList.append(pair)
                        #     pair = []

        #Create Booleans for std and ext and set true when it sees them


    #############################################################################


    def _sendSearch(self, root):  

        setupQuery = '''
            (function_definition
                (function_declarator 
                    (identifier) @func_Decl
                        (#eq? @func_Decl "loop")
                )
                body: (compound_statement
                        [(expression_statement
                            (call_expression
                                (field_expression
                                    (identifier) @fd_id
                                    (field_identifier) @func_name
                                ) @fd_ex
                                (argument_list) @args
                            ) @c_ex
                        )]
                    ) @func_body (#eq? @func_name "sendMessage")
            )
        '''

        query = TreeSitter.Query(CPP_LANGUAGE, setupQuery)
        queryCursor = TreeSitter.QueryCursor(query)
        captures = queryCursor.captures(root)
        
        for cap in captures:
            #get the frame name, id, and count the bits (7ff vs 1fffffff)
            if cap == 'c_ex':
                pair = []
                sendList = captures[cap]
                for send in sendList:
                    for node in send.children:
                        if(node.type == "argument_list"):
                            frametype = "standard"
                            for arg in node.children:
                                if(arg.text.decode() == "MCP2515::TXB1"):
                                    frametype = "extended"
                                if(arg.type == "pointer_expression"):
                                    pair.append(arg.text.decode())
                                    pair.append(frametype)
                                    
                                    
                                    
                                
                                
                    #self._addData(pair[0],pair[1])
                    print(pair)
                    pair = []

        #Create Booleans for std and ext and set true when it sees them


    #############################################################################

    def _addData(self, frameID ,data):
        frameID = frameID.lstrip('&')
        for frame in self.frameIDList:
            if frame[0] == frameID:
                frame.append(data)
    
     #############################################################################
    
    def _idBitLengthCheck(self, root):

        self._modeSearch(root)
        self._modeSearch2(root)
        self._modeSearch3(root)
        #self._sendSearch(root)
    
        # maskSetupWarn = False
        # maskWarn = False
        # usageWarn = False
        # unusedList = []

        # excludedWarn = False
        # excludeList = []

        #setup to look in loop also and separate the output messages

        print("#"*100,'\n')

        if(self.frameIDList == []):
            print("No ID Bit Length usage found")
        for frame in self.frameIDList:
            if(frame[1]==frame[2]):
                print(frame[0] + " has no errors, " + frame[2] + " ID bit length is properly set and sent")
            elif(frame[1]!=frame[2]):
                print("A(n) " + frame[1] + " ID Bit Length is set during frame initialization for " + frame[0] + " but uses a(n) " + frame[2] + " flag when sending message.")

        print()
        print("#"*100)

        # if(len(self.maskList) == 0 and len(self.setupFilterList) == 0 and len(self.loopFilterList) == 0):
        #     print("#"*100,'\n')
        #     print("No Mask/Filter usage found\n")
        #     print("#"*100,'\n')
        #     return
        # elif(len(self.maskList) == 0 and len(self.setupFilterList) > 0):
        #     maskSetupWarn = True
        # elif(len(self.maskList) == 0 and len(self.setupFilterList) == 0 and len(self.loopFilterList) > 0):
        #     print("#"*100,'\n')
        #     print("No filters were set during initialization, but address checking is being done.  Consider adding filters during initialization to optimize this code.\n")
        #     print("#"*100,'\n')
        #     return
            
        # for filter in self.setupFilterList:
        #     for mask in self.maskList:
        #         if((int(mask, 16) & int(filter, 16)) != int(filter, 16)):
        #             maskWarn = True 
            
        #     if(filter not in self.loopFilterList):
        #         usageWarn = True
        #         unusedList.append(filter)
        
        # for filt in self.loopFilterList:
        #     if(filt not in self.setupFilterList):
        #         excludedWarn = True
        #         excludeList.append(filt)

        # print("#"*100,'\n')
        # if(maskSetupWarn):
        #     print(f'Filters {self.setupFilterList} were set up during initialization but no masks were set!') if len(self.setupFilterList) > 1 else print(f'Filter {self.setupFilterList} was set up during initialization but no masks were set!')
        # if(maskWarn):   
        #     print("Mask(s) set aren't applied across the full filter value. Is that intentional?")
        # if(usageWarn and (len(self.setupFilterList) > 1)):
        #     print(unusedList, "were setup in the filter but never explicitly used.") if len(unusedList) > 1 else print(unusedList, "was setup in the filter but never explicitly used.")
        # else:
        #     usageWarn = False 
        # if(excludedWarn):
        #     print(excludeList, "were being checked but are excluded from the filter.") if len(excludeList) > 1 else print(excludeList, "was being checked but is excluded from the filter.")

        # if((not maskSetupWarn) and (not maskWarn) and (not usageWarn) and (not excludedWarn)):
        #     print("No Mask/Filter issues detected!")
        # print()
        # print("#"*100)
    #############################################################################
    def checkIDBitLength(self, root):

        # with(open(file_input, 'r', encoding='utf-8') as inFile):
        #     sourceCode = inFile.read()

        # parser = TreeSitter.Parser(CPP_LANGUAGE)
        # tree = parser.parse(bytes(sourceCode, "utf8"))
        # RootCursor = tree.root_node
        self._idBitLengthCheck(root)
        self._reset()
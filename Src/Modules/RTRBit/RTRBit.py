import tree_sitter as TreeSitter

import tree_sitter_cpp as _CPP
CPP_LANGUAGE = TreeSitter.Language(_CPP.language())

class RTRBitChecker:
    def __init__(self):
        self.msgList = []
        self.resultList = []
    
    def _reset(self):
        self.msgList = []
        self.resultList = []

    def _checkRTRMode(self, root):

        rtrQuery0 = '''
        (function_definition
            body: (compound_statement
                [(_) @sendBuf         
                    (#match? @sendBuf "[cC][aA][nN](\d*)\.[Ss]endMsgBuf") 
                (expression_statement
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
                        (number_literal) @ids
                    ) @a_ex
                )]
            ) @func_body 
        )

        (#match? @fd_id "^[cC][aA][nN](\d*)\.$")
        '''

        rtrQuery = '''
        (function_definition
            body: (compound_statement
                (expression_statement
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
            ) @func_body 
            (#match? @fd_id "^[cC][aA][nN](\d*)\.$")
        )

        (function_definition
            body: (compound_statement
                (expression_statement
                    (assignment_expression
                        (field_expression
                            (identifier) @fd_id
                            (field_identifier) @func_name
                        ) @fd_ex
                        (number_literal) @ids
                    ) @a_ex
                )
            ) @func_body 
            (#match? @fd_id "^[cC][aA][nN](\d*)\.$")
        )

        (function_definition
            body: (compound_statement
                (declaration
                    (init_declarator
                        (identifier) @fd_id_2
                        (binary_expression 
                            (number_literal) @ids_2
                            (identifier) @flag_2
                        ) @b_ex_2
                    )
                )
            ) @func_body 
        )

        (function_definition
            body: (compound_statement
                (declaration
                    (init_declarator
                        (identifier) @fd_id_2
                        (binary_expression 
                            (number_literal) @ids_2
                            (number_literal) @flag_2
                        ) @b_ex_2
                    )
                )
            ) @func_body 
        )

        (function_definition
            body: (compound_statement
                (_) @sendBuf         
            ) @func_body 
            (#match? @sendBuf "[cC][aA][nN](\d*)\.[Ss]endMsgBuf") 
        )

        (function_definition
            body: (compound_statement
                (_) @setMsg          
            ) @func_body 
            (#match? @setMsg "[cC][aA][nN](\d*)\.[Ss]etMsg")
        )
        '''

        query = TreeSitter.Query(CPP_LANGUAGE, rtrQuery)
        queryCursor = TreeSitter.QueryCursor(query)
        captures = queryCursor.captures(root)
        
        functionText = None
        for cap in captures:
            #get the frame name, id, and count the bits (7ff vs 1fffffff)
            if(cap == 'func_body'):
                functionText = captures[cap][0].text.decode()
                functionText = functionText.splitlines()
            if cap == 'a_ex':
                pair = []
                idList = captures[cap]
                for id in idList:
                    lineString = id.text.decode()
                    for node in id.children:
                        if(node.type == "binary_expression"):
                            for field in node.children:
                                if(field.type == "number_literal" and ('0x' in node.text.decode())):
                                    pair.append(field.text.decode()) #idList
                                if(field.type == "identifier"):
                                    if((field.text.decode() == "CAN_RTR_FLAG") or (field.text.decode() == "0x40000000")):
                                        pair.append(True) #frameIDList
                                        lineString = lineString.split('.')
                                        pair.append(lineString[0])
                                        self.msgList.append(pair)
                                    else:
                                        pair.append( False)
                
                for msg in self.msgList:
                    can_obj = msg[2]
                    can_addr = msg[0]
                    for line in functionText:
                        if((can_obj + '(' + can_addr + ") set the RTR bit to high but it has a data length associated with it.") in self.resultList):
                            continue
                        elif((can_obj in line) and (('dlc' in line.lower()) or ('data' in line.lower()))):
                            issueStr = can_obj + '(' + can_addr + ") set the RTR bit to high but it has a data length associated with it."
                            self.resultList.append(issueStr)

            if cap == 'sendBuf':
                pair = []
                sendList = captures[cap]
                for sendFunc in sendList:
                    lineString = sendFunc.text.decode().strip()
                    lineString = lineString[0:(len(lineString)-2)]
                    lineString = lineString.split('(')[1]
                    args = lineString.split(',')
                    
                    if(len(args) < 5):
                        continue

                    if(args[2].lower().strip() == 'rtr'):
                        for textLine in functionText:
                            textLine = textLine.lower()
                            if(('rtr' in textLine) and ('=' in textLine)):
                                rtrBit = textLine.split('=')[1][:-1].strip() 
                                args[2] = int(rtrBit)
                            if(('dlc' in textLine) and ('=' in textLine)):
                                dlcSize = textLine.split('=')[1].strip().strip(';')
                                args[3] = int(dlcSize)

                    if(int(args[2]) == 1):
                        pair.append(args[0])
                        pair.append(True)
                        self.msgList.append(pair)

                        if(int(args[3]) != 0 or (args[4].strip() != 'NULL' and args[4].strip() != 'nullptr')):
                            if((sendFunc.text.decode() + " set the RTR bit to high but it has a data length associated with it.") in self.resultList):
                                continue
                            else:
                                issueStr = sendFunc.text.decode() + " set the RTR bit to high but it has a data length associated with it."
                                self.resultList.append(issueStr)
                    elif(int(args[2]) == 0):
                        pair.append(args[0])
                        pair.append(False)
                        self.msgList.append(pair)

            if(cap == "b_ex_2"):
                pair = []
                functionText = captures['func_body'][0].text.decode()
                functionText = functionText.splitlines()
                for idx in range(0, len(captures[cap])):
                    can_id_name = captures['fd_id_2'][idx].text.decode()
                    id_attributes = captures[cap][idx].text.decode()
                    id_attributes = id_attributes.split('|')

                    isRtr = False
                    for attr in id_attributes:
                        if(attr.strip() == '0x40000000'):
                            isRtr = True
                        elif(attr.strip() == '0x80000000'): #EXT flag, do nothing
                            continue
                        else:
                            can_id = attr.strip()
                    
                    pair.append(can_id)
                    pair.append(isRtr)
                    pair.append(can_id_name)
                    pair.append(captures[cap][idx].text.decode())
                    self.msgList.append(pair)
  
                for canIDFlags in self.msgList:
                    id_name = canIDFlags[2]
                    for lines in functionText:
                        if((id_name in lines) and ('=' not in lines)):
                            senderLine = lines.strip()
                            sender = senderLine[0:(len(senderLine)-2)]
                            sender = sender.split('(')[1]
                            args = sender.split(',')

                            if(int(args[2]) != 0 or (args[3].strip() != 'NULL' and args[3].strip() != 'nullptr')):
                                if(("message ID '" + id_name + '\' (' + canIDFlags[3] + ") set the RTR bit to high but it has a data length associated with it in " + senderLine) in self.resultList):
                                    continue
                                else:
                                    issueStr = "message ID '" + id_name + '\' (' + canIDFlags[3] + ") set the RTR bit to high but it has a data length associated with it in " + senderLine
                                    self.resultList.append(issueStr)

        if(len(self.msgList) == 0):
            print("No remote transmission requests found.")
            print()
            print('_'*100)
            return
        if(len(self.resultList) == 0):
            print("No issues detected!")
            print()
            print('_'*100)
            return
        else:
            for issue in self.resultList:
                print(issue)
            print()
            print('_'*100)
            return




    def checkRTRmode(self, root):
        self._reset()
        self._checkRTRMode(root)

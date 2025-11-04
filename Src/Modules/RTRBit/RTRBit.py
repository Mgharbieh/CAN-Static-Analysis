import tree_sitter as TreeSitter

import tree_sitter_cpp as _CPP
CPP_LANGUAGE = TreeSitter.Language(_CPP.language())

class RTRBitChecker:
    def __init__(self):
        self.msgList = []
        self.resultList = []

    def _checkRTRMode(self, root):

        rtrQuery = '''
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
  
        (assignment_expression
            left: (identifier) @variableName
            right: (_) @value
            (#match? @variableName "[Rr][Tt][Rr]")
            (#match? @variableName "[Dd][Ll][Cc]")
        )
        (init_declarator
            declarator: (identifier) @variableName
            value: (_) @value
            (#match? @variableName "[Rr][Tt][Rr]")
            (#match? @variableName "[Dd][Ll][Cc]")
        )

        (#match? @fd_id "^[cC][aA][nN](\d*)\.$")
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
                                    if(field.text.decode() == "CAN_RTR_FLAG"):
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
                    lineString = sendFunc.text.decode()
                    lineString = lineString[0:(len(lineString)-2)]
                    lineString = lineString.split('(')[1]
                    args = lineString.split(',')
                    

                    if(args[2].lower().strip() == 'rtr'):
                        for textLine in functionText:
                            textLine = textLine.lower()
                            if(('rtr' in textLine) and ('=' in textLine)):
                                rtrBit = textLine.split('=')[1][:-1].strip() 
                                args[2] = int(rtrBit)
                            if(('dlc' in textLine) and ('=' in textLine)):
                                dlcSize = textLine.split('=')[1][:-1].strip() 
                                args[3] = int(dlcSize)

                    if(int(args[2]) == 1):
                        pair.append(args[0])
                        pair.append(True)
                        self.msgList.append(pair)

                        if(int(args[3]) != 0 or args[4].strip() != 'NULL'):
                            if((sendFunc.text.decode() + " set the RTR bit to high but it has a data length associated with it.") in self.resultList):
                                continue
                            else:
                                issueStr = sendFunc.text.decode() + " set the RTR bit to high but it has a data length associated with it."
                                self.resultList.append(issueStr)
                    elif(int(args[2]) == 0):
                        pair.append(args[0])
                        pair.append(False)
                        self.msgList.append(pair)

        

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
        self._checkRTRMode(root)

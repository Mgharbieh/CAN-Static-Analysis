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
                        (number_literal) @ids
                    ) @a_ex
                )]
            ) @func_body 
        )

        (#match? @fd_id "^[cC][aA][nN](\d*)\.$")
        '''

        rtrQuery1 = '''
        (function_definition
            body: (compound_statement
                [(declaration
                    (init_declarator
                        (identifier) @fd_id_2
                        (binary_expression 
                            (number_literal) @ids_2
                            (number_literal) @flag_2
                        ) @b_ex_2
                    )
                )
                (expression_statement
                    (call_expression
                        (field_expression) @fd_expr
                        (argument_list) @arg_list
                    ) @call_expr
                    (#match? @call_expr "0x40000000") 
                )]
            ) @func_body 
        )

        (#match? @fd_expr "^[cC][aA][nN](\d*)\.[Ss]endMsgBuf&")
        '''

        rtrQuery2 = '''
        (function_definition
            body: (compound_statement
                (_) @sendBuf         
            ) @func_body 
            (#match? @sendBuf "[cC][aA][nN](\d*)\.[Ss]endMsgBuf") 
        )
        '''

        QUERY_LIST = [rtrQuery0, rtrQuery1, rtrQuery2]

        for rtrQuery in QUERY_LIST:
            query = TreeSitter.Query(CPP_LANGUAGE, rtrQuery)
            queryCursor = TreeSitter.QueryCursor(query)
            captures = queryCursor.captures(root)
            if(len(captures) != 0):
                break
        
        functionText = None
        for cap in captures:
            if(cap == 'func_body'):
                startingLineNum = captures[cap][0].start_point.row + 1
                functionText = captures[cap][0].text.decode()
                functionText = functionText.splitlines()
            if cap == 'a_ex':
                idList = captures[cap]
                for id in idList:
                    pair = []
                    lineString = id.text.decode()
                    for node in id.children:
                        if(node.type == "binary_expression"):
                            for field in node.children:
                                if(field.type == "number_literal" and ('0x' in node.text.decode()) and (node.text.decode() != "0x40000000")):
                                    pair.append(field.text.decode()) #idList
                                if(field.type == "identifier"):
                                    if((field.text.decode() == "CAN_RTR_FLAG") or (field.text.decode() == "0x40000000")):
                                        pair.append(True) 
                                        lineString = lineString.split('.')
                                        pair.append(lineString[0])
                                        self.msgList.append(pair.copy())
                                    else:
                                        pair.append(False)
                                        self.msgList.append(pair.copy())
                
                for msg in self.msgList:
                    can_obj = msg[2]
                    can_addr = msg[0]
                    for line in functionText:
                        if((can_obj + '(' + can_addr + ") set the RTR bit to high but it has a data length associated with it.") in self.resultList):
                            continue
                        elif((can_obj in line) and (('dlc' in line.lower()) or ('data' in line.lower()))):
                            if(('dlc = 0' not in line) and ('dlc= 0' not in line) and ('dlc =0' not in line) and ('dlc=0' not in line)):
                                issueStr = can_obj + '(' + can_addr + ") set the RTR bit to high but it has a data length associated with it."
                                self.resultList.append(issueStr)

            if cap == 'sendBuf':
                sendList = captures[cap]
                for sendFunc in sendList:
                    pair = []
                    lineNum = sendFunc.start_point.row + 1
                    lineString = sendFunc.text.decode().strip()
                    lineString = lineString[0:(len(lineString)-2)]
                    lineString = lineString.split('(')[1]
                    args = lineString.split(',')
                    if(len(args) < 5):
                        continue

                    try:
                        args[2] = int(args[2].strip())
                    except:
                        rangeStart = lineNum - startingLineNum
                        for lineIDX in range(rangeStart, 0, -1):
                            textLine = functionText[lineIDX].lower()
                            if((args[2].strip() in textLine) and ('=' in textLine)):
                                rtrBit = textLine.split('=')[1][:-1].strip() 
                                args[2] = int(rtrBit)
                                break

                    try:
                        args[3] = int(args[3].strip())
                    except:
                        rangeStart = lineNum - startingLineNum
                        for lineIDX in range(rangeStart, 0, -1):
                            textLine = functionText[lineIDX].lower()
                            if((args[3].strip() in textLine) and ('=' in textLine)):
                                dlcSize = textLine.split('=')[1].strip().strip(';')
                                args[3] = int(dlcSize)
                                break

                    if(args[2] == 1):
                        pair.append(args[0])
                        pair.append(True)
                        self.msgList.append(pair.copy())

                        if(args[3] != 0 or (args[4].strip() != 'NULL' and args[4].strip() != 'nullptr')):
                            if((sendFunc.text.decode() + " set the RTR bit to high but it has a data length associated with it.") in self.resultList):
                                continue
                            else:
                                issueStr = sendFunc.text.decode() + " set the RTR bit to high but it has a data length associated with it."
                                self.resultList.append(issueStr)
                    elif(args[2] == 0):
                        pair.append(args[0])
                        pair.append(False)
                        self.msgList.append(pair.copy())

            if(cap == "b_ex_2"):
                functionText = captures['func_body'][0].text.decode()
                functionText = functionText.splitlines()
                for idx in range(0, len(captures[cap])):
                    pair = []
                    lineNum = captures[cap][idx].start_point.row + 1

                    can_id_name = captures['ids_2'][idx].text.decode()
                    id_attributes = captures[cap][idx].text.decode()
                    id_attributes = id_attributes.split('|')
                    if(len(id_attributes) > 3):
                        continue

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
                    self.msgList.append(pair.copy())
  
                for canIDFlags in self.msgList:
                    id_name = canIDFlags[2]
                    for lines in functionText:
                        if((id_name in lines) and ('=' not in lines)):
                            senderLine = lines.strip()
                            sender = senderLine[0:(len(senderLine)-2)]
                            sender = sender.split('(')[1]
                            args = sender.split(',')
                            if(len(args) != 3):
                                continue

                            try:
                                args[1] = int(args[1].strip())
                            except:
                                rangeStart = lineNum - startingLineNum
                                for lineIDX in range(rangeStart, 0, -1):
                                    textLine = functionText[lineIDX].lower()
                                    if((args[1].strip() in textLine) and ('=' in textLine)):
                                        dlcSize = textLine.split('=')[1].strip().strip(';')
                                        args[1] = int(dlcSize)
                                        break

                            if(args[1] != 0 or (args[2].strip() != 'NULL' and args[2].strip() != 'nullptr')):
                                if(("message ID '" + id_name + '\' (' + canIDFlags[3] + ") set the RTR bit to high but it has a data length associated with it in " + senderLine) in self.resultList):
                                    continue
                                else:
                                    issueStr = "message ID '" + id_name + '\' (' + canIDFlags[3] + ") set the RTR bit to high but it has a data length associated with it in " + senderLine
                                    self.resultList.append(issueStr)

            if(cap == "call_expr"):
                functionText = captures['func_body'][0].text.decode()
                functionText = functionText.splitlines()
                for idx in range(0, len(captures[cap])):
                    pair = []
                    lineNum = captures[cap][idx].start_point.row + 1
                    args = captures['arg_list'][idx].text.decode()[1:-1].split(',')

                    if(len(args) != 3):
                        continue

                    if(('0x40000000' in args[0]) and ('|' in args[0])): 
                        pair.append(args[0].split('|')[0].strip())
                        pair.append(True)

                        try:
                            args[1] = int(args[1].strip())
                        except:
                            rangeStart = lineNum - startingLineNum
                            for lineIDX in range(rangeStart, 0, -1):
                                textLine = functionText[lineIDX].lower()
                                if((args[1].strip() in textLine) and ('=' in textLine)):
                                    dlcSize = textLine.split('=')[1].strip().strip(';')
                                    args[1] = int(dlcSize)
                                    break
                        
                        pair.append(args[1])
                        pair.append(args[2].strip())
                        pair.append(captures['call_expr'][idx].text.decode())
                        self.msgList.append(pair.copy())
                    elif('|' in args[0]):
                        pair.append(args[0].split('|')[0].strip())
                        pair.append(False)
                        pair.append(None)
                        pair.append(args[2].strip())
                        pair.append(captures['call_expr'][idx].text.decode())
                        self.msgList.append(pair.copy())
                    else:
                        pair.append(args[0].strip())
                        pair.append(False) 
                        pair.append(None)   
                        pair.append(args[2].strip())
                        pair.append(captures['call_expr'][idx].text.decode())  
                        self.msgList.append(pair.copy())

                for msg in self.msgList:
                    if((msg[1] == True) and ((msg[2] != 0) or (msg[3] != 'NULL' and msg[3] != 'nullptr'))):
                        if((msg[4] + " set the RTR bit to high but it has a data length associated with it.") in self.resultList):
                            continue
                        else:
                            issueStr = msg[4] + " set the RTR bit to high but it has a data length associated with it."
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

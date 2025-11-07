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
                                if(field.type == "number_literal" and ('0x' in node.text.decode())):
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
                                rtrBitLineNum = functionText.index(textLine) + startingLineNum
                                rtrBit = textLine.split('=')[1][:-1].strip() 
                                args[2] = int(rtrBit)
                                break

                        '''
                        for textLine in functionText:
                            textLine = textLine.lower()
                            if((args[2].strip() in textLine) and ('=' in textLine)):
                                rtrBitLineNum = functionText.index(textLine) + startingLineNum
                                rtrBit = textLine.split('=')[1][:-1].strip() 

                                if()
                                if(rtrBitLineNum < lineNum):
                                    variablePairs.append((rtrBitLineNum, lineNum)) # rtr variable line, send line

                                args[2] = int(rtrBit)
                                break
                        '''
                        

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

                            try:
                                args[2] = int(args[2].strip())
                            except:
                                for textline in functionText:
                                    if((args[2].strip() in textline) and ('=' in textline)):
                                        dlcSize = textline.split('=')[1].strip().strip(';')
                                        args[2] = int(dlcSize)
                                        break #add tuple with line # to make sure if it is reused we can check again, aslo check to make sure line # is above calling func

                            if(args[2] != 0 or (args[3].strip() != 'NULL' and args[3].strip() != 'nullptr')):
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

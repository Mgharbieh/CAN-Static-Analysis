import tree_sitter as TreeSitter
import tree_sitter_cpp as _CPP

CPP_LANGUAGE = TreeSitter.Language(_CPP.language())

class DLCAnalyzer:
    def __init__(self):
        self.msgList = []
        self.resultList = []

    def _reset(self):
        self.msgList = []
        self.resultList = []

    def _checkDLC(self, root):

        dlcQuery0 = r'''
        (function_definition
            body: (compound_statement
                [(expression_statement
                    (assignment_expression
                        (field_expression
                            (identifier) @msg
                            (field_identifier) @field
                        ) @fd_ex
                        (number_literal) @dlc
                    ) @a_ex
                )]
            ) @func_body (#eq? @field "can_dlc")
        )
        
        '''

        dlcQuery1 = r'''
        (function_definition
            body: (compound_statement
                [(expression_statement
                    (call_expression
                        (field_expression
                            (identifier) @obj
                            (field_identifier) @method
                        ) @fd_ex
                        (argument_list) @arg_list
                    ) @call_expr
                )
                (declaration
                    (init_declarator
                        (call_expression
                            (field_expression
                                (identifier) @obj
                                (field_identifier) @method
                            ) @fd_ex
                            (argument_list) @arg_list
                        ) @call_expr
                    )
                )]
            ) @func_body
        )
        (#match? @method "^[Ss]endMsgBuf$")
        '''

        bufQuery = r'''
        (
          (declaration
            (init_declarator
              declarator: (array_declarator
                declarator: (identifier) @buf
                size: (number_literal) @size
              )
            )
          )
        )
        '''
#####################################################################################
        self.buffer_sizes = {}

        q = TreeSitter.Query(CPP_LANGUAGE, bufQuery)
        cur = TreeSitter.QueryCursor(q)
        bufCaps = cur.captures(root)

        for capname in bufCaps:
            if capname == "buf":
                for i, b in enumerate(bufCaps["buf"]):
                    name = b.text.decode().strip()
                    try:
                        sz = int(bufCaps["size"][i].text.decode().strip(), 0)
                    except:
                        continue
                    self.buffer_sizes[name] = sz
      
      ###############################################################################
        QUERY_LIST = [dlcQuery0, dlcQuery1]

        captures = None
        for q in QUERY_LIST:
            query = TreeSitter.Query(CPP_LANGUAGE, q)
            queryCursor = TreeSitter.QueryCursor(query)
            captures = queryCursor.captures(root)
            if len(captures) != 0:
                break

        functionText = None
        startingLineNum = 1

        for cap in captures:

            if cap == 'func_body':
                startingLineNum = captures[cap][0].start_point.row + 1
                functionText = captures[cap][0].text.decode().splitlines()

            if cap == 'a_ex':
                assignList = captures[cap]
                for stmt in assignList:
                    msg_name = None
                    field_name = None
                    dlc_val = None
                    lineNum = stmt.start_point.row + 1

                    for node in stmt.children:
                        if node.type == "field_expression":
                            msg_name = node.children[0].text.decode()
                            field_name = node.children[2].text.decode()
                        elif node.type == "number_literal":
                            try:
                                dlc_val = int(node.text.decode(), 0)
                            except:
                                dlc_val = None

                    if msg_name and field_name and dlc_val is not None:
                        self.msgList.append([msg_name, field_name, dlc_val, lineNum])

                        if dlc_val > 8:
                            issueStr = f"Expected less than actual: {msg_name}.{field_name}={dlc_val} at line {lineNum} (>8)."
                            if issueStr not in self.resultList:
                                self.resultList.append(issueStr)

                        elif dlc_val < 8:
                            issueStr = f"Expected more than actual: {msg_name}.{field_name}={dlc_val} at line {lineNum} (<8)."
                            if issueStr not in self.resultList:
                                self.resultList.append(issueStr)

            if cap == 'call_expr':
                sendList = captures[cap]
                for call in sendList:
                    if call.type == "comment":
                        continue

                    lineNum = call.start_point.row + 1
                    callText = call.text.decode().strip()

                    arg_node = None
                    for child in call.children:
                        if child.type == "argument_list":
                            arg_node = child
                            break
                    if arg_node is None:
                        continue

                    try:
                        flag_raw = arg_node.children[3].text.decode().strip()
                        dlc_raw  = arg_node.children[5].text.decode().strip()
                    except:
                        continue

                    dlc_val = None
                    try:
                        dlc_val = int(dlc_raw, 0)
                    except:
                        if functionText is not None:
                            rangeStart = lineNum - startingLineNum
                            rangeStart = min(rangeStart, len(functionText) - 1)  # fixes line index out of range
                            for lineIDX in range(rangeStart, 0, -1):
                                textLine = functionText[lineIDX].lower()
                                if (dlc_raw.lower() in textLine) and ('=' in textLine):
                                    try:
                                        rhs = textLine.split('=')[1].strip().strip(';')
                                        dlc_val = int(rhs, 0)
                                    except:
                                        pass
                                    break

                    self.msgList.append([callText, dlc_raw, dlc_val, lineNum])

                    #lassic CAN ONLY expects DLC == 8
                    buf_raw = arg_node.children[7].text.decode().strip()
                    expected = self.buffer_sizes.get(buf_raw)

                    if dlc_val is not None:
                        if dlc_val > 8:
                            issueStr = f"Overflow Error: {callText} uses DLC={dlc_val} at line {lineNum} (>8)."
                            if issueStr not in self.resultList:
                                self.resultList.append(issueStr)

                        elif expected is not None and dlc_val < expected:
                          issueStr = f"Underflow Error: {callText} uses DLC={dlc_val} but {buf_raw}[{expected}] at line {lineNum}."
                          if issueStr not in self.resultList:
                              self.resultList.append(issueStr)

        print('#' * 100)
        print()

        if len(self.msgList) == 0:
            print("No DLC usage found.")
            print()
            print('#' * 100)
            return

        if len(self.resultList) == 0:
            print("No issues detected!")
            print()
            print('#' * 100)
            return

        for issue in self.resultList:
            print(issue)
        print()
        print('#' * 100)

    def checkDLC(self, filepath):
        self._reset()

        with(open(filepath, 'r', encoding='utf-8') as inFile):
            sourceCode = inFile.read()

        parser = TreeSitter.Parser(CPP_LANGUAGE)
        tree = parser.parse(bytes(sourceCode, "utf8"))
        root = tree.root_node

        self._checkDLC(root)
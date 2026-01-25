import tree_sitter as TreeSitter
import tree_sitter_cpp as _CPP

CPP_LANGUAGE = TreeSitter.Language(_CPP.language())

class DataBytePackingAnalyzer:
    def __init__(self):
        self.bufSizes = {}
        self.dlcValues = {}
        self.frameBytes = {}

    def _reset(self):
        self.bufSizes = {}
        self.dlcValues = {}
        self.frameBytes = {}

    def _runQuery(self, root, queryText: str):
        q = TreeSitter.Query(CPP_LANGUAGE, queryText)
        cur = TreeSitter.QueryCursor(q)
        return cur.captures(root)

    def _text(self, node):
        return node.text.decode("utf-8", "ignore").strip()

    def _toInt(self, node):
        try:
            return int(self._text(node), 0)
        except:
            return None

    #buffer declarations byte stmp[8];
    def _bufSearch(self, root):
        bufQuery = r"""
        (
          (declaration
            declarator: (init_declarator
              declarator: (array_declarator
                declarator: (identifier) @buf
                size: (number_literal) @size
              )
            )
          )
        )
        """
        caps = self._runQuery(root, bufQuery)
        if "buf" not in caps or "size" not in caps:
            return
        for i, b in enumerate(caps["buf"]):
            name = self._text(b)
            try:
                sz = int(caps["size"][i].text.decode().strip(), 0)
            except:
                continue
            if name:
                self.bufSizes[name] = sz

    #dlc assignments (dlc=8; int dlc=8; canMsg.can_dlc=8;)
    def _dlcSearch(self, root):
        dlcQuery = r"""
        (
          (assignment_expression
            left: (identifier) @name
            right: (number_literal) @val
          )
        )
        (
          (declaration
            declarator: (init_declarator
              declarator: (identifier) @name2
              value: (number_literal) @val2
            )
          )
        )
        (
          (assignment_expression
            left: (field_expression
              argument: (identifier) @obj
              field: (field_identifier) @field
            )
            right: (number_literal) @val3
          )
          (#match? @field "^(can_dlc|length|dlc)$")
        )
        """
        caps = self._runQuery(root, dlcQuery)

        #dlc =8;
        for n, v in zip(caps.get("name", []), caps.get("val", [])):
            key = self._text(n)
            val = self._toInt(v)
            if key and val is not None:
                self.dlcValues.setdefault(key, []).append((n.start_byte, val))

        #int dlc=8;
        for n, v in zip(caps.get("name2", []), caps.get("val2", [])):
            key = self._text(n)
            val = self._toInt(v)
            if key and val is not None:
                self.dlcValues.setdefault(key, []).append((n.start_byte, val))

        #canMsg.can_dlc=8;
        for o, f, v in zip(caps.get("obj", []), caps.get("field", []), caps.get("val3", [])):
            obj = self._text(o)
            field = self._text(f)
            val = self._toInt(v)
            if obj and field and val is not None:
                self.dlcValues.setdefault(f"{obj}.{field}", []).append((o.start_byte, val))

        for k in self.dlcValues:
            self.dlcValues[k].sort(key=lambda x: x[0])

    #checks how many bytes are written into CAN frame.data[]
    def _byteWriteSearch(self, root):
        dataIdxQuery = r"""
        (
          (assignment_expression
            left: (subscript_expression
              argument: (field_expression
                argument: (identifier) @frame
                field: (field_identifier) @field
              )
              (subscript_argument_list (number_literal) @idx)
            )
            right: (_)
          ) @hit
          (#match? @field "^data$")
        )
        """
        caps = self._runQuery(root, dataIdxQuery)
        
        for hit in caps.get("hit", []):
            left = hit.child_by_field_name("left") 
            if left is None or left.type != "subscript_expression":
                continue

            field_expr = left.child_by_field_name("argument") 
            if field_expr is None or field_expr.type != "field_expression":
                continue

            frame_node = field_expr.child_by_field_name("argument")
            field_node = field_expr.child_by_field_name("field")
            if frame_node is None or field_node is None:
                continue

            if self._text(field_node) != "data":
                continue

            frame = self._text(frame_node)

            indexValue = None
            for child in left.children:
                if child.type == "subscript_argument_list":
                    for sub in child.children:
                        if sub.type == "number_literal":
                            indexValue = self._toInt(sub)
                            break
                if indexValue is not None:
                    break

            if frame and indexValue is not None:
                self.frameBytes[frame] = max(self.frameBytes.get(frame, 0), indexValue + 1)
        #checks for memcpy calls to frame.data
        memcpyQuery = r"""
        (
          (call_expression
            function: (identifier) @fn
            arguments: (argument_list) @args
          ) @call
          (#match? @fn "^memcpy$")
        )
        """
        caps2 = self._runQuery(root, memcpyQuery)

        for args_node in caps2.get("args", []):
            args = [c for c in args_node.children if c.type not in ("(", ")", ",")]
            if len(args) < 3:
                continue

            dest = self._text(args[0])
            src = self._text(args[1])

            if not dest.endswith(".data"):
                continue

            frame = dest.split(".")[0].strip()
            size = self._toInt(args[2])
            if size is None and src in self.bufSizes:
                size = self.bufSizes[src]

            if frame and size is not None:
                self.frameBytes[frame] = max(self.frameBytes.get(frame, 0), size)

    #searches for sendMessage/sendMsgBuf/CAN.write CAn calls
    def _sendSearch(self, root):
        sendQuery = r"""
        (
          (call_expression
            function: (field_expression
              argument: (_) @obj
              field: (field_identifier) @method
            )
            arguments: (argument_list) @args
          ) @call
          (#match? @method "(?i)^(sendMsgBuf|sendMessage|write)$")
        )
        """
        caps = self._runQuery(root, sendQuery)
        return list(zip(caps.get("call", []), caps.get("args", [])))

    #finds latest dlc value 
    def _latestBefore(self, key, call_pos):
        items = self.dlcValues.get(key)
        if not items:
            return None
        latest = None
        for pos, val in items:
            if pos <= call_pos:
                latest = val
            else:
                break
        return latest

    #compares dlc to bytes sent
    def _compare(self, label, dlc, bytes_sent, assumed):
        suffix = " , Assumed DLC=8" if assumed else ""
        if bytes_sent is None:
            return f"{label} Has no bytes sent.{suffix}"

        if dlc == bytes_sent:
            return f"{label} has no errors, bytes packed match declared DLC.{suffix}"
        if dlc < bytes_sent:
            return f"{label} Overflow error, DLC={dlc} < BYTES={bytes_sent}{suffix}"
        return f"{label} Underflow error, DLC={dlc} > BYTES={bytes_sent}{suffix}"

    #analyzes each CAN send call
    def _analyzeCall(self, call_node, args_node):
        funcNode = call_node.child_by_field_name("function")
        funcTxt = self._text(funcNode).lower() if funcNode else ""

        args = [c for c in args_node.children if c.type not in ("(", ")", ",")]
        #sendMessage(&canMsg)
        if "sendmessage" in funcTxt and len(args) >= 1:
            label = self._text(args[0]).lstrip("&").strip()
            frame = label
            dlc = (self._latestBefore(f"{frame}.can_dlc", call_node.start_byte) or self._latestBefore(f"{frame}.length", call_node.start_byte)or self._latestBefore(f"{frame}.dlc", call_node.start_byte))
            assumed = False
            if dlc is None:
                dlc = 8
                assumed = True

            return self._compare(label, dlc, self.frameBytes.get(frame), assumed)

        #CAN.write(frame)
        if "write" in funcTxt and len(args) == 1:
            frame = self._text(args[0]).lstrip("&").strip()

            dlc = (self._latestBefore(f"{frame}.length", call_node.start_byte) or self._latestBefore(f"{frame}.can_dlc", call_node.start_byte) or self._latestBefore(f"{frame}.dlc", call_node.start_byte))
            assumed = False
            if dlc is None:
                dlc = 8
                assumed = True

            return self._compare(frame, dlc, self.frameBytes.get(frame), assumed)

        #sendMsgBuf(dlc, buf)
        if len(args) >= 2:
            if "write" in funcTxt and len(args) >= 4:
                dlc_node, buf_node = args[2], args[3]
            else:
                dlc_node, buf_node = args[-2], args[-1]

            buf = self._text(buf_node)
            bytes_sent = self.bufSizes.get(buf)

            dlc = self._toInt(dlc_node)
            if dlc is None:
                dlc = self._latestBefore(self._text(dlc_node), call_node.start_byte)

            assumed = False
            if dlc is None:
                dlc = 8
                assumed = True

            return self._compare(buf, dlc, bytes_sent, assumed)

        return None

    def checkDataPack(self, root):
        self._reset()
        self._bufSearch(root)
        self._dlcSearch(root)
        self._byteWriteSearch(root)

        print("#" * 100, "\n")

        for call_node, args_node in self._sendSearch(root):
            msg = self._analyzeCall(call_node, args_node)
            if msg:
                print(msg)

        print()
        print("#" * 100)

        self._reset()

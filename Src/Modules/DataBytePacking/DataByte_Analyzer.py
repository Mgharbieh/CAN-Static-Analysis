import os
from tree_sitter import Parser
from tree_sitter_languages import get_language

CPP = get_language("cpp")


class DataBytePackingAnalyzer:
    def __init__(self):
        self._parser = Parser()
        self._parser.set_language(CPP)
        self._src = b""

    def _parse(self, path: str):
        with open(path, "rb") as f:
            self._src = f.read()
        tree = self._parser.parse(self._src)
        return tree.root_node

    def _txt(self, node) -> str:
        return self._src[node.start_byte:node.end_byte].decode("utf-8")

    def _to_int_text(self, s: str):
        try:
            return int(s.strip(), 0)
        except Exception:
            return None

    def _to_int_node(self, node):
        if node is None:
            return None
        return self._to_int_text(self._txt(node))

    def _run_query(self, root, src: str):
        q = CPP.query(src)
        caps = q.captures(root)
        out = {}
        for n, name in caps:
            out.setdefault(name, []).append(n)
        return out

    #Queries
    #extracts buffer name with array declaration and its size ex. data [8]
    BUF_DECL = r"""
    (
      (declaration
        declarator: (init_declarator
          declarator: (array_declarator
            declarator: (identifier) @buf
            size: (number_literal) @n
          )
        )
      )
    )
    """

    DLC_ASSIGN = r"""
    ;checks for simple dlc assingments ex. dlc = 8
    (
      (assignment_expression
        left: (identifier) @name
        right: (number_literal) @val
      )
    )

    ;checks for DLC declared and initialized statements ex.  int dlc = 8
    (
      (declaration
        declarator: (init_declarator
          declarator: (identifier) @name2
          value: (number_literal) @val2
        )
      )
    )

    ;checks for DLC value is assigned to a field inside a struct or object ex. obj.can_dlc = 8  / obj.length = 8 / obj.dlc = 8
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

    #captures CAN send/write function calls
    CAN_CALLS = r"""
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

    #finds assignments like frame.data[0] = 0xAA; and counts bytes written to frame data
    FRAME_DATA_WRITE = r"""
    (
      (assignment_expression
        left: (subscript_expression
          argument: (field_expression
            argument: (identifier) @frame
            field: (field_identifier) @field
          )
          (subscript_argument_list
            (number_literal) @idx
          )
        )
        right: (_)
      )
      (#match? @field "^(data)$")
    )
    """
    #catches memcpy calls to frame.data ex. memcpy(frame.data, buf, 8);
    MEMCPY_TO_FRAME_DATA = r"""
    (
      (call_expression
        function: (identifier) @fn
        arguments: (argument_list) @args
      ) @call
      (#match? @fn "^memcpy$")
    )
    """

    #collects the declared sizes of buffers in the source file and stores them in a dict (maps each buffer name to its declared length for later DLC comparison)
    def _collect_buf_sizes(self, root):
        caps = self._run_query(root, self.BUF_DECL)
        sizes = {}
        for b, n in zip(caps.get("buf", []), caps.get("n", [])):
            name = self._txt(b).strip()
            val = self._to_int_node(n)
            if name and val is not None:
                sizes[name] = val
        return sizes
    #grabs DLC values assigned in the source file and stores them in a dict (maps each DLC variable/field name to a list of (name, value)
    def _collect_dlc_values(self, root):
        caps = self._run_query(root, self.DLC_ASSIGN)
        m = {}

        for name, val in zip(caps.get("name", []), caps.get("val", [])): #simple assignments
            n = self._txt(name).strip()
            v = self._to_int_node(val)
            if n and v is not None:
                m.setdefault(n, []).append((name.start_byte, v))

        for name, val in zip(caps.get("name2", []), caps.get("val2", [])): #declaration with initialization
            n = self._txt(name).strip()
            v = self._to_int_node(val)
            if n and v is not None:
                m.setdefault(n, []).append((name.start_byte, v))

        for obj, field, val in zip(caps.get("obj", []), caps.get("field", []), caps.get("val3", [])): #field assignments
            o = self._txt(obj).strip()
            f = self._txt(field).strip()
            v = self._to_int_node(val)
            if o and f and v is not None:
                key = f"{o}.{f}"
                m.setdefault(key, []).append((obj.start_byte, v))

        for k in m:
            m[k].sort(key=lambda x: x[0])
        return m

    #takes the most recent value assigned to 'name' before a given source location (in the case of a duplicate assignment, the last one before the call is used)
    def _resolve_before(self, name: str, before_pos: int, value_map: dict):
        if not name or name not in value_map:
            return None
        best = None
        for pos, val in value_map[name]:
            if pos <= before_pos:
                best = val
            else:
                break
        return best

    #extracts argument nodes from an argument_list node, ignoring punctuation
    def _arg_nodes(self, arg_list_node):
        out = []
        for ch in arg_list_node.children:
            if ch.type in ("(", ")", ","):
                continue
            out.append(ch)
        return out

    #counts and stores literal index writes to each CAN frame’s data array to determine how many payload bytes are populated
    def _collect_frame_bytes_sent(self, root, buf_sizes):
        frame_bytes = {}

        #direct assignments to frame.data[i]
        caps = self._run_query(root, self.FRAME_DATA_WRITE)
        for fr, idx in zip(caps.get("frame", []), caps.get("idx", [])):
            frame = self._txt(fr).strip()
            i = self._to_int_node(idx)
            if frame and i is not None:
                frame_bytes[frame] = max(frame_bytes.get(frame, 0), i + 1)

        #memcpy to frame.data
        caps2 = self._run_query(root, self.MEMCPY_TO_FRAME_DATA)
        calls = caps2.get("call", [])
        args_nodes = caps2.get("args", [])

        for call_node, args_node in zip(calls, args_nodes):
            args = self._arg_nodes(args_node)
            if len(args) < 3:
                continue

            dest = args[0]
            src = args[1]
            size = args[2]
            dest_txt = self._txt(dest).strip()
            if not dest_txt.endswith(".data"):
                continue

            frame_name = dest_txt.split(".")[0].strip()
            if not frame_name:
                continue

            sz = self._to_int_node(size)
            if sz is None:
                src_name = self._txt(src).strip()
                if src_name in buf_sizes:
                    sz = buf_sizes[src_name]

            if sz is not None:
                frame_bytes[frame_name] = max(frame_bytes.get(frame_name, 0), sz)
        return frame_bytes

    #analyzes each CAN send/write call to compare DLC and bytes sent, returning the analysis result
    def _analyze_call(self, call_node, args_node, buf_sizes, dlc_values, frame_bytes):
        call_txt = self._txt(call_node).strip()
        line = call_node.start_point[0] + 1
        col = call_node.start_point[1]

        args = self._arg_nodes(args_node)

        fn_node = call_node.child_by_field_name("function")
        fn_text = (self._txt(fn_node) if fn_node else call_txt).lower()

        #unwraps address-of operator from argument if present ex. &canMsg -> canMsg
        def _unwrap_addr(arg_node):
            txt = self._txt(arg_node).strip()
            if txt.startswith("&"):
                return txt[1:].strip()
            return txt

        #grabs the frame name from the first argument of the call
        #ex. CAN.sendMessage(frame)
        if "sendmessage" in fn_text and len(args) >= 1:
            frame_name = _unwrap_addr(args[0])
            dlc = ( self._resolve_before(f"{frame_name}.can_dlc", call_node.start_byte, dlc_values) or self._resolve_before(f"{frame_name}.length", call_node.start_byte, dlc_values) or self._resolve_before(f"{frame_name}.dlc", call_node.start_byte, dlc_values))
            assumed = False
            #if DLC not found, assume 8
            if dlc is None:
                assumed = True
                dlc = 8

            bytes_sent = frame_bytes.get(frame_name)

            
            if dlc == bytes_sent:
                return ("OK", f"{call_txt}  DLC={dlc} matches BYTES={bytes_sent}. No issues found." + (" (Assumed DLC=8)" if assumed else ""))
            if dlc < bytes_sent:
                return ("OVERFLOW",f"{call_txt}  DLC={dlc} < BYTES={bytes_sent}. (Overflow)"+ (" (Assumed DLC=8)" if assumed else ""))
            return ("UNDERFLOW",f"{call_txt} DLC={dlc} > BYTES={bytes_sent}. (Underflow)"+ (" (Assumed DLC=8)" if assumed else ""))

        #write(frame) OR write(frameType, frame)
        if "write" in fn_text and len(args) == 1:
            frame_name = self._txt(args[0]).strip()
            dlc = (self._resolve_before(f"{frame_name}.length", call_node.start_byte, dlc_values) or self._resolve_before(f"{frame_name}.can_dlc", call_node.start_byte, dlc_values) or self._resolve_before(f"{frame_name}.dlc", call_node.start_byte, dlc_values) )

            assumed = False
            if dlc is None:
                assumed = True
                dlc = 8

            bytes_sent = frame_bytes.get(frame_name)

            if dlc == bytes_sent:
                return ("OK",f"{call_txt}  DLC={dlc} matches BYTES={bytes_sent}. No issues found."+ (" (Assumed DLC=8)" if assumed else ""))
            if dlc < bytes_sent:
                return ("OVERFLOW",f"{call_txt} DLC={dlc} < BYTES={bytes_sent}. (Overflow)"+ (" (Assumed DLC=8)" if assumed else ""))
            return ("UNDERFLOW",f"{call_txt} DLC={dlc} > BYTES={bytes_sent}. (Underflow)"+ (" (Assumed DLC=8)" if assumed else ""))

        #write(id, frameType, dlc, buf) OR sendMsgBuf(..., dlc, buf)
        if "write" in fn_text:
            dlc_node = args[2]
            buf_node = args[3]
        else:
            dlc_node = args[-2]
            buf_node = args[-1]

        buf_name = self._txt(buf_node).strip()
        bytes_sent = buf_sizes.get(buf_name)

        dlc = self._to_int_node(dlc_node)
        assumed = False

        if dlc is None:
            dlc_name = self._txt(dlc_node).strip()
            dlc = self._resolve_before(dlc_name, before_pos=call_node.start_byte, value_map=dlc_values)

        if dlc is None:
            assumed = True
            dlc = 8

        if dlc == bytes_sent:
            return ("OK",f"{call_txt} DLC={dlc} matches BYTES={bytes_sent}. No issues found."+ (" (Assumed DLC=8)" if assumed else "") )
        if dlc < bytes_sent:
            return ("OVERFLOW",f"{call_txt}  DLC={dlc} < BYTES={bytes_sent}. (Overflow)"+ (" (Assumed DLC=8)" if assumed else ""))
        return ("UNDERFLOW",f"{call_txt}  DLC={dlc} > BYTES={bytes_sent}. (Underflow)"+ (" (Assumed DLC=8)" if assumed else ""))

    #public method to check DLC issues in a given source file
    def checkDataPack(self, file_input: str):
        root = self._parse(file_input)

        buf_sizes = self._collect_buf_sizes(root)
        dlc_values = self._collect_dlc_values(root)
        frame_bytes = self._collect_frame_bytes_sent(root, buf_sizes)

        caps = self._run_query(root, self.CAN_CALLS)
        calls = list(zip(caps.get("call", []), caps.get("args", [])))

        for call_node, args_node in calls:
            sev, msg = self._analyze_call(call_node, args_node, buf_sizes, dlc_values, frame_bytes)
            print(msg)
        print()





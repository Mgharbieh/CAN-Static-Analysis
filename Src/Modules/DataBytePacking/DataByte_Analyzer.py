import os
from tree_sitter import Parser
from tree_sitter_languages import get_language

CPP = get_language("cpp")


class DataBytePackingAnalyzer:
    def __init__(self):
        self._parser = Parser()
        self._parser.set_language(CPP)
        self._src = b""

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
        q = CPP.query(self.BUF_DECL)
        caps_raw = q.captures(root)

        if isinstance(caps_raw, dict):
            caps = caps_raw
        else:
            caps = {}
            for item in caps_raw:
                if isinstance(item, tuple) and len(item) >= 2:
                    node, name = item[0], item[1]
                    caps.setdefault(name, []).append(node)

        sizes = {}
        for b, n in zip(caps.get("buf", []), caps.get("n", [])):
            name = self._src[b.start_byte:b.end_byte].decode("utf-8", errors="ignore").strip()
            try:
                val_txt = self._src[n.start_byte:n.end_byte].decode("utf-8", errors="ignore").strip()
                val = int(val_txt, 0)
            except Exception:
                val = None

            if name and val is not None:
                sizes[name] = val
        return sizes
#grabs DLC values assigned in the source file and stores them in a dict (maps each DLC variable/field name to a list of (name, value)
    def _collect_dlc_values(self, root):
        q = CPP.query(self.DLC_ASSIGN)
        caps_raw = q.captures(root)

        if isinstance(caps_raw, dict):
            caps = caps_raw
        else:
            caps = {}
            for item in caps_raw:
                if isinstance(item, tuple) and len(item) >= 2:
                    node, name = item[0], item[1]
                    caps.setdefault(name, []).append(node)

        m = {}

        for name, val in zip(caps.get("name", []), caps.get("val", [])): #simple assignments
            n = self._src[name.start_byte:name.end_byte].decode("utf-8", errors="ignore").strip()
            try:
                v_txt = self._src[val.start_byte:val.end_byte].decode("utf-8", errors="ignore").strip()
                v = int(v_txt, 0)
            except Exception:
                v = None
            if n and v is not None:
                m.setdefault(n, []).append((name.start_byte, v))

        for name, val in zip(caps.get("name2", []), caps.get("val2", [])): #declaration with initialization
            n = self._src[name.start_byte:name.end_byte].decode("utf-8", errors="ignore").strip()
            try:
                v_txt = self._src[val.start_byte:val.end_byte].decode("utf-8", errors="ignore").strip()
                v = int(v_txt, 0)
            except Exception:
                v = None
            if n and v is not None:
                m.setdefault(n, []).append((name.start_byte, v))

        for obj, field, val in zip(caps.get("obj", []), caps.get("field", []), caps.get("val3", [])):  #field assignments
            o = self._src[obj.start_byte:obj.end_byte].decode("utf-8", errors="ignore").strip()
            f = self._src[field.start_byte:field.end_byte].decode("utf-8", errors="ignore").strip()
            try:
                v_txt = self._src[val.start_byte:val.end_byte].decode("utf-8", errors="ignore").strip()
                v = int(v_txt, 0)
            except Exception:
                v = None
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
        q1 = CPP.query(self.FRAME_DATA_WRITE)
        caps_raw = q1.captures(root)
        if isinstance(caps_raw, dict):
            caps = caps_raw
        else:
            caps = {}
            for item in caps_raw:
                if isinstance(item, tuple) and len(item) >= 2:
                    node, name = item[0], item[1]
                    caps.setdefault(name, []).append(node)

        for fr, idx in zip(caps.get("frame", []), caps.get("idx", [])):
            frame = self._src[fr.start_byte:fr.end_byte].decode("utf-8", errors="ignore").strip()
            try:
                i_txt = self._src[idx.start_byte:idx.end_byte].decode("utf-8", errors="ignore").strip()
                i = int(i_txt, 0)
            except Exception:
                i = None

            if frame and i is not None:
                frame_bytes[frame] = max(frame_bytes.get(frame, 0), i + 1)
        #memcpy calls to frame.data
        q2 = CPP.query(self.MEMCPY_TO_FRAME_DATA)
        caps2_raw = q2.captures(root)
        if isinstance(caps2_raw, dict):
            caps2 = caps2_raw
        else:
            caps2 = {}
            for item in caps2_raw:
                if isinstance(item, tuple) and len(item) >= 2:
                    node, name = item[0], item[1]
                    caps2.setdefault(name, []).append(node)

        calls = caps2.get("call", [])
        args_nodes = caps2.get("args", [])

        for call_node, args_node in zip(calls, args_nodes):
            args = self._arg_nodes(args_node)
            if len(args) < 3:
                continue

            dest = args[0]
            src = args[1]
            size = args[2]

            dest_txt = self._src[dest.start_byte:dest.end_byte].decode("utf-8", errors="ignore").strip()
            if not dest_txt.endswith(".data"):
                continue

            frame_name = dest_txt.split(".")[0].strip()
            if not frame_name:
                continue

            try:
                sz_txt = self._src[size.start_byte:size.end_byte].decode("utf-8", errors="ignore").strip()
                sz = int(sz_txt, 0)
            except Exception:
                sz = None

            if sz is None:
                src_name = self._src[src.start_byte:src.end_byte].decode("utf-8", errors="ignore").strip()
                if src_name in buf_sizes:
                    sz = buf_sizes[src_name]

            if sz is not None:
                frame_bytes[frame_name] = max(frame_bytes.get(frame_name, 0), sz)

        return frame_bytes
#analyzes each CAN send/write call to compare DLC and bytes sent, returning the analysis result
    def _analyze_call(self, call_node, args_node, buf_sizes, dlc_values, frame_bytes):
        call_txt = self._src[call_node.start_byte:call_node.end_byte].decode("utf-8", errors="ignore").strip()

        args = self._arg_nodes(args_node)

        fn_node = call_node.child_by_field_name("function")
        fn_text = (
            self._src[fn_node.start_byte:fn_node.end_byte].decode("utf-8", errors="ignore").strip()
            if fn_node else call_txt
        ).lower()
#unwraps address-of operator from argument if present ex. &canMsg -> canMsg
        def _unwrap_addr_text(arg_node):
            txt = self._src[arg_node.start_byte:arg_node.end_byte].decode("utf-8", errors="ignore").strip()
            return txt[1:].strip() if txt.startswith("&") else txt
#grabs the frame name from the first argument of the call
        #ex. CAN.sendMessage(frame)
        if "sendmessage" in fn_text and len(args) >= 1:
            frame_name = _unwrap_addr_text(args[0])
            dlc = (self._resolve_before(f"{frame_name}.can_dlc", call_node.start_byte, dlc_values)or self._resolve_before(f"{frame_name}.length", call_node.start_byte, dlc_values) or self._resolve_before(f"{frame_name}.dlc", call_node.start_byte, dlc_values) )
            assumed = False
            if dlc is None:
                assumed = True
                dlc = 8

            bytes_sent = frame_bytes.get(frame_name)

            if dlc == bytes_sent:
                return ("OK", f"{call_txt}  DLC={dlc} matches BYTES={bytes_sent}. No issues found." + (" (Assumed DLC=8)" if assumed else ""))
            if dlc < bytes_sent:
                return ("OVERFLOW", f"{call_txt}  DLC={dlc} < BYTES={bytes_sent}. (Overflow)" + (" (Assumed DLC=8)" if assumed else ""))
            return ("UNDERFLOW", f"{call_txt} DLC={dlc} > BYTES={bytes_sent}. (Underflow)" + (" (Assumed DLC=8)" if assumed else ""))
 #write(frame) OR write(frameType, frame)
        if "write" in fn_text and len(args) == 1:
            frame_name = self._src[args[0].start_byte:args[0].end_byte].decode("utf-8", errors="ignore").strip()
            dlc = (
                self._resolve_before(f"{frame_name}.length", call_node.start_byte, dlc_values)
                or self._resolve_before(f"{frame_name}.can_dlc", call_node.start_byte, dlc_values)
                or self._resolve_before(f"{frame_name}.dlc", call_node.start_byte, dlc_values)
            )

            assumed = False
            if dlc is None:
                assumed = True
                dlc = 8

            bytes_sent = frame_bytes.get(frame_name)

            if dlc == bytes_sent:
                return ("OK", f"{call_txt}  DLC={dlc} matches BYTES={bytes_sent}. No issues found." + (" (Assumed DLC=8)" if assumed else ""))
            if dlc < bytes_sent:
                return ("OVERFLOW", f"{call_txt} DLC={dlc} < BYTES={bytes_sent}. (Overflow)" + (" (Assumed DLC=8)" if assumed else ""))
            return ("UNDERFLOW", f"{call_txt} DLC={dlc} > BYTES={bytes_sent}. (Underflow)" + (" (Assumed DLC=8)" if assumed else ""))
  #write(id, frameType, dlc, buf) OR sendMsgBuf(..., dlc, buf)
        if "write" in fn_text:
            dlc_node = args[2]
            buf_node = args[3]
        else:
            dlc_node = args[-2]
            buf_node = args[-1]

        buf_name = self._src[buf_node.start_byte:buf_node.end_byte].decode("utf-8", errors="ignore").strip()
        bytes_sent = buf_sizes.get(buf_name)

        dlc = None
        try:
            dlc_txt = self._src[dlc_node.start_byte:dlc_node.end_byte].decode("utf-8", errors="ignore").strip()
            dlc = int(dlc_txt, 0)
        except Exception:
            dlc = None

        assumed = False
        if dlc is None:
            dlc_name = self._src[dlc_node.start_byte:dlc_node.end_byte].decode("utf-8", errors="ignore").strip()
            dlc = self._resolve_before(dlc_name, before_pos=call_node.start_byte, value_map=dlc_values)

        if dlc is None:
            assumed = True
            dlc = 8

        if dlc == bytes_sent:
            return ("OK", f"{call_txt} DLC={dlc} matches BYTES={bytes_sent}. No issues found." + (" (Assumed DLC=8)" if assumed else ""))
        if dlc < bytes_sent:
            return ("OVERFLOW", f"{call_txt}  DLC={dlc} < BYTES={bytes_sent}. (Overflow)" + (" (Assumed DLC=8)" if assumed else ""))
        return ("UNDERFLOW", f"{call_txt}  DLC={dlc} > BYTES={bytes_sent}. (Underflow)" + (" (Assumed DLC=8)" if assumed else ""))
    #public method to check DLC issues in a given source file
    def checkDataPack(self, file_input: str):
        with open(file_input, "rb") as f:
            self._src = f.read()
        root = self._parser.parse(self._src).root_node

        buf_sizes = self._collect_buf_sizes(root)
        dlc_values = self._collect_dlc_values(root)
        frame_bytes = self._collect_frame_bytes_sent(root, buf_sizes)

        q = CPP.query(self.CAN_CALLS)
        caps_raw = q.captures(root)

        if isinstance(caps_raw, dict):
            caps = caps_raw
        else:
            caps = {}
            for item in caps_raw:
                if isinstance(item, tuple) and len(item) >= 2:
                    node, name = item[0], item[1]
                    caps.setdefault(name, []).append(node)

        calls = list(zip(caps.get("call", []), caps.get("args", [])))

        for call_node, args_node in calls:
            _, msg = self._analyze_call(call_node, args_node, buf_sizes, dlc_values, frame_bytes)
            print(msg)
        print()

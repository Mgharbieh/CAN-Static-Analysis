import os
from tree_sitter import Parser
from tree_sitter_languages import get_language

CPP_LANGUAGE = get_language("cpp")


class DataLengthAnalyzer:
    def __init__(self):
        self._parser = Parser()
        self._parser.set_language(CPP_LANGUAGE)
        self._source_bytes = b""
        self.issues = []

    def _reset(self):
        self._source_bytes = b""
        self.issues.clear()

    dlc_query = r"""
    ; Detect CAN.write(ID, frameType, dlcVar, data) where dlcVar is declared in the same function
    (
      (function_definition
        body: (compound_statement
          (_)*
          (declaration
            declarator: (init_declarator
              declarator: (identifier) @dlc_name
              value: (number_literal) @dlc_val
            )
          )
          (_)*
          (expression_statement
            (call_expression
              function: (field_expression
                (identifier) @obj
                field: (field_identifier) @method
              )
              arguments: (argument_list
                (_) @id1
                ","
                (_) @frame_type1
                ","
                (identifier) @dlc_use
                ","
                (_)
              )
            ) @call
          )
          (_)*
        )
      )
      (#match? @obj "^(CAN|Can|can)$")
      (#match? @method "(?i)write")
      (#match? @dlc_name "^(dlc|length)$")
      (#eq? @dlc_name @dlc_use)
    )

    ; Detect CANx.sendMsgBuf/sendMessage(..., dlcVar, data) where dlcVar is declared in the same function
    (
      (function_definition
        body: (compound_statement
          (_)*
          (declaration
            declarator: (init_declarator
              declarator: (identifier) @dlc_name2
              value: (number_literal) @dlc_val2
            )
          )
          (_)*
          (expression_statement
            (call_expression
              function: (field_expression
                (identifier) @obj2
                field: (field_identifier) @method2
              )
              arguments: (argument_list
                (number_literal) @id2
                ","
                (_)*
                (identifier) @dlc_use2
                ","
                (_)
              )
            ) @call2
          )
          (_)*
        )
      )
      (#match? @obj2 "[cC][aA][nN](\\d*)")
      (#match? @method2 "(?i)(sendmsgbuf|sendmessage)")
      (#match? @dlc_name2 "^(dlc|length)$")
      (#eq? @dlc_name2 @dlc_use2)
    )

    ; Detect declaration-assignment: byte x = CANx.sendMsgBuf(..., <dlc_literal>, data)
    (
      (declaration
        declarator: (init_declarator
          value: (call_expression
            function: (field_expression
              (identifier) @obj3
              field: (field_identifier) @method3
            )
            arguments: (argument_list
              (number_literal) @id3
              ","
              (_) @ext3
              ","
              (number_literal) @dlc_lit3
              ","
              (_) @data3
            )
          ) @call3
        )
      )
      (#match? @obj3 "[cC][aA][nN](\\d*)")
      (#match? @method3 "(?i)(sendmsgbuf|sendmessage)")
    )

    ; Detect direct call: CANx.sendMsgBuf(..., <dlc_literal>, data)
    (
      (expression_statement
        (call_expression
          function: (field_expression
            (identifier) @obj4
            field: (field_identifier) @method4
          )
          arguments: (argument_list
            (number_literal) @id4
            ","
            (_) @ext4
            ","
            (number_literal) @dlc_lit4
            ","
            (_) @data4
          )
        ) @call4
      )
      (#match? @obj4 "[cC][aA][nN](\\d*)")
      (#match? @method4 "(?i)(sendmsgbuf|sendmessage)")
    )
    """

    CANFRAME_ID_ASSIGN = r"""
    ; Detect can_frame can_id assignments (e.g., canMsg.can_id = 0x123)
    (assignment_expression
      left: (field_expression (identifier) @msg field: (field_identifier) @field)
      right: (number_literal) @idval
    )
    (#match? @field "^(can_id)$")
    """

    CANFRAME_DLC_ASSIGN = r"""
    ; Detect can_frame can_dlc assignments (e.g., canMsg.can_dlc = 8)
    (assignment_expression
      left: (field_expression (identifier) @msg field: (field_identifier) @field)
      right: (number_literal) @dlcval
    )
    (#match? @field "^(can_dlc)$")
    """

    MCP_SENDMESSAGE_CALL = r"""
    ; Detect MCP2515-style sendMessage(&canMsg) calls (arduino-mcp2515 library pattern)
    (call_expression
      function: (field_expression (identifier) @sender field: (field_identifier) @method)
      arguments: (argument_list (_) @arg)
    ) @call
    (#match? @method "(?i)(sendmessage)$")
    """

    def _infer_expected_dlc(self, *, is_sendmsgbuf, id_node=None, frame_type_node=None):
        if not is_sendmsgbuf and frame_type_node is not None:
            ft = self._source_bytes[frame_type_node.start_byte:frame_type_node.end_byte].decode(
                "utf-8", errors="ignore"
            ).upper()
            if "EXTENDED" in ft:
                return 64
            if "STANDARD" in ft:
                return 8
            return 8

        if id_node is not None:
            try:
                txt = self._source_bytes[id_node.start_byte:id_node.end_byte].decode("utf-8", errors="ignore").strip()
                msg_id = int(txt, 0)
                return 8 if msg_id <= 0x7FF else 64
            except Exception:
                return 8

        return 8

    @staticmethod
    def _clean_msg_ref(arg_text: str) -> str:
        t = arg_text.strip().replace("(", "").replace(")", "").strip()
        while t.startswith("&") or t.startswith("*"):
            t = t[1:].strip()
        out = []
        for ch in t:
            if ch.isalnum() or ch == "_":
                out.append(ch)
            else:
                break
        return "".join(out)

    def _emit_issue(self, call_node, dlc_val: int, expected: int):
        line = call_node.start_point[0] + 1
        col = call_node.start_point[1]
        call_text = self._source_bytes[call_node.start_byte:call_node.end_byte].decode("utf-8", errors="ignore").strip()

        if dlc_val > expected:
            self.issues.append(
                f"{call_text} at L{line}:C{col}: DLC {dlc_val} > expected {expected}. "
                f"(DLC exceeds maximum payload length)"
            )
        elif dlc_val < expected:
            self.issues.append(
                f"{call_text} at L{line}:C{col}: DLC {dlc_val} < expected {expected}. "
                f"(DLC below required payload length)"
            )
        else:
            self.issues.append(f"{call_text} at L{line}:C{col}: DLC {dlc_val} == expected {expected}. (OK)")

    def _try_int_node(self, node):
        try:
            txt = self._source_bytes[node.start_byte:node.end_byte].decode("utf-8", errors="ignore").strip()
            v = int(txt, 0)
            return None if v == 0 else v
        except Exception:
            return None

    def _check_canframe_sendmessage(self, root):
        q1 = CPP_LANGUAGE.query(self.CANFRAME_ID_ASSIGN)
        caps1_raw = q1.captures(root)
        if isinstance(caps1_raw, dict):
            id_caps = caps1_raw
        else:
            id_caps = {}
            for item in caps1_raw:
                if isinstance(item, tuple) and len(item) >= 2:
                    node, name = item[0], item[1]
                    id_caps.setdefault(name, []).append(node)

        q2 = CPP_LANGUAGE.query(self.CANFRAME_DLC_ASSIGN)
        caps2_raw = q2.captures(root)
        if isinstance(caps2_raw, dict):
            dlc_caps = caps2_raw
        else:
            dlc_caps = {}
            for item in caps2_raw:
                if isinstance(item, tuple) and len(item) >= 2:
                    node, name = item[0], item[1]
                    dlc_caps.setdefault(name, []).append(node)

        q3 = CPP_LANGUAGE.query(self.MCP_SENDMESSAGE_CALL)
        caps3_raw = q3.captures(root)
        if isinstance(caps3_raw, dict):
            call_caps = caps3_raw
        else:
            call_caps = {}
            for item in caps3_raw:
                if isinstance(item, tuple) and len(item) >= 2:
                    node, name = item[0], item[1]
                    call_caps.setdefault(name, []).append(node)

        msg_to_id = {
            self._source_bytes[m.start_byte:m.end_byte].decode("utf-8", errors="ignore").strip(): idn
            for m, idn in zip(id_caps.get("msg", []), id_caps.get("idval", []))
        }
        msg_to_dlc = {
            self._source_bytes[m.start_byte:m.end_byte].decode("utf-8", errors="ignore").strip(): dn
            for m, dn in zip(dlc_caps.get("msg", []), dlc_caps.get("dlcval", []))
        }

        seen = set()
        for call_node, arg_node in zip(call_caps.get("call", []), call_caps.get("arg", [])):
            key = (call_node.start_byte, call_node.end_byte)
            if key in seen:
                continue
            seen.add(key)

            arg_text = self._source_bytes[arg_node.start_byte:arg_node.end_byte].decode("utf-8", errors="ignore")
            msg_name = self._clean_msg_ref(arg_text)
            if not msg_name:
                continue

            id_node = msg_to_id.get(msg_name)
            dlc_node = msg_to_dlc.get(msg_name)
            if id_node is None or dlc_node is None:
                continue

            dlc_val = self._try_int_node(dlc_node)
            if dlc_val is None:
                continue

            expected = self._infer_expected_dlc(is_sendmsgbuf=True, id_node=id_node, frame_type_node=None)
            self._emit_issue(call_node, dlc_val, expected)

    def _check_dlc_pairs(self, root):
        q = CPP_LANGUAGE.query(self.dlc_query)
        caps_raw = q.captures(root)
        if isinstance(caps_raw, dict):
            caps = caps_raw
        else:
            caps = {}
            for item in caps_raw:
                if isinstance(item, tuple) and len(item) >= 2:
                    node, name = item[0], item[1]
                    caps.setdefault(name, []).append(node)

        n1 = min(len(caps.get("dlc_val", [])), len(caps.get("call", [])), len(caps.get("frame_type1", [])))
        for i in range(n1):
            dlc_val = self._try_int_node(caps["dlc_val"][i])
            if dlc_val is None:
                continue
            expected = self._infer_expected_dlc(is_sendmsgbuf=False, frame_type_node=caps["frame_type1"][i])
            self._emit_issue(caps["call"][i], dlc_val, expected)

        n2 = min(len(caps.get("dlc_val2", [])), len(caps.get("call2", [])), len(caps.get("id2", [])))
        for i in range(n2):
            dlc_val = self._try_int_node(caps["dlc_val2"][i])
            if dlc_val is None:
                continue
            expected = self._infer_expected_dlc(is_sendmsgbuf=True, id_node=caps["id2"][i])
            self._emit_issue(caps["call2"][i], dlc_val, expected)

        seen_calls = set()

        n3 = min(len(caps.get("dlc_lit3", [])), len(caps.get("call3", [])), len(caps.get("id3", [])))
        for i in range(n3):
            call_node = caps["call3"][i]
            key = (call_node.start_byte, call_node.end_byte)
            if key in seen_calls:
                continue
            seen_calls.add(key)

            dlc_val = self._try_int_node(caps["dlc_lit3"][i])
            if dlc_val is None:
                continue
            expected = self._infer_expected_dlc(is_sendmsgbuf=True, id_node=caps["id3"][i])
            self._emit_issue(call_node, dlc_val, expected)

        n4 = min(len(caps.get("dlc_lit4", [])), len(caps.get("call4", [])), len(caps.get("id4", [])))
        for i in range(n4):
            call_node = caps["call4"][i]
            key = (call_node.start_byte, call_node.end_byte)
            if key in seen_calls:
                continue
            seen_calls.add(key)

            dlc_val = self._try_int_node(caps["dlc_lit4"][i])
            if dlc_val is None:
                continue
            expected = self._infer_expected_dlc(is_sendmsgbuf=True, id_node=caps["id4"][i])
            self._emit_issue(call_node, dlc_val, expected)

        self._check_canframe_sendmessage(root)

    def checkDlc(self, file_input: str):
        if not os.path.isfile(file_input):
            raise FileNotFoundError(f"File not found: {file_input}")

        with open(file_input, "rb") as f:
            src = f.read()
        self._source_bytes = src
        root = self._parser.parse(src).root_node

        self._check_dlc_pairs(root)

        if self.issues:
            for msg in self.issues:
                print(msg)
        else:
            print("No DLC issues detected.")
        self._reset()

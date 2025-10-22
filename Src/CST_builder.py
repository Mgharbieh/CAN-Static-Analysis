import tree_sitter as TreeSitter
import tree_sitter_cpp as _CPP

FOLDER = "//100.83.44.15/shared/Michael/UMich/Research/Static_Analysis_Research/Src/Modules/MaskFilter/Test_Cases/test_arduino-CAN/"
CPP_LANGUAGE = TreeSitter.Language(_CPP.language())
parser = TreeSitter.Parser(CPP_LANGUAGE)


strList = []
def visit_node(node, level=0):
   
    indent = "—" * level
    if node.type != "translation_unit" and node.type != "comment":
        strList.append(f"|{indent}Node:{node.type} Text: {node.text.decode()}\n")
    else:
       strList.append(f"|{indent}Node:{node.type}\n")
    for child in node.children:
        visit_node(child, level + 1)



sourceCode = '''
void loop() {
  // try to parse packet
  int packetSize = CAN.parsePacket();

  if (packetSize || CAN.packetId() != -1) {
    // received a packet
    Serial.print("Received ");

    if (CAN.packetExtended()) {
      Serial.print("extended ");
    }

    if (CAN.packetRtr()) {
      // Remote transmission request, packet contains no data
      Serial.print("RTR ");
    }

    Serial.print("packet with id 0x");
    Serial.print(CAN.packetId(), HEX);

    if (CAN.packetRtr()) {
      Serial.print(" and requested length ");
      Serial.println(CAN.packetDlc());
    } else {
      Serial.print(" and length ");
      Serial.println(packetSize);

      // only print packet data for non-RTR packets
      while (CAN.available()) {
        Serial.print((char)CAN.read());
      }
      Serial.println();
    }

    Serial.println();
  }
}
'''

tree = parser.parse(bytes(sourceCode, "utf8"))
RootCursor = tree.root_node
visit_node(RootCursor)
with(open(FOLDER + "tree.txt", 'w', encoding='utf-8') as inFile):
    #inFile.write(nameStr)
    inFile.write('\n\n')
    for line in strList:
        inFile.write(line)

print(f"done with file")
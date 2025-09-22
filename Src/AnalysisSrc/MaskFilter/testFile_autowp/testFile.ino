#include <SPI.h>
#include <mcp2515.h>

struct can_frame canMsg;
MCP2515 mcp2515(10);


void setup() {
  Serial.begin(115200);
  
  mcp2515.reset();
  mcp2515.setBitrate(CAN_125KBPS);

  mcp2515.setConfigMode();
  mcp2515.setFilterMask(MCP2515::MASK0, false, 0x7FF);
  mcp2515.setFilter(MCP2515::RXF0, false, 0x640);
  mcp2515.setFilter(MCP2515::RXF1, false, 0x641);

  mcp2515.setFilterMask(MCP2515::MASK1, false, 0x7FF);
  mcp2515.setFilter(MCP2515::RXF2, false, 0x080);
  mcp2515.setFilter(MCP2515::RXF3, false, 0x081);
  mcp2515.setFilter(MCP2515::RXF4, false, 0x082);
  mcp2515.setFilter(MCP2515::RXF5, false, 0x083);
  mcp2515.setNormalMode();
  
  Serial.println("------- CAN Read ----------");
  Serial.println("ID  DLC   DATA");
}

void loop() {
  if (mcp2515.readMessage(&canMsg) == MCP2515::ERROR_OK) 
  {
    switch(canMsg.can_id)
    {
    case (0x640):
        break;
    case (0x082):
        break;
    case (0x083):
        break;
    case (0x084):
        break;
    default:
        break;
    }
    
    if(canMsg.can_id == 0x081)
    {
        continue;
    }

    Serial.print(canMsg.can_id, HEX); // print ID
    Serial.print(" "); 
    Serial.print(canMsg.can_dlc, HEX); // print DLC
    Serial.print(" ");
    
    for (int i = 0; i<canMsg.can_dlc; i++)  {  // print the data
      Serial.print(canMsg.data[i],HEX);
      Serial.print(" ");
    }

    Serial.println();      
  }
}
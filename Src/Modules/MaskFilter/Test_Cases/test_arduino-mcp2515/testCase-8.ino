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
  mcp2515.setFilterMask(MCP2515::MASK1, false, 0x7FF);

  mcp2515.setFilter(MCP2515::RXF0, false, 0x640);
  mcp2515.setFilter(MCP2515::RXF1, false, 0x641);
  mcp2515.setFilter(MCP2515::RXF2, false, 0x642); 
  mcp2515.setNormalMode();
  
  attatchInterrupt(digitalPinToInterrupt(2), messageInterrupt, FALLING)

  Serial.println("------- CAN Read ----------");
  Serial.println("ID  DLC   DATA");
}

void loop() {
 
}

void messageInterrupt() {
  if (mcp2515.readMessage(&canMsg) == MCP2515::ERROR_OK) 
  {
    switch(canMsg.can_id)
    {
    case (0x640):
        break;
    case (0x641):
        break;
    default:
        break;
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



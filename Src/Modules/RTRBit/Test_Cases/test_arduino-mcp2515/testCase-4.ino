#include <SPI.h>
#include <mcp2515.h>

struct can_frame canMsg1;
struct can_frame canMsg2;
MCP2515 mcp2515(10);


void setup() {
    
  canMsg1.can_id  = 0x0F6 | CAN_RTR_FLAG;

  canMsg2.can_id  = 0x036 | CAN_RTR_FLAG;
  canMsg2.can_dlc = 0;

  
  while (!Serial);
  Serial.begin(115200);
  
  mcp2515.reset();
  mcp2515.setBitrate(CAN_125KBPS);
  mcp2515.setNormalMode();
  
  Serial.println("Example: Write to CAN");
}

void loop() {
  mcp2515.sendMessage(&canMsg1);
  mcp2515.sendMessage(&canMsg2);

  Serial.println("Messages sent");
  
  delay(100);
}
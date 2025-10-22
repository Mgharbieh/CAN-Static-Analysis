#include <mcp_can.h>
#include <SPI.h>

long unsigned int rxId;
unsigned char len = 0;
unsigned char rxBuf[8];
char msgString[128];                        // Array to store serial string

#define CAN0_INT 2                              // Set INT to pin 2
MCP_CAN CAN0(10);                               // Set CS to pin 10


void setup()
{
  Serial.begin(115200);
  
  // Initialize MCP2515 running at 16MHz with a baudrate of 500kb/s and the masks and filters disabled.
  if(CAN0.begin(MCP_ANY, CAN_500KBPS, MCP_16MHZ) == CAN_OK)
    Serial.println("MCP2515 Initialized Successfully!");
  else
    Serial.println("Error Initializing MCP2515...");
  
  CAN0.init_Mask(0,0,0x7FF);                // Init first mask...
  CAN0.init_Mask(1,0,0x7FF);                // Init first mask...
  CAN0.init_Filt(0,0,0x1E3);  
  CAN0.init_Filt(1,0,0x1E4);
  CAN0.init_Filt(2,0,0x1E5); 
  CAN0.init_Filt(3,0,0x1E6); 

  CAN0.setMode(MCP_NORMAL);                     // Set operation mode to normal so the MCP2515 sends acks to received data.

  pinMode(CAN0_INT, INPUT);                            // Configuring pin for /INT input
  attachInterrupt(digitalPinToInterrupt(CAN0_INT), callback, LOW); // start interrupt

  Serial.println("MCP2515 Library Receive Example...");
}

void loop()
{

}

void callback()
{
    CAN0.readMsgBuf(&rxId, &len, rxBuf);      // Read data: len = data length, buf = data byte(s)

    switch(rxId)
    {
    case (0x1E3):
        break;
    case (0x1E4):
        break;
    case (0x1E7):
        break;
    default:
        break;
    }

    if(rxId == 0x1E5)
        continue;
    else if(rxId == 0x1E8)
        continue;

    for(byte i = 0; i<len; i++){
        sprintf(msgString, " 0x%.2X", rxBuf[i]);
        Serial.print(msgString);
    }
    Serial.println();
}
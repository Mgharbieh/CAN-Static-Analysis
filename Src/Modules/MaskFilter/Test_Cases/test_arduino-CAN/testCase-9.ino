#include <CAN.h>

void setup() {
  Serial.begin(9600);
  while (!Serial);

  Serial.println("CAN Receiver");

  // start the CAN bus at 500 kbps
  if (!CAN.begin(500E3)) {
    Serial.println("Starting CAN failed!");
    while (1);
  }
}

void loop() {
  // try to parse packet
  int packetSize = CAN.parsePacket();

  if (packetSize || CAN.packetId() != -1) {
    // received a packet
    Serial.print("Received ");

    Serial.print("packet with id 0x");
    Serial.print(CAN.packetId(), HEX);

    switch(CAN.packetId())
    {
    case (0x408):
    {
        break;
    }
    case (0x409):
    {
        break;
    }
    default:
    {
        break;
    }
    }

    if(CAN.packetId() == 0x410)
        continue;
   
    Serial.print(" and length ");
    Serial.println(packetSize);

    // only print packet data for non-RTR packets
    while (CAN.available()) {
    Serial.print((char)CAN.read());
    }
    Serial.println();
    

    Serial.println();
  }
}
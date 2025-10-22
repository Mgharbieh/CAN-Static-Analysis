/* https://github.com/Longan-Labs/Arduino_CAN_BUS_MCP2515/blob/master/examples/ */

#include <SPI.h>
#include <mcp_canbus.h>

/* Please modify SPI_CS_PIN to adapt to your board.

   CANBed V1        - 17
   CANBed M0        - 3
   CAN Bus Shield   - 9
   CANBed 2040      - 9
   CANBed Dual      - 9
   OBD-2G Dev Kit   - 9
   OBD-II GPS Kit   - 9
   Hud Dev Kit      - 9

   Seeed Studio CAN-Bus Breakout Board for XIAO and QT Py - D7
*/

#define SPI_CS_PIN  9 

MCP_CAN CAN(SPI_CS_PIN);                                    // Set CS pin

unsigned char flagRecv = 0;
unsigned char len = 0;
unsigned char buf[8];
char str[20];

void setup()
{
    Serial.begin(115200);
    while(!Serial);
    
    while (CAN_OK != CAN.begin(CAN_500KBPS))    // init can bus : baudrate = 500k
    {
        Serial.println("CAN BUS FAIL!");
        delay(100);
    }
    Serial.println("CAN BUS OK!");

    CAN.init_Mask(0, 0, 0x7FF);
    CAN.init_Filt(0, 0, 0x04);
}

void loop()
{
    if(CAN_MSGAVAIL == CAN.checkReceive())                   // check if get data
    {
        CAN.readMsgBuf(&len, buf);    // read data,  len: data length, buf: data buf

        Serial.println("\r\n------------------------------------------------------------------");
        Serial.print("Get Data From id: ");
        Serial.println(CAN.getCanId());
        for(int i = 0; i<len; i++)    // print the data
        {
            Serial.print("0x");
            Serial.print(buf[i], HEX);
            Serial.print("\t");
        }
        Serial.println();
    }
}

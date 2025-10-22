#include <CAN.h>
#include <SPI.h> // required to resolve #define conflicts

// Define our CAN speed (bitrate).
#define bitrate CAN_BPS_500K

void setup()
{
    Serial.begin(115200);  // Initialize Serial communications with computer to use serial monitor

    //Set CAN speed. Note: Speed is now 500kbit/s so adjust your CAN monitor

    CAN.begin(bitrate);
    delay(4000);  // Delay added just so we can have time to open up Serial Monitor and CAN bus monitor. It can be removed later...

    // Output will be formatted as a CSV file, for capture and analysis
    Serial.println(F("millis(),ID,RTR,EID,Length,Data0,Data1,Data2,Data3,Data4,Data5,Data6,Data7"));
}

void loop()
{
    CAN_Frame message; // Create message object to use CAN message structure

    Serial.print(millis());

    if (CAN.available() == true) // Check to see if a valid message has been received.
    {
        message = CAN.read(); //read message, it will follow the CAN structure of ID,RTR, legnth, data. Allows both Extended or Standard

        switch(message.id)
        {
        case(0x654):
        {
            break;
        }
        case(0x656):
        {
            break;
        }
        case(0x657):
        {
            break;
        }
        }

        if(message.id == 0x659)
            continue;
        else if(message.id = 0x660)
            continue;
    
    }
    Serial.println(); // adds a line
}
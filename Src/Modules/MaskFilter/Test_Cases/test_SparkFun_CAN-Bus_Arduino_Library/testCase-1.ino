#include <Canbus.h>
#include <defaults.h>
#include <global.h>
#include <mcp2515.h>
#include <mcp2515_defs.h>

//********************************Setup Loop*********************************//

void setup() {
  Serial.begin(9600); // For debug use
  Serial.println("CAN Read - Testing receival of CAN Bus message");  
  delay(1000);
  
  if(Canbus.init(CANSPEED_500))  //Initialise MCP2515 CAN controller at the specified speed
    Serial.println("CAN Init ok");
  else
    Serial.println("Can't init CAN");
    
  delay(1000);
}

//********************************Main Loop*********************************//

void loop(){

  tCAN message;
if (mcp2515_check_message()) 
	{
        if (mcp2515_get_message(&message)) 
        {
            //if(message.id == 0x620)  //uncomment when you want to filter
            //{ 
                Serial.print("ID: ");
                Serial.print(message.id,HEX);
                Serial.print(", ");
                Serial.print("Data: ");
                Serial.print(message.header.length,DEC);
                for(int i=0;i<message.header.length;i++) 
                {	
                    Serial.print(message.data[i],HEX);
                    Serial.print(" ");
                }
                Serial.println("");
            //}
        }
    }

}
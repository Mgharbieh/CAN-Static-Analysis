/* CAN communications example

  Topic: Send messages using write() function
  Authors: Pedro Cevallos & Neil McNeight
  Created: 05/07/14
  Updated: 06/14/15

  Example shows how to send messages using CAN
  This example uses Serial Monitor to display received messages.

  As per wiki information:
  "CAN bus is a message-based protocol, designed specifically for automotive
  applications but now also used in other areas such as aerospace, maritime,
  industrial automation and medical equipment."

  For more info http://en.wikipedia.org/wiki/Controller_area_network

 */

#include <CAN.h>
#include <SPI.h> // required to resolve #define conflicts

// Define our CAN speed (bitrate).
#define bitrate CAN_BPS_500K

// data counter just to show a dynamic change in data messages
uint32_t extended_counter = 0;
uint32_t standard_counter = 0;

void setup()
{
  Serial.begin(115200); // Initialize Serial communications with computer to use serial monitor

  //Set CAN speed. Note: Speed is now 500kbit/s so adjust your CAN monitor

  CAN.begin(bitrate);

  delay(4000); // Delay added just so we can have time to open up Serial Monitor and CAN bus monitor. It can be removed later...

  // Output will be formatted as a CSV file, for capture and analysis
  Serial.println(F("millis(),standard_counter,extended_counter"));
}


// Create a function to load and send an extended frame message
void extendedMessage()
{
  CAN_Frame extended_message; // Create message object to use CAN message structure

  extended_message.id = 0x02DACBF1; // Random Extended Message ID
  extended_message.valid = true;
  extended_message.rtr = 1;
  extended_message.extended = CAN_EXTENDED_FRAME;
  extended_message.length = 0; // Data length

  CAN.write(extended_message); // Load message and send
  extended_counter++; // increase count
}


// Create a function to load and send a standard frame message
void standardMessage()
{
  CAN_Frame standard_message; // Create message object to use CAN message structure

  standard_message.id = 0x555; // Random Standard Message ID
  standard_message.valid = true;
  standard_message.rtr = 1;
  standard_message.extended = CAN_STANDARD_FRAME;
  standard_message.length = 0; // Data length


  CAN.write(standard_message); // Load message and send
  standard_counter++; // increase count
}


// Finally arduino loop to execute above functions with a 250ms delay
void loop()
{
  standardMessage();
  delay(250);
  extendedMessage();
  delay(250);
  Serial.print(millis());
  Serial.print(',');
  Serial.print(standard_counter);
  Serial.print(',');
  Serial.println(extended_counter); // adds a line
}
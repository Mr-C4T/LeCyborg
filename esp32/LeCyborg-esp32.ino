#include <BluetoothSerial.h>

BluetoothSerial SerialBT;

const int myoPin = 34; // Use an analog-capable GPIO pin
unsigned long previousMillis = 0;
const long interval = 30; // Sampling interval in milliseconds ( 1ms=1000Hz | 30ms=33Hz )

void setup() {
  Serial.begin(115200);
  SerialBT.begin("🤗 LeCyborg-EMG 🦾");
}

void loop() {
  unsigned long currentMillis = millis();
  if (currentMillis - previousMillis >= interval) {
    previousMillis = currentMillis;

    int emgValue = analogRead(myoPin);
    SerialBT.println(emgValue);
    Serial.println(emgValue);
  }
}

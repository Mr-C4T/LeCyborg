#include <esp_now.h>
#include <WiFi.h>

const int myoPin = 1;

typedef struct struct_message {
  int emgValue;
} struct_message;

struct_message myData;

uint8_t broadcastAddress[] = {0xFF,0xFF,0xFF,0xFF,0xFF,0xFF}; // Broadcast

void setup() {
  Serial.begin(115200);
  pinMode(myoPin, INPUT);

  WiFi.mode(WIFI_STA);
  esp_now_init();

  esp_now_peer_info_t peerInfo = {};
  memcpy(peerInfo.peer_addr, broadcastAddress, 6);
  peerInfo.channel = 0;  
  peerInfo.encrypt = false;

  esp_now_add_peer(&peerInfo);
}

void loop() {
  int emgValue = analogRead(myoPin);

  myData.emgValue = emgValue;
  esp_now_send(broadcastAddress, (uint8_t *) &myData, sizeof(myData));

  Serial.println(emgValue);

  delay(30); // ~33Hz
}

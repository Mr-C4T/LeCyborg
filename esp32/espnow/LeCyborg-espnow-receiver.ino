#include <esp_now.h>
#include <WiFi.h>

typedef struct struct_message {
  int emgValue;
} struct_message;

void onDataRecv(const esp_now_recv_info_t* recv_info, const uint8_t* incomingData, int len) {
  struct_message myData;
  memcpy(&myData, incomingData, sizeof(myData));
  Serial.println(myData.emgValue);
}

void setup() {
  Serial.begin(115200);
  WiFi.mode(WIFI_STA);
  if (esp_now_init() != ESP_OK) {
    Serial.println("Error initializing ESP-NOW");
    return;
  }
  esp_now_register_recv_cb(onDataRecv);
}

void loop() {
  // nothing needed here
}

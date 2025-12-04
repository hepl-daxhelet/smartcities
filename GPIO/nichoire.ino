#include "esp_camera.h"
#include <WiFi.h>
#include <PubSubClient.h>

// Attribution pins capteur + led 
#define PIR_PIN 13
#define LED_PIN 14

// -------- CONFIG WIFI ----------
#define WIFI_SSID       "electroProjectWifi"
#define WIFI_PASSWORD   "B1MesureEnv"

// -------- CONFIG MQTT ----------
#define MQTT_SERVER     "192.168.2.28"   // Adresse du broker MQTT
#define MQTT_PORT       1883
#define MQTT_TOPIC       "test"


// -------- TIMER ---------------
unsigned long captureInterval = 15000; // 15 sec
unsigned long lastCapture = 0;

WiFiClient wifiClient;
PubSubClient mqtt(wifiClient);


// -------- CONFIG CAMERA (AI Thinker) --------
#define PWDN_GPIO_NUM     -1
#define RESET_GPIO_NUM    15
#define XCLK_GPIO_NUM     27
#define SIOD_GPIO_NUM     25
#define SIOC_GPIO_NUM     23
#define Y9_GPIO_NUM       19
#define Y8_GPIO_NUM       36
#define Y7_GPIO_NUM       18
#define Y6_GPIO_NUM       39
#define Y5_GPIO_NUM       5
#define Y4_GPIO_NUM       34
#define Y3_GPIO_NUM       35
#define Y2_GPIO_NUM       32
#define VSYNC_GPIO_NUM    22
#define HREF_GPIO_NUM     26
#define PCLK_GPIO_NUM     21


// -----------------------------------------------------
// Initialisation de la caméra
// -----------------------------------------------------
bool initCamera() {
  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer   = LEDC_TIMER_0;
  config.pin_d0       = Y2_GPIO_NUM;
  config.pin_d1       = Y3_GPIO_NUM;
  config.pin_d2       = Y4_GPIO_NUM;
  config.pin_d3       = Y5_GPIO_NUM;
  config.pin_d4       = Y6_GPIO_NUM;
  config.pin_d5       = Y7_GPIO_NUM;
  config.pin_d6       = Y8_GPIO_NUM;
  config.pin_d7       = Y9_GPIO_NUM;
  config.pin_xclk     = XCLK_GPIO_NUM;
  config.pin_pclk     = PCLK_GPIO_NUM;
  config.pin_vsync    = VSYNC_GPIO_NUM;
  config.pin_href     = HREF_GPIO_NUM;
  config.pin_sscb_sda = SIOD_GPIO_NUM;
  config.pin_sscb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn     = PWDN_GPIO_NUM;
  config.pin_reset    = RESET_GPIO_NUM;

  config.xclk_freq_hz = 20000000;
  config.pixel_format = PIXFORMAT_JPEG;

  config.frame_size   = FRAMESIZE_SVGA; // 800x600
  config.jpeg_quality = 12;
  config.fb_count     = 1;

  if (esp_camera_init(&config) != ESP_OK) {
    Serial.println("Erreur Init Caméra !");
    return false;
  }
  Serial.println("Caméra OK");
  return true;
}


// -----------------------------------------------------
// Connexion MQTT (reconnexion automatique)
// -----------------------------------------------------
void mqttReconnect() {
  while (!mqtt.connected()) {
    Serial.print("Connexion MQTT...");
    if (mqtt.connect("esp32cam")) {
      Serial.println(" CONNECTÉ");
    } else {
      Serial.print("Erreur : ");
      Serial.println(mqtt.state());
      delay(2000);
    }
  }
}


// -----------------------------------------------------
// Envoi de la photo sur MQTT en plusieurs morceaux
// -----------------------------------------------------
bool sendImageMQTT(uint8_t *buf, size_t len) {

  if (!mqtt.connected()) return false;

  const int chunkSize = 2000;

  // Envoyer la taille de l'image
  mqtt.publish("test/start", String(len).c_str());

  for (size_t i = 0; i < len; i += chunkSize) {
    size_t sendSize = min(chunkSize, (int)(len - i));

    Serial.print("➜ Envoi chunk taille = ");
    Serial.println(sendSize);

    if (!mqtt.publish("test/data", buf + i, sendSize)) {
        Serial.println("❌ Chunk FAIL (pub refused)");
    } else {
        Serial.println("✔ Chunk OK");
    }

    delay(5);
  }

  mqtt.publish("test/end", "1");

  Serial.println("Image envoyée via MQTT !");
  return true;
}




// -----------------------------------------------------
// SETUP
// -----------------------------------------------------
void setup() {
  Serial.begin(115200);
  
  // Config pins
  pinMode(PIR_PIN, INPUT);
  pinMode(LED_PIN, OUTPUT);

  // WiFi
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  Serial.print("Connexion WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println(" CONNECTÉ !");

  // MQTT
  mqtt.setServer(MQTT_SERVER, MQTT_PORT);

  // Caméra
  initCamera();

  lastCapture = millis();
}


// -----------------------------------------------------
// LOOP
// -----------------------------------------------------
void loop() {
  //if (millis() - lastCapture >= captureInterval) {
  if(digitalRead(PIR_PIN) && millis() - lastCapture >= captureInterval) {
    digitalWrite(LED_PIN, HIGH);
    lastCapture = millis();   // <<< IMPORTANT
    Serial.println("→ Capture image…");

    camera_fb_t *fb = esp_camera_fb_get();
    if (!fb) {
      Serial.println("Erreur capture !");
      return;
    }

    Serial.println("📸 Photo capturée !");
    Serial.print("📏 Taille JPEG : ");
    Serial.print(fb->len);
    Serial.println(" octets");

    // Connexion MQTT après la photo
    if (!mqtt.connected()) mqttReconnect();
    if (!mqtt.connected()) {
      Serial.println("MQTT non dispo.");
      esp_camera_fb_return(fb);
      return;
    }

    sendImageMQTT(fb->buf, fb->len);
    Serial.println("Image envoyée via MQTT !");

    esp_camera_fb_return(fb);
  }

  mqtt.loop();
}
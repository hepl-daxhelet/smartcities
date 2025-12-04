#include "esp_camera.h"
#include <WiFi.h>
#include <PubSubClient.h>

// -------- CONFIG WIFI ----------
#define WIFI_SSID       "electroProjectWifi"
#define WIFI_PASSWORD   "B1MesureEnv"

// -------- CONFIG MQTT ----------
#define MQTT_SERVER     "192.168.2.28"
#define MQTT_PORT       1883

WiFiClient wifiClient;
PubSubClient mqtt(wifiClient);

// -------- Bouton de réveil ----------
#define WAKE_BUTTON_PIN 13  // Bouton entre GPIO12 et GND

// -------- Mémorisation du temps de la dernière photo --------
RTC_DATA_ATTR unsigned long lastCaptureTime = 0;  // Conservé même pendant deep sleep



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
// INITIALISATION CAMÉRA
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

  config.frame_size   = FRAMESIZE_SVGA;
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
// MQTT reconnect
// -----------------------------------------------------
void mqttReconnect() {
  while (!mqtt.connected()) {
    Serial.print("Connexion MQTT...");
    if (mqtt.connect("esp32cam")) {
      Serial.println(" CONNECTÉ");
    } else {
      Serial.print("Erreur : ");
      Serial.println(mqtt.state());
      delay(1000);
    }
  }
}



// -----------------------------------------------------
// ENVOI DE l’IMAGE EN CHUNKS
// -----------------------------------------------------
bool sendImageMQTT(uint8_t *buf, size_t len) {
  if (!mqtt.connected()) return false;

  const int chunkSize = 2000;

  mqtt.publish("test/start", String(len).c_str());

  for (size_t i = 0; i < len; i += chunkSize) {
    size_t sendSize = min(chunkSize, (int)(len - i));
    mqtt.publish("test/data", buf + i, sendSize);
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
  delay(500);

  esp_sleep_wakeup_cause_t cause = esp_sleep_get_wakeup_cause();

  Serial.print("Cause reveil = ");
  Serial.println(cause);

  // ---------- ETAT 1 : réveil par TIMER → activer bouton ----------
  if (cause == ESP_SLEEP_WAKEUP_TIMER) {
    Serial.println("⏱ 15s écoulées → bouton réactivé");

    // On Active le bouton
    pinMode(WAKE_BUTTON_PIN, INPUT_PULLUP);
    esp_sleep_enable_ext0_wakeup((gpio_num_t)WAKE_BUTTON_PIN, 1);

    Serial.println("💤 Deep sleep en attente du bouton...");
    esp_deep_sleep_start();
  }


  // ---------- ETAT 2 : réveil par BOUTON ----------
  if (cause == ESP_SLEEP_WAKEUP_EXT0) {
    Serial.println("🔘 Réveil par le bouton → capture autorisée");
  }

  // ---------- ETAT 3 : premier boot ----------
  if (cause != ESP_SLEEP_WAKEUP_EXT0 && cause != ESP_SLEEP_WAKEUP_TIMER) {
    Serial.println("⚡ Premier boot → bouton désactivé 15s");

    // bouton désactivé → on ne met pas ext0
    esp_sleep_enable_timer_wakeup(15 * 1000000ULL);
    esp_deep_sleep_start();
  }


  // ========== SI ON ARRIVE ICI → CAPTURE AUTORISÉE ==========
  Serial.println("📸 Capture image…");

  if (!initCamera()) Serial.println("Erreur init cam !");

  // ------- Connexion WiFi -------
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  while (WiFi.status() != WL_CONNECTED) {
    Serial.print(".");
    delay(300);
  }
  Serial.println(" CONNECTÉ !");

  mqtt.setServer(MQTT_SERVER, MQTT_PORT);
  mqttReconnect();

  // ------- Capture -------
  camera_fb_t *fb = esp_camera_fb_get();
  if (fb) {
    sendImageMQTT(fb->buf, fb->len);
    esp_camera_fb_return(fb);
  }

  // Après capture → on BLOQUE le bouton 15s
  Serial.println("🔒 Bouton désactivé pendant 15s…");

  // Bouton désactivé → PAS DE EXT0
  esp_sleep_enable_timer_wakeup(15 * 1000000ULL);

  Serial.println("💤 Deep sleep 15s...");
  esp_deep_sleep_start();





  // ------- DEEP SLEEP -------
  Serial.println("💤 Mise en Deep Sleep…");

  pinMode(WAKE_BUTTON_PIN, INPUT_PULLUP);
  esp_sleep_enable_ext0_wakeup((gpio_num_t)WAKE_BUTTON_PIN, 1);

  esp_deep_sleep_start();
}




// -----------------------------------------------------
// LOOP INUTILISÉ EN DEEP SLEEP
// -----------------------------------------------------
void loop() {
  Serial.println("boucle principale");
  delay(1000);
}

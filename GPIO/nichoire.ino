#include "esp_camera.h"
#include <WiFi.h>
#include <PubSubClient.h>
#include <WiFiManager.h>

// -------- CONFIG MQTT ----------
#define MQTT_SERVER     "pietann.local"
#define MQTT_PORT       1883

WiFiClient wifiClient;
PubSubClient mqtt(wifiClient);

// -------- Bouton réveil --------
#define PIR_PIN 13   // Bouton -> GND

// -------- Camera pins (AI Thinker) --------
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
// INITIALISATION CAMERA
// -----------------------------------------------------
bool initCamera() {
  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer   = LEDC_TIMER_0;

  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;

  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href  = HREF_GPIO_NUM;

  config.pin_sscb_sda = SIOD_GPIO_NUM;
  config.pin_sscb_scl = SIOC_GPIO_NUM;

  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;

  config.xclk_freq_hz = 20000000;
  config.pixel_format = PIXFORMAT_JPEG;

  config.frame_size   = FRAMESIZE_UXGA;
  config.jpeg_quality = 12;
  config.fb_count     = 1;

  if (esp_camera_init(&config) != ESP_OK) {
    Serial.println("❌ Erreur Init Caméra !");
    return false;
  }
  Serial.println("📸 Caméra OK");
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
      delay(400);
    }
  }
}

// -----------------------------------------------------
// ENVOI DE l’IMAGE EN CHUNKS
// -----------------------------------------------------
bool sendImageMQTT(uint8_t *buf, size_t len) {
  const int chunkSize = 1024;

  // --- START ---
  mqtt.publish("test/start", String(len).c_str());
  mqtt.loop();
  delay(20);

  // --- DATA chunks ---
  for (size_t i = 0; i < len; i += chunkSize) {
    size_t sendSize = min(chunkSize, (int)(len - i));

    // Envoie du chunk
    bool ok = mqtt.publish("test/data", buf + i, sendSize, false);

    if (!ok) {
      Serial.println("⚠️ Chunk perdu - MQTT buffer plein !");
      mqtt.loop();
      delay(30);
      ok = mqtt.publish("test/data", buf + i, sendSize, false);
      if (!ok) Serial.println("❌ Chunk définitivement perdu");
    }

    mqtt.loop();   // Vidage TCP
    delay(20);     // >= 20 ms (important)
  }

  // --- END ---
  mqtt.publish("test/end", "1", false);
  mqtt.loop();
  Serial.println("📤 END envoyé");

  // --- Flush réseau complet ---
  unsigned long t0 = millis();
  while (millis() - t0 < 350) {   // 350ms = sécurité
      mqtt.loop();
      delay(10);
  }

  // --- Déconnexion propre ---
  if (mqtt.connected()) {
    mqtt.disconnect();
    delay(50);
  }

  return true;
}

void sleepWaitingForPIR() {
  Serial.println("⏳ Attente que le PIR repasse à LOW avant deep sleep...");
  uint32_t t0 = millis();

  // On attend max 10 s que le PIR retombe à 0
  while (digitalRead(PIR_PIN) == HIGH && millis() - t0 < 3000) {
    delay(20);
  }

  if (digitalRead(PIR_PIN) == HIGH) {
    Serial.println("⚠ PIR toujours HIGH après 10 s, on arme quand même.");
  } else {
    Serial.println("✅ PIR LOW, armement du réveil sur HIGH.");
  }

  // Réveil quand PIR passe à HIGH
  esp_sleep_enable_ext1_wakeup(1ULL << PIR_PIN, ESP_EXT1_WAKEUP_ANY_HIGH);
  Serial.println("💤 Deep sleep (attente PIR)...");
  esp_deep_sleep_start();
}


// -----------------------------------------------------
// SETUP
// -----------------------------------------------------
void setup() {
  Serial.begin(115200);
  mqtt.setBufferSize(4096);   // ou 2048 si tu veux être plus léger

  delay(150);

  pinMode(PIR_PIN, INPUT);

  esp_sleep_wakeup_cause_t cause = esp_sleep_get_wakeup_cause();
  Serial.print("Cause reveil = ");
  Serial.println(cause);

  // -------------------------------------------------
  // 1️⃣ RÉVEIL PAR TIMER → JUSTE RETOUR EN MODE BOUTON
  // -------------------------------------------------
  if (cause == ESP_SLEEP_WAKEUP_TIMER) {
    Serial.println("⏱ Réveil par TIMER → retour en attente bouton");

    // On ne fait RIEN : pas de WiFi, pas de caméra, pas de MQTT
    sleepWaitingForPIR();
  }

  // -------------------------------------------------
  // 2️⃣ AUTRES CAS → ON GÈRE LE WIFI (premier boot OU bouton)
  // -------------------------------------------------
  WiFiManager wifiManager;

  // Ne JAMAIS supprimer le WiFi déjà configuré
  wifiManager.setBreakAfterConfig(true);
  wifiManager.setEnableConfigPortal(false);
  wifiManager.setConnectRetries(10);
  wifiManager.setConfigPortalTimeout(60);

  // Si PAS de WiFi déjà enregistré -> ouvrir AP
  if (!wifiManager.getWiFiIsSaved()) {
    Serial.println("📡 Aucune config WiFi -> mode portail");
    wifiManager.startConfigPortal("BirdCam_Config", "12345678");
} 
else {
    Serial.println("🔵 WiFi déjà enregistré -> connexion...");
    WiFi.mode(WIFI_STA);
    delay(300);
    WiFi.begin();
}


  // -------------------------------------------------
  // 3️⃣ SI RÉVEIL PAR BOUTON → PRENDRE PHOTO
  // -------------------------------------------------
  if (cause == ESP_SLEEP_WAKEUP_EXT1) {
    Serial.println("🔵 Réveil par bouton → Capture");

    // Petit délai pour laisser le WiFi bien se poser
    delay(200);

    if (!initCamera()) {
      Serial.println("❌ Caméra KO, reboot...");
      delay(2000);
      ESP.restart();
    }

    mqtt.setServer(MQTT_SERVER, MQTT_PORT);
    mqttReconnect();

    camera_fb_t *fb = esp_camera_fb_get();
    if (fb) {
      sendImageMQTT(fb->buf, fb->len);
      esp_camera_fb_return(fb);
    }

    Serial.println("📤 Image envoyée !");

    // ---------- COOLDOWN 15s : bouton désactivé ----------
    uint32_t cooldown_sec = 15;
    Serial.printf("⏳ Cooldown %u sec (bouton OFF)...\n", cooldown_sec);

    // Uniquement le timer peut réveiller
    esp_sleep_enable_timer_wakeup(cooldown_sec * 1000000ULL);

    Serial.println("💤 Deep sleep (cooldown)...");
    esp_deep_sleep_start();
  }

  // -------------------------------------------------
  // 4️⃣ PREMIER DÉMARRAGE / RESET NORMAL (cause != TIMER, != EXT1)
  //     → ON NE PREND PAS DE PHOTO
  //     → ON VA DIRECT EN ATTENTE BOUTON
  // -------------------------------------------------
  Serial.println("🌙 Démarrage normal → attente bouton (pas de capture)");

 sleepWaitingForPIR();
}

void loop() {}

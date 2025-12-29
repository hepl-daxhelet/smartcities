#include "esp_camera.h"
#include <WiFi.h>
#include <PubSubClient.h>
#include <WiFiManager.h>
#include "esp_sleep.h"

// =========================
//      CONFIG GÉNÉRALE
// =========================

// --- Batterie / alimentation ---
#define BAT_HOLD         33
#define BAT_ADC_PIN      38
#define BAT_ADC_MAX      4095.0f
#define BAT_VREF         3.3f

// Pont diviseur (R_TOP = 2.67k, R_BOT = 1.37k)
#define R_TOP            2.67f   // kΩ
#define R_BOT            1.37f   // kΩ
#define BAT_DIVIDER      ((R_TOP + R_BOT) / R_BOT)

// Seuils batterie (LiPo 1S)
#define VBAT_MIN         3.30f   // 0 %
#define VBAT_MAX         4.20f   // 100 %

// --- Timings ---
#define HEARTBEAT_INTERVAL_SEC  (24UL * 60UL * 60UL)   // Heartbeat toutes les 24 h
//#define HEARTBEAT_INTERVAL_SEC  30UL                 // (pour tests rapides)
#define PIR_COOLDOWN_SEC        15UL                  // Cooldown après capture (sec)

// --- MQTT ---
#define MQTT_SERVER     "pietann.local"
#define MQTT_PORT       1883

WiFiClient wifiClient;
PubSubClient mqtt(wifiClient);

// --- GPIO divers ---
#define PIR_PIN         13      // Capteur PIR / bouton réveil
#define LED_PIN         4       // LED indicateur
#define WIFI_RESET_PIN  37      // (si utilisé avec bouton externe)

// --- Camera pins (AI Thinker) ---
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

// =========================
//   INIT CAMERA
// =========================
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

  config.pin_xclk     = XCLK_GPIO_NUM;
  config.pin_pclk     = PCLK_GPIO_NUM;
  config.pin_vsync    = VSYNC_GPIO_NUM;
  config.pin_href     = HREF_GPIO_NUM;
  config.pin_sscb_sda = SIOD_GPIO_NUM;
  config.pin_sscb_scl = SIOC_GPIO_NUM;

  config.pin_pwdn  = PWDN_GPIO_NUM;
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

// =========================
//   MQTT reconnect simple
// =========================
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

// =========================
//   Envoi image en chunks
// =========================
bool sendImageMQTT(uint8_t *buf, size_t len) {
  const int chunkSize = 1024;

  // START
  mqtt.publish("test/start", String(len).c_str());
  mqtt.loop();
  delay(20);

  // Chunks
  for (size_t i = 0; i < len; i += chunkSize) {
    size_t sendSize = min(chunkSize, (int)(len - i));

    bool ok = mqtt.publish("test/data", buf + i, sendSize, false);
    if (!ok) {
      Serial.println("⚠️ Chunk perdu - MQTT buffer plein !");
      mqtt.loop();
      delay(30);
      ok = mqtt.publish("test/data", buf + i, sendSize, false);
      if (!ok) {
        Serial.println("❌ Chunk définitivement perdu");
      }
    }

    mqtt.loop();
    delay(20);
  }

  // END
  mqtt.publish("test/end", "1", false);
  mqtt.loop();
  Serial.println("📤 END envoyé");

  // Flush réseau
  unsigned long t0 = millis();
  while (millis() - t0 < 350) {
    mqtt.loop();
    delay(10);
  }

  if (mqtt.connected()) {
    mqtt.disconnect();
    delay(50);
  }

  return true;
}

// =========================
//   Lecture batterie
// =========================
float readBatteryVoltage() {
  analogReadResolution(12);
  analogSetPinAttenuation(BAT_ADC_PIN, ADC_11db);

  // Jeter première mesure
  (void)analogRead(BAT_ADC_PIN);

  const int N = 30;
  uint32_t sum = 0;
  for (int i = 0; i < N; i++) {
    sum += analogRead(BAT_ADC_PIN);
    delay(2);
  }
  float raw = sum / (float)N;

  float vadc = (raw / BAT_ADC_MAX) * BAT_VREF;
  float vbat = vadc * BAT_DIVIDER;

  Serial.printf("ADC=%.1f | Vadc=%.3f V | Vbat=%.3f V (div=%.3f)\n",
                raw, vadc, vbat, BAT_DIVIDER);
  return vbat;
}

int readBatteryPercent() {
  float v = readBatteryVoltage();

  int percent = (int)((v - VBAT_MIN) * 100.0f / (VBAT_MAX - VBAT_MIN));
  percent = constrain(percent, 0, 100);

  Serial.printf("🔋 Vbat=%.2f V => %d%%\n", v, percent);
  return percent;
}

void sendBatteryMQTT() {
  Serial.println("📡 [BAT] Envoi heartbeat batterie");

  mqtt.setServer(MQTT_SERVER, MQTT_PORT);
  mqttReconnect();

  int battery = readBatteryPercent();

  char payload[8];
  snprintf(payload, sizeof(payload), "%d", battery);

  Serial.print("📤 [BAT] MQTT → birdcam/battery : ");
  Serial.println(payload);

  bool ok = mqtt.publish("birdcam/battery", payload, true);
  mqtt.loop();
  delay(100);

  if (ok) {
    Serial.println("✅ [BAT] Publication OK");
  } else {
    Serial.println("❌ [BAT] Échec publication");
  }

  mqtt.disconnect();
}

// =========================
//   Commandes série
// =========================
void handleSerialCommands() {
  if (!Serial.available()) return;

  String cmd = Serial.readStringUntil('\n');
  cmd.trim();

  if (cmd == "AP") {
    Serial.println("📡 Commande AP → mode configuration");

    WiFi.disconnect(true, false);
    delay(300);

    WiFiManager wifiManager;
    wifiManager.setBreakAfterConfig(true);
    wifiManager.setConfigPortalTimeout(180);
    wifiManager.startConfigPortal("BirdCam_Config", "12345678");

    Serial.println("🔁 Sortie portail → reboot");
    delay(500);
    ESP.restart();
  }

  if (cmd == "RESET WIFI") {
    Serial.println("🔥 Reset WiFi total");
    WiFiManager wifiManager;
    wifiManager.resetSettings();
    delay(500);
    ESP.restart();
  }
}

// =========================
//   Deep sleep PIR + Timer
// =========================
void sleepWaitingForPIR() {
  Serial.println("⏳ Attente que le PIR repasse à LOW avant deep sleep...");
  uint32_t t0 = millis();

  // On laisse au PIR le temps de retomber
  while (digitalRead(PIR_PIN) == HIGH && millis() - t0 < 3000) {
    delay(20);
  }

  if (digitalRead(PIR_PIN) == HIGH) {
    Serial.println("⚠ PIR toujours HIGH, on arme quand même.");
  } else {
    Serial.println("✅ PIR LOW, armement EXT1.");
  }

  // Réveil sur PIR OU sur heartbeat timer
  esp_sleep_enable_ext1_wakeup(1ULL << PIR_PIN, ESP_EXT1_WAKEUP_ANY_HIGH);
  esp_sleep_enable_timer_wakeup((uint64_t)HEARTBEAT_INTERVAL_SEC * 1000000ULL);

  Serial.printf("💤 Deep sleep (PIR + Heartbeat %lu s)...\n", (unsigned long)HEARTBEAT_INTERVAL_SEC);
  esp_deep_sleep_start();
}

// =========================
//   Connexion WiFi (STA ou AP si échec)
// =========================
void connectWiFiOrAP() {
  Serial.println("🔵 Tentative de connexion WiFi (STA)...");
  WiFi.mode(WIFI_STA);
  delay(300);
  WiFi.begin();

  unsigned long wifiT0 = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - wifiT0 < 8000) {
    delay(200);
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.print("✔️ WiFi connecté, IP = ");
    Serial.println(WiFi.localIP());
    return;
  }

  // Si on est ici → impossible de se connecter
  Serial.println("❌ WiFi indisponible → passage en AP config");

  WiFiManager wifiManager;
  wifiManager.setBreakAfterConfig(true);
  wifiManager.startConfigPortal("BirdCam_Config", "12345678");

  Serial.println("🔁 Sortie portail → reboot");
  delay(500);
  ESP.restart();
}

// =========================
//        SETUP
// =========================
void setup() {
  Serial.begin(115200);
  delay(100);

  // Alimentation pont diviseur batterie
  pinMode(BAT_HOLD, OUTPUT);
  digitalWrite(BAT_HOLD, HIGH);

  // GPIO
  pinMode(PIR_PIN, INPUT);
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);
  pinMode(WIFI_RESET_PIN, INPUT);  // si pull-down externe

  // Fenêtre série pour commandes manuelles
  Serial.println("⌨️ Fenêtre série (AP / RESET WIFI) 2 s...");
  uint32_t t0 = millis();
  while (millis() - t0 < 2000) {
    handleSerialCommands();
    delay(10);
  }

  mqtt.setBufferSize(4096);

  // Raison du réveil
  esp_sleep_wakeup_cause_t cause = esp_sleep_get_wakeup_cause();
  Serial.print("Cause réveil = ");
  Serial.println(cause);

  // Connexion WiFi (ou AP si échec)
  connectWiFiOrAP();

  // =========================
  //   CAS 1 : Réveil TIMER → Heartbeat batterie
  // =========================
  if (cause == ESP_SLEEP_WAKEUP_TIMER) {
    Serial.println("⏱ Réveil par TIMER → Heartbeat batterie");
    sendBatteryMQTT();
    Serial.println("🌙 Retour à l'attente PIR + Heartbeat");
    sleepWaitingForPIR();
  }

  // =========================
  //   CAS 2 : Réveil PIR (EXT1) → Capture image
  // =========================
  if (cause == ESP_SLEEP_WAKEUP_EXT1) {
    Serial.println("🔵 Réveil par PIR → Capture");

    // LED ON
    digitalWrite(LED_PIN, HIGH);
    delay(100);

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
    } else {
      Serial.println("❌ Capture échouée");
    }

    // Envoie pourcentage de la batterie
    sendBatteryMQTT();

    // LED OFF
    digitalWrite(LED_PIN, LOW);
    Serial.println("📤 Image envoyée, activation cooldown...");

    // Cooldown : on désactive temporairement le PIR, seul le timer réveillera
    esp_sleep_enable_timer_wakeup((uint64_t)PIR_COOLDOWN_SEC * 1000000ULL);
    Serial.printf("💤 Deep sleep cooldown (%lu s)...\n", (unsigned long)PIR_COOLDOWN_SEC);
    esp_deep_sleep_start();
  }

  // =========================
  //   CAS 3 : Premier démarrage / reset normal
  // =========================
  Serial.println("🌙 Démarrage normal → attente PIR + Heartbeat");
  sleepWaitingForPIR();
}

// =========================
//        LOOP
// =========================
void loop() {
  // En pratique on ne repasse quasiment jamais ici,
  // mais on garde la possibilité de traiter des commandes série.
  handleSerialCommands();
  delay(20);
}

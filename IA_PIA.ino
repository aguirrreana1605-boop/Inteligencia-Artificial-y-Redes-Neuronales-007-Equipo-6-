#include "esp_camera.h"
#include <WiFi.h>
#include <ESP32Servo.h>

// --- CONFIGURACIÓN DEL WI-FI ---
const char* ssid = "IZZI-74A7";       
const char* password = "ENGuHTy2";    

// --- CONFIGURACIÓN DEL SERVO ---
Servo miServo;
const int pinServo = 13; 

// --- DEFINICIÓN DE PINES (Modelo AI-THINKER) ---
#define PWDN_GPIO_NUM     32
#define RESET_GPIO_NUM    -1
#define XCLK_GPIO_NUM      0
#define SIOD_GPIO_NUM     26
#define SIOC_GPIO_NUM     27
#define Y9_GPIO_NUM       35
#define Y8_GPIO_NUM       34
#define Y7_GPIO_NUM       39
#define Y6_GPIO_NUM       36
#define Y5_GPIO_NUM       21
#define Y4_GPIO_NUM       19
#define Y3_GPIO_NUM       18
#define Y2_GPIO_NUM        5
#define VSYNC_GPIO_NUM    25
#define HREF_GPIO_NUM     23
#define PCLK_GPIO_NUM     22

WiFiServer server(80);

// 1. DECLARACIÓN DE LA FUNCIÓN DE LA CÁMARA (Debe ir arriba de setup)
void configurarCamara() {
  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
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
  config.pin_href = HREF_GPIO_NUM;
  config.pin_sscb_sda = SIOD_GPIO_NUM; 
  config.pin_sscb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;
  config.xclk_freq_hz = 20000000;
  config.pixel_format = PIXFORMAT_JPEG;

  if (psramFound()) {
    config.frame_size = FRAMESIZE_QVGA; 
    config.jpeg_quality = 10;
    config.fb_count = 2;
  } else {
    config.frame_size = FRAMESIZE_QVGA;
    config.jpeg_quality = 12;
    config.fb_count = 1;
  }

  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("Error al iniciar la cámara: 0x%x\n", err);
    return;
  }
}

// 2. FUNCIÓN PARA MANEJAR EL STREAM DE VIDEO
void handleMjpeg(WiFiClient client) {
  client.print("HTTP/1.1 200 OK\r\n");
  client.print("Content-Type: multipart/x-mixed-replace; boundary=frame\r\n\r\n");
  
  while (client.connected()) {
    camera_fb_t * fb = esp_camera_fb_get();
    if (!fb) {
      Serial.println("Error al capturar frame");
      break;
    }
    
    client.printf("--frame\r\nContent-Type: image/jpeg\r\nContent-Length: %d\r\n\r\n", fb->len);
    client.write(fb->buf, fb->len);
    client.print("\r\n");
    
    esp_camera_fb_return(fb);
    delay(30); 
  }
}

// 3. SETUP PRINCIPAL
void setup() {
  Serial.begin(115200);
  delay(500); 

  // Reset eléctrico de la cámara para estabilidad
  pinMode(PWDN_GPIO_NUM, OUTPUT);
  digitalWrite(PWDN_GPIO_NUM, HIGH); 
  delay(200);
  digitalWrite(PWDN_GPIO_NUM, LOW);  
  delay(200);

  miServo.attach(pinServo);
  miServo.write(0);

  // Conectar Wi-Fi primero
  Serial.print("Conectando a ");
  Serial.println(ssid);
  WiFi.begin(ssid, password);
  
  int intentos = 0;
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
    intentos++;
    if(intentos > 30) { 
      Serial.println("\nTardó mucho. Reiniciando placa...");
      ESP.restart();
    }
  }
  Serial.println("\nWiFi conectado con éxito.");

  // Ahora que está declarada arriba, setup() sí la reconoce sin errores
  configurarCamara();

  server.begin();

  Serial.print("Cámara lista. Usa la IP: http://");
  Serial.println(WiFi.localIP());
}

// 4. BUCLE INFINITO
void loop() {
  WiFiClient client = server.available();
  if (client) {
    String req = client.readStringUntil('\r');
    client.flush();

    if (req.indexOf("/mjpeg") != -1) {
      handleMjpeg(client);
    } 
    else if (req.indexOf("/abrir") != -1) {
      Serial.println("¡Comando recibido! Abriendo puerta...");
      miServo.write(90);  
      delay(3000);        
      miServo.write(0);   
      
      client.print("HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\nPuerta Abierta");
      client.stop();
    } 
    else {
      client.print("HTTP/1.1 404 Not Found\r\n\r\n");
      client.stop();
    }
  }
}

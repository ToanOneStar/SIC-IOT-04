#include <WiFi.h>
#include <WebServer.h>
#include <ArduinoJson.h>

// Cấu hình WiFi
const char* ssid = "Huy";
const char* password = "0814437549";

// Tạo web server
WebServer server(80);

// Cấu hình chân
const int LED_PIN = 2;        // LED cảnh báo

// Biến trạng thái
int current_distance = 0;
bool is_warning = false;
unsigned long last_update = 0;

void setup() {
  Serial.begin(115200);
  
  // Initialize pins
  pinMode(LED_PIN, OUTPUT);
  
  // Connect to WiFi
  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");
  
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.print(".");
  }
  
  Serial.println();
  Serial.print("WiFi connected! IP: ");
  Serial.println(WiFi.localIP());
  
  // Configure routes
  server.on("/", handleRoot);
  server.on("/update", HTTP_POST, handleUpdate);
  server.on("/status", handleStatus);
  
  // Start server
  server.begin();
  Serial.println("Web server started!");
  
  digitalWrite(LED_PIN, LOW);
}

void loop() {
  server.handleClient();
  
  // Control LED simply
  if (is_warning) {
    digitalWrite(LED_PIN, HIGH);  // LED on when warning
  } else {
    digitalWrite(LED_PIN, LOW);   // LED off when OK
  }
  
  // Check timeout (if no data received > 10s)
  if (millis() - last_update > 4000) {
    is_warning = false;
    current_distance = 0;
  }
}

// Root page
void handleRoot() {
  String html = "<!DOCTYPE html>";
  html += "<html>";
  html += "<head>";
  html += "<title>Eye Distance Monitor</title>";
  html += "<meta charset=\"UTF-8\">";
  html += "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">";
  html += "<style>";
  html += "body { font-family: Arial; margin: 20px; background: #f0f0f0; }";
  html += ".container { max-width: 500px; margin: auto; background: white; padding: 20px; border-radius: 10px; }";
  html += ".status { font-size: 24px; text-align: center; margin: 20px 0; }";
  html += ".warning { color: red; }";
  html += ".ok { color: green; }";
  html += ".distance { font-size: 36px; font-weight: bold; text-align: center; margin: 20px 0; }";
  html += "button { width: 100%; padding: 15px; font-size: 18px; margin: 10px 0; border: none; border-radius: 5px; cursor: pointer; }";
  html += ".btn-success { background: #28a745; color: white; }";
  html += "</style>";
  html += "</head>";
  html += "<body>";
  html += "<div class=\"container\">";
  html += "<h1 style=\"text-align: center;\">👁️ Eye Distance Monitor</h1>";
  html += "<div class=\"distance\" id=\"distance\">-- cm</div>";
  html += "<div class=\"status\" id=\"status\">Waiting for data...</div>";
  html += "<button class=\"btn-success\" onclick=\"location.reload()\">Refresh</button>";
  html += "</div>";
  html += "<script>";
  html += "function updateStatus() {";
  html += "fetch('/status')";
  html += ".then(response => response.json())";
  html += ".then(data => {";
  html += "document.getElementById('distance').textContent = data.distance + ' cm';";
  html += "const statusEl = document.getElementById('status');";
  html += "if (data.warning) {";
  html += "statusEl.textContent = '⚠️ WARNING: Too close to screen!';";
  html += "statusEl.className = 'status warning';";
  html += "} else {";
  html += "statusEl.textContent = '✅ Distance OK';";
  html += "statusEl.className = 'status ok';";
  html += "}";
  html += "});";
  html += "}";
  html += "setInterval(updateStatus, 1000);";
  html += "updateStatus();";
  html += "</script>";
  html += "</body>";
  html += "</html>";
  
  server.send(200, "text/html", html);
}

// Receive data from Python
void handleUpdate() {
  if (server.hasArg("plain")) {
    String json = server.arg("plain");
    
    DynamicJsonDocument doc(1024);
    deserializeJson(doc, json);
    
    DeserializationError error = deserializeJson(doc, json);
    if (error) {
      Serial.print("deserializeJson() failed: ");
      Serial.println(error.f_str());
      server.send(400, "text/plain", "JSON parse error");
      return;
    }

    current_distance = doc["distance"];
    is_warning = doc["warning"];
    last_update = millis();
    
    Serial.printf("Received: %dcm, Warning: %s\n", 
                  current_distance, is_warning ? "YES" : "NO");
    
    server.send(200, "application/json", "{\"status\":\"OK\"}");
  } else {
    server.send(400, "text/plain", "No data received");
  }
}

// Return current status
void handleStatus() {
  String json = "{";
  json += "\"distance\":" + String(current_distance) + ",";
  json += "\"warning\":" + String(is_warning ? "true" : "false");
  json += "}";
  
  server.send(200, "application/json", json);
}
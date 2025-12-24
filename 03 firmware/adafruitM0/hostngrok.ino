#include <SPI.h>
#include <WiFi101.h>

char ssid[] = "testwifi";
char pass[] = "12345678";
int status = WL_IDLE_STATUS;

// --- CONFIGURATION ---
char server[] = "change-me.ngrok.io";  // <--- ENTER YOUR NGROK DOMAIN HERE
char path[]   = "/api/data";           // <--- ENTER YOUR API PATH HERE
int port      = 80;

WiFiClient client;

// 25 kSPS = 1 sample every 40 microseconds
const unsigned long SAMPLE_INTERVAL_US = 40; 
const int SAMPLES_PER_PACKET = 256;

// Buffer for binary data (256 samples * 2 bytes each)
uint8_t packetBuffer[SAMPLES_PER_PACKET * 2]; 

void setup() {
  // 1. Setup Feather Pins
  WiFi.setPins(8,7,4,2);

  // 2. Setup DAC on Pin A0 (Hardcoded Reference)
  analogWriteResolution(10); // Enable 10-bit resolution for DAC
  analogWrite(A0, 512);      // Output approx 1.65V (Half of 3.3V)

  // 3. Setup ADC for High Speed
  // We manipulate the SAMD21 registers to speed up reading
  ADC->CTRLB.reg = ADC_CTRLB_PRESCALER_DIV32 | ADC_CTRLB_RESSEL_10BIT;
  ADC->SAMPCTRL.reg = 0x00; 
  while (ADC->STATUS.bit.SYNCBUSY); 

  // 4. Connect WiFi
  Serial.begin(9600);
  // Optional: Wait for serial only if you want to debug startup
  // while (!Serial); 
  
  if (WiFi.status() == WL_NO_SHIELD) {
    // If no shield, stop here
    while (true);
  }
  
  while (status != WL_CONNECTED) {
    Serial.print("Attempting to connect to SSID: ");
    Serial.println(ssid);
    status = WiFi.begin(ssid, pass);
    delay(500);
  }
  
  Serial.println("Connected to WiFi");
}

void loop() {
  unsigned long previousMicros = micros();

  // --- SAMPLING PHASE ---
  for (int i = 0; i < SAMPLES_PER_PACKET; i++) {
    
    // Precise 40us timing lock
    while (micros() - previousMicros < SAMPLE_INTERVAL_US);
    previousMicros = micros();

    // 1. Read Signal (A1)
    int val_signal = analogRead(A1);
    
    // 2. Read Reference (A2)
    int val_ref = analogRead(A2);

    // 3. Calculate Differential
    // Result is signed (e.g., +200 or -200)
    int16_t differential = val_signal - val_ref;

    // 4. Pack into Binary Buffer (Little Endian)
    // Cast to uint16_t for bitwise math, but preserves binary value
    uint16_t binaryValue = (uint16_t)differential;
    
    packetBuffer[i*2] = binaryValue & 0xFF;         // Low Byte
    packetBuffer[i*2+1] = (binaryValue >> 8) & 0xFF; // High Byte
  }

  // --- TRANSMISSION PHASE ---
  // Send the batch via HTTP POST
  Serial.println("Starting connection to server...");
  if (client.connect(server, port)) {
    Serial.println("Connected to server");
    
    // Make a HTTP request:
    client.print("POST ");
    client.print(path);
    client.println(" HTTP/1.1");
    client.print("Host: ");
    client.println(server);
    client.println("Content-Type: application/octet-stream");
    client.print("Content-Length: ");
    client.println(SAMPLES_PER_PACKET * 2);
    client.println("Connection: close");
    client.println(); // End of headers
    
    // Write binary data
    client.write(packetBuffer, SAMPLES_PER_PACKET * 2);
    
    // Wait slightly to ensure data is sent? 
    // Usually client.stop() will flush, but waiting for response is safer for robustness
    // For speed, strict waiting might be bad, but for debugging let's read response line
    /*
    unsigned long timeout = millis();
    while (client.connected() && millis() - timeout < 1000) {
      if (client.available()) {
        char c = client.read();
        // Serial.print(c); // Print response for debug
      }
    }
    */
    client.stop(); // Disconnect
    Serial.println("Data sent & disconnected");

  } else {
    Serial.println("Connection failed");
  }
}

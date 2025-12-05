#include <SPI.h>
#include <WiFi101.h>
#include <WiFiUdp.h>

char ssid[] = "SSID_Here";
char pass[] = "PW_Here";
int status = WL_IDLE_STATUS;

// --- CONFIGURATION ---
IPAddress remoteIp(192, 168, 1, 9); // <--- target PC IP
unsigned int remotePort = 8888;
WiFiUDP Udp;

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
    status = WiFi.begin(ssid, pass);
    delay(500);
  }
  
  Udp.begin(remotePort);
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
  // Send the batch
  Udp.beginPacket(remoteIp, remotePort);
  Udp.write(packetBuffer, SAMPLES_PER_PACKET * 2);
  Udp.endPacket();
}
// JARVIS LEGO BOT — Diagnostica isolata GPIO1 su Wokwi (FASE 11.1)
// Nessuna dipendenza esterna, nessun file .bin richiesto.

static constexpr uint8_t kTouchPin = 1;
static constexpr unsigned long kPollIntervalMs = 100;

unsigned long last_poll_ms = 0;

void setup() {
  Serial.begin(115200);
  delay(200);
  pinMode(kTouchPin, INPUT);
  Serial.println("=== JARVIS GPIO1 DIAGNOSTIC ===");
  Serial.println("Premi il pulsante verde TOUCH GPIO1 (o tasto T) per verificare HIGH/LOW.");
}

void loop() {
  const unsigned long now = millis();
  if (now - last_poll_ms >= kPollIntervalMs) {
    last_poll_ms = now;
    const int state = digitalRead(kTouchPin);
    Serial.println(state == HIGH ? "GPIO1=HIGH" : "GPIO1=LOW");
  }
}

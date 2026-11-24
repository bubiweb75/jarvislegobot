// =============================================================================
// JARVIS LEGO BOT — FASE 10.6: Integrazione Offline Audio Duplex + Eyes 3.0
// Target: Espressif ESP32-S3-DevKitC-1 N16R8 (16 MB Flash, 8 MB OPI PSRAM)
//
// Hardware:
//   OLED SH1106 (0x3C) : SDA=GPIO41, SCL=GPIO42
//   INMP441 (I2S0 RX)  : WS=GPIO4, SCK=GPIO5, SD=GPIO6, L/R=GND
//   MAX98357A (I2S1 TX): DIN=GPIO7, BCLK=GPIO15, LRC=GPIO16, SD=3V3, VIN=5V
//   Pulsante           : GPIO47 (INPUT_PULLUP, attivo LOW)
// =============================================================================

#ifndef OLED_DRIVER_SH1106
#define OLED_DRIVER_SH1106 1
#endif

#include <Arduino.h>

#include "audio_buffer.h"
#include "audio_capture.h"
#include "audio_playback.h"
#include "button_controller.h"
#include "eye_controller.h"
#include "serial_commands.h"
#include "state_machine.h"

namespace {

jarvis::duplex::AudioBuffer g_buffer;
jarvis::duplex::AudioCapture g_capture;
jarvis::duplex::AudioPlayback g_playback;
jarvis::duplex::EyeController g_eyes;
jarvis::duplex::ButtonController g_button;
jarvis::duplex::StateMachine g_sm;
jarvis::duplex::SerialCommands g_serial;

}  // namespace

void setup() {
  Serial.begin(115200);
  const uint32_t wait_start = millis();
  while (!Serial && (millis() - wait_start) < 1200U) {
  }

  Serial.println();
  Serial.println(F("=== JARVIS FASE 10.6 — Duplex Offline + Eyes 3.0 ==="));

  g_eyes.Begin();
  g_buffer.Allocate();
  g_capture.Begin();
  g_playback.Begin();
  g_button.Begin();

  g_sm.Begin(g_buffer, g_capture, g_playback, g_eyes, g_button);
  g_serial.Begin(g_sm, g_buffer, g_capture, g_playback, g_eyes);

  Serial.println(F("Pronto. Tieni premuto GPIO47 per parlare (max 5s) o invia HELP."));
}

void loop() {
  const uint32_t now_ms = millis();
  g_serial.Poll(now_ms);
  g_sm.Update(now_ms);
}

// =============================================================================
// JARVIS LEGO BOT — FASE 10.5: Prima Voce Italiana (Collaudo Isolato)
// Target: Espressif ESP32-S3-DevKitC-1 N16R8 + OLED SH1106 + MAX98357A
//
// Frase: "Ciao, sono Jarvis! Sono pronto ad aiutarti."
// Trigger: comando seriale SPEAK (115200 baud) o pressione breve GPIO47
// =============================================================================

#ifndef OLED_DRIVER_SH1106
#define OLED_DRIVER_SH1106 1
#endif

#include <Arduino.h>

#include "audio_player.h"
#include "button_controller.h"
#include "eye_controller.h"
#include "serial_command_handler.h"

namespace {

jarvis::voice::AudioPlayer g_audio;
jarvis::voice::EyeController g_eyes;
jarvis::voice::ButtonController g_button;
jarvis::voice::SerialCommandHandler g_serial;

}  // namespace

void setup() {
  Serial.begin(115200);
  const uint32_t wait_start = millis();
  while (!Serial && (millis() - wait_start) < 1200U) {
  }

  Serial.println();
  Serial.println(F("=== JARVIS FASE 10.5 — Collaudo Prima Voce Italiana ==="));

  g_eyes.Begin();
  g_audio.Begin();
  g_button.Begin();
  g_serial.Begin(g_audio, g_eyes);

  Serial.println(F("Pronto. Invia SPEAK o premi brevemente GPIO47. Digita HELP per i comandi."));
}

void loop() {
  const uint32_t now_ms = millis();

  g_serial.Poll();

  if (g_button.PollShortPress(now_ms)) {
    Serial.println(F("BTN:GPIO47_SHORT_PRESS -> SPEAK"));
    g_audio.Start();
  }

  // Blocchetto audio da 16 ms (256 frame @ 16 kHz) compatibile con aggiornamento fluido OLED
  g_audio.Update();
  g_eyes.SetSpeaking(g_audio.IsPlaying(), now_ms);
  g_eyes.Update(now_ms);
}

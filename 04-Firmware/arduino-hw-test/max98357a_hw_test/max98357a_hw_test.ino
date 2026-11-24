// =============================================================================
// JARVIS LEGO BOT — FASE 10.4: Diagnostica audio MAX98357A + Speaker
// Target: Espressif ESP32-S3-DevKitC-1 N16R8 (Arduino-ESP32 3.3.12 / ESP_I2S)
// Collegamenti MAX98357A:
//   LRC  -> GPIO16 | BCLK -> GPIO15 | DIN -> GPIO7
//   GAIN -> N.C.   | SD   -> 3V3    | GND -> GND | VIN -> 3V3 (solo test <=5%)
//   Speaker 4 Ohm / 3 W collegato esclusivamente ai morsetti + e - del MAX98357A
//
// Comandi Serial Monitor (115200 baud):
//   TEST1 -> Riproduce 1 tono 440 Hz (300 ms) al 1% (amp=327/32767)
//   TEST3 -> Riproduce 1 tono 440 Hz (300 ms) al 3% (amp=983/32767)
//   TEST5 -> Riproduce 1 tono 440 Hz (300 ms) al 5% (amp=1638/32767)
//   HELP  -> Mostra i comandi disponibili
// =============================================================================

#include <Arduino.h>
#include <ESP_I2S.h>
#include <ctype.h>
#include <math.h>
#include <stdint.h>
#include <string.h>

namespace {

constexpr int8_t kI2sBclkPin = 15;
constexpr int8_t kI2sLrcPin = 16;
constexpr int8_t kI2sDinPin = 7;

constexpr uint32_t kSampleRateHz = 16000;
constexpr float kToneFreqHz = 440.0f;
constexpr uint32_t kToneDurationMs = 300;
constexpr uint32_t kFadeDurationMs = 20;

constexpr uint8_t kMaxPercent = 5;
constexpr size_t kChunkFrames = 256;
constexpr size_t kSilenceFlushFrames = (kSampleRateHz * 60U) / 1000U;  // 60 ms di zeri post-tono

I2SClass g_i2s;
int16_t g_stereo_buf[kChunkFrames * 2];  // Interleaved [L, R] (4 byte per frame)
bool g_i2s_ready = false;

char g_rx_buf[32];
uint8_t g_rx_len = 0;

int16_t AmplitudeFromPercent(uint8_t pct) {
  const uint8_t clamped = (pct > kMaxPercent) ? kMaxPercent : pct;
  return static_cast<int16_t>((32767UL * clamped) / 100UL);
}

bool PlayTestTone(uint8_t pct) {
  if (!g_i2s_ready) {
    Serial.println(F("ERRORE: I2S TX non inizializzato."));
    return false;
  }

  const uint8_t safe_pct = (pct > kMaxPercent) ? kMaxPercent : pct;
  const int16_t amp = AmplitudeFromPercent(safe_pct);

  const size_t total_frames = (kSampleRateHz * kToneDurationMs) / 1000U;
  const size_t fade_frames = (kSampleRateHz * kFadeDurationMs) / 1000U;
  const float two_pi_f_over_fs = (2.0f * static_cast<float>(M_PI) * kToneFreqHz) /
                                 static_cast<float>(kSampleRateHz);

  size_t frame_idx = 0;
  size_t expected_bytes = 0;
  size_t bytes_written = 0;
  uint32_t partial_writes = 0;
  uint32_t i2s_errors = 0;
  int last_err = 0;

  while (frame_idx < total_frames) {
    const size_t n = ((total_frames - frame_idx) < kChunkFrames)
                         ? (total_frames - frame_idx)
                         : kChunkFrames;

    for (size_t i = 0; i < n; ++i) {
      const size_t idx = frame_idx + i;
      float env = 1.0f;
      if (idx < fade_frames) {
        env = static_cast<float>(idx) / static_cast<float>(fade_frames);
      } else if (idx >= (total_frames - fade_frames)) {
        env = static_cast<float>(total_frames - 1U - idx) / static_cast<float>(fade_frames);
      }

      const float s = sinf(two_pi_f_over_fs * static_cast<float>(idx));
      const int16_t sample = static_cast<int16_t>(lroundf(s * static_cast<float>(amp) * env));

      // Duplicazione identica su slot LEFT e RIGHT (4 byte/frame)
      g_stereo_buf[2U * i] = sample;
      g_stereo_buf[2U * i + 1U] = sample;
    }

    const size_t bytes_to_write = n * 2U * sizeof(int16_t);
    const size_t written = g_i2s.write(reinterpret_cast<const uint8_t*>(g_stereo_buf), bytes_to_write);
    const int err = g_i2s.lastError();

    expected_bytes += bytes_to_write;
    bytes_written += written;
    if (written != bytes_to_write) {
      partial_writes++;
    }
    if (err != 0) {
      i2s_errors++;
      last_err = err;
    }
    frame_idx += n;
  }

  // Flush finale di silenzio (60 ms a zero) per evitare clic
  memset(g_stereo_buf, 0, sizeof(g_stereo_buf));
  size_t sil_idx = 0;
  while (sil_idx < kSilenceFlushFrames) {
    const size_t n = ((kSilenceFlushFrames - sil_idx) < kChunkFrames)
                         ? (kSilenceFlushFrames - sil_idx)
                         : kChunkFrames;
    const size_t bytes_to_write = n * 2U * sizeof(int16_t);
    const size_t written = g_i2s.write(reinterpret_cast<const uint8_t*>(g_stereo_buf), bytes_to_write);
    const int err = g_i2s.lastError();

    expected_bytes += bytes_to_write;
    bytes_written += written;
    if (written != bytes_to_write) {
      partial_writes++;
    }
    if (err != 0) {
      i2s_errors++;
      last_err = err;
    }
    sil_idx += n;
  }

  const size_t total_frames_sent = total_frames + kSilenceFlushFrames;
  const size_t total_stereo_samples = total_frames_sent * 2U;

  Serial.printf(
      "TONE_DONE: level=%u%% amp=%d/32767 | frames=%lu(+%lu sil) | stereo_samples=%lu | bytes=%lu/%lu | partial=%lu | i2s_err=%lu(last=%d)\n",
      static_cast<unsigned>(safe_pct),
      static_cast<int>(amp),
      static_cast<unsigned long>(total_frames),
      static_cast<unsigned long>(kSilenceFlushFrames),
      static_cast<unsigned long>(total_stereo_samples),
      static_cast<unsigned long>(bytes_written),
      static_cast<unsigned long>(expected_bytes),
      static_cast<unsigned long>(partial_writes),
      static_cast<unsigned long>(i2s_errors),
      last_err);

  return (partial_writes == 0 && i2s_errors == 0);
}

void PollSerial() {
  while (Serial.available() > 0) {
    const char ch = static_cast<char>(Serial.read());
    if (ch == '\n' || ch == '\r') {
      if (g_rx_len > 0) {
        g_rx_buf[g_rx_len] = '\0';
        for (uint8_t i = 0; i < g_rx_len; ++i) {
          g_rx_buf[i] = static_cast<char>(toupper(static_cast<unsigned char>(g_rx_buf[i])));
        }
        if (strcmp(g_rx_buf, "TEST1") == 0) {
          Serial.println(F("Avvio TEST1 (440 Hz, 300 ms, 1% PCM)..."));
          PlayTestTone(1);
        } else if (strcmp(g_rx_buf, "TEST3") == 0) {
          Serial.println(F("Avvio TEST3 (440 Hz, 300 ms, 3% PCM)..."));
          PlayTestTone(3);
        } else if (strcmp(g_rx_buf, "TEST5") == 0) {
          Serial.println(F("Avvio TEST5 (440 Hz, 300 ms, 5% PCM)..."));
          PlayTestTone(5);
        } else if (strcmp(g_rx_buf, "HELP") == 0) {
          Serial.println(F("Comandi: TEST1 (1%) | TEST3 (3%) | TEST5 (5%) | HELP"));
        } else {
          Serial.printf("Comando sconosciuto: %s (usa TEST1, TEST3, TEST5, HELP)\n", g_rx_buf);
        }
        g_rx_len = 0;
      }
    } else if (g_rx_len < (sizeof(g_rx_buf) - 1)) {
      g_rx_buf[g_rx_len++] = ch;
    } else {
      g_rx_len = 0;
    }
  }
}

}  // namespace

void setup() {
  Serial.begin(115200);
  const uint32_t wait_start = millis();
  while (!Serial && (millis() - wait_start) < 1200U) {
  }

  Serial.println();
  Serial.println(F("=== JARVIS FASE 10.4 — Diagnostica MAX98357A + Speaker ==="));
  Serial.printf("Pin I2S TX: BCLK=GPIO%d, LRC=GPIO%d, DIN=GPIO%d\n",
                kI2sBclkPin, kI2sLrcPin, kI2sDinPin);

  g_i2s.setPins(kI2sBclkPin, kI2sLrcPin, kI2sDinPin, -1, -1);
  if (!g_i2s.begin(I2S_MODE_STD,
                   kSampleRateHz,
                   I2S_DATA_BIT_WIDTH_16BIT,
                   I2S_SLOT_MODE_STEREO,
                   I2S_STD_SLOT_BOTH)) {
    Serial.printf("ERRORE: I2S TX begin() fallito (lastError=%d)\n", g_i2s.lastError());
    g_i2s_ready = false;
    return;
  }

  g_i2s_ready = true;
  Serial.println(F("I2S TX pronto (STD Philips, 16 kHz, 16-bit signed stereo L=R)."));
  Serial.println(F("Nota: i2s_err=0 indica solo invio DMA valido, non verifica il segnale fisico sui pin."));
  Serial.println(F("Riproduzione iniziale TEST1 (1%)..."));
  PlayTestTone(1);
  Serial.println(F("Comandi disponibili: TEST1 | TEST3 | TEST5 | HELP"));
}

void loop() {
  PollSerial();
  delay(10);
}

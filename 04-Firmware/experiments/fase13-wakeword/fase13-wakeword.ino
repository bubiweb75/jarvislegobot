// =============================================================================
// JARVIS LEGO BOT — FASE 13.2E: IDLE + Silent Speaker + microWakeWord ("Hey Jarvis")
// Hardware: ESP32-S3-DevKitC-1 N16R8 (same pinout as FASE 12.27, no modifications)
// NOTE: Isolated experiment only — DO NOT flash without explicit authorization.
// =============================================================================

#include <Arduino.h>
#include <ESP_I2S.h>
#include <string.h>
#include "wakeword_engine.h"

using namespace jarvis::wakeword;

namespace {

// Existing INMP441 I2S0 RX pinout (unchanged)
constexpr int8_t kMicWsPin = 4;
constexpr int8_t kMicSckPin = 5;
constexpr int8_t kMicSdPin = 6;

// Existing MAX98357A I2S1 TX pinout (unchanged, matched to audio_playback.h)
constexpr int8_t kSpkBclkPin = 15;
constexpr int8_t kSpkLrcPin = 16;
constexpr int8_t kSpkDinPin = 7;

constexpr int8_t kButtonPin = 47;

constexpr uint32_t kSampleRateHz = 16000U;
constexpr size_t kFrame10msSamples = 160U;         // 10 ms @ 16 kHz
constexpr size_t kSilenceChunkFrames = 256U;       // 16 ms stereo chunk
constexpr size_t kSilenceFlushFrames = 960U;       // 60 ms zero flush (no click/pop)
constexpr int kMicShiftBits = 6;                   // Total >> 14 (raw >> 8, minus DC, >> 6)
constexpr int16_t kSatThreshold16 = 32000;
constexpr uint32_t kMaxCommandMs = 8000U;
constexpr uint32_t kPostCycleGuardMs = 1000U;      // Anti-retrigger guard while flushing VAR_HANDLE state

I2SClass g_i2s_mic{I2S_NUM_0};
I2SClass g_i2s_spk{I2S_NUM_1};
MicroWakeWordDetector g_detector;
PreRollRingBuffer g_preroll;
WakeState g_state = WakeState::kBoot;
uint32_t g_state_ms = 0;
uint32_t g_guard_until_ms = 0;
uint32_t g_last_diag_ms = 0;
bool g_triggered_by_button = false;

int16_t g_diag_peak_16 = 0;
uint32_t g_diag_clip_cnt = 0;
uint32_t g_diag_sat_cnt = 0;
int32_t g_last_dc_24 = 0;

int16_t g_frame_buf[kFrame10msSamples] = {};
int32_t g_i2s_raw_buf[kFrame10msSamples] = {};
int16_t g_zero_stereo_buf[kSilenceChunkFrames * 2] = {};

void FlushSpeakerSilence() {
  memset(g_zero_stereo_buf, 0, sizeof(g_zero_stereo_buf));
  size_t remaining = kSilenceFlushFrames;
  while (remaining > 0) {
    const size_t n = (remaining < kSilenceChunkFrames) ? remaining : kSilenceChunkFrames;
    g_i2s_spk.write(reinterpret_cast<const uint8_t*>(g_zero_stereo_buf), n * 2U * sizeof(int16_t));
    remaining -= n;
  }
}

void SetState(WakeState next) {
  if (g_state == next) return;
  g_state = next;
  g_state_ms = millis();
  Serial.printf("[FASE13.2E] State -> %s (heap=%u, psram=%u)\n",
                WakeStateName(next),
                static_cast<unsigned>(ESP.getFreeHeap()),
                static_cast<unsigned>(ESP.getFreePsram()));
}

}  // namespace

void setup() {
  Serial.begin(115200);
  delay(200);
  Serial.println(F("[FASE13.2E] IDLE + Silent Speaker + microWakeWord (Hey Jarvis)"));

  pinMode(kButtonPin, INPUT_PULLUP);

  // Initialize MAX98357A I2S1 TX first and drive clean digital zeros (no hiss/pop)
  g_i2s_spk.setPins(kSpkBclkPin, kSpkLrcPin, kSpkDinPin, -1, -1);
  if (!g_i2s_spk.begin(I2S_MODE_STD, kSampleRateHz, I2S_DATA_BIT_WIDTH_16BIT, I2S_SLOT_MODE_STEREO, I2S_STD_SLOT_BOTH)) {
    Serial.println(F("[WAKE_ERROR] I2S1 TX (MAX98357A) init failed"));
    SetState(WakeState::kError);
    return;
  }
  FlushSpeakerSilence();
  Serial.println(F("[AUDIO] I2S1 TX silent ready (BCLK=GPIO15 LRC=GPIO16 DIN=GPIO7, 16kHz zero-flushed)"));

  if (!g_preroll.AllocatePsram()) {
    Serial.println(F("[WAKE_ERROR] PreRoll PSRAM alloc failed"));
    SetState(WakeState::kError);
    return;
  }

  g_i2s_mic.setPins(kMicSckPin, kMicWsPin, -1, kMicSdPin, -1);
  if (!g_i2s_mic.begin(I2S_MODE_STD, kSampleRateHz, I2S_DATA_BIT_WIDTH_32BIT, I2S_SLOT_MODE_MONO, I2S_STD_SLOT_LEFT)) {
    Serial.println(F("[WAKE_ERROR] I2S0 RX (INMP441) init failed"));
    SetState(WakeState::kError);
    return;
  }

  if (!g_detector.Begin()) {
    Serial.println(F("[WAKE_ERROR] MicroWakeWordDetector init failed"));
    SetState(WakeState::kError);
    return;
  }

  SetState(WakeState::kIdle);
}

void loop() {
  const uint32_t now_ms = millis();

  if (g_state == WakeState::kError) {
    if (now_ms - g_state_ms > 2000U) {
      SetState(WakeState::kRecovery);
      g_detector.Reset();
      g_preroll.Clear();
      FlushSpeakerSilence();
      Serial.println(F("[WAKE_RESET] Recovery complete"));
      SetState(WakeState::kIdle);
    }
    delay(20);
    return;
  }

  // Single I2S0 owner: read 10 ms frame (INMP441 24-bit in 32-bit slot -> DC-removed PCM16)
  const size_t bytes_req = kFrame10msSamples * sizeof(int32_t);
  const size_t bytes_read = g_i2s_mic.readBytes(reinterpret_cast<char*>(g_i2s_raw_buf), bytes_req);
  const size_t n = bytes_read / sizeof(int32_t);
  if (n > 0) {
    int64_t sum24 = 0;
    for (size_t i = 0; i < n; ++i) {
      sum24 += static_cast<int64_t>(g_i2s_raw_buf[i] >> 8);
    }
    const int32_t dc_mean = static_cast<int32_t>(sum24 / static_cast<int64_t>(n));
    g_last_dc_24 = dc_mean;

    for (size_t i = 0; i < n; ++i) {
      const int32_t ac24 = (g_i2s_raw_buf[i] >> 8) - dc_mean;
      int32_t s = ac24 >> kMicShiftBits;
      if (s > 32767) {
        s = 32767;
        g_diag_clip_cnt++;
      } else if (s < -32767) {
        s = -32767;
        g_diag_clip_cnt++;
      }
      const int16_t pcm16 = static_cast<int16_t>(s);
      g_frame_buf[i] = pcm16;
      const int16_t abs_v = (pcm16 < 0) ? static_cast<int16_t>(-pcm16) : pcm16;
      if (abs_v > g_diag_peak_16) g_diag_peak_16 = abs_v;
      if (abs_v >= kSatThreshold16) g_diag_sat_cnt++;
    }
  }

  if (g_state == WakeState::kIdle && n == kFrame10msSamples) {
    const bool in_guard = (static_cast<int32_t>(now_ms - g_guard_until_ms) < 0);
    if (!in_guard) {
      g_preroll.Push(g_frame_buf, n);
    }
    const WakeDetectionResult r = g_detector.ProcessFrame10ms(g_frame_buf, n);
    if (r.ran_inference && (now_ms - g_last_diag_ms >= 2000U)) {
      g_last_diag_ms = now_ms;
      Serial.printf("[WAKE_INFERENCE_MS] %.2f ms | [WAKE_SCORE] raw=%.3f smooth=%.3f rms=%u peak=%d clip=%lu sat=%lu dc=%ld\n",
                    static_cast<double>(r.inference_us) / 1000.0,
                    r.confidence,
                    r.smoothed_confidence,
                    static_cast<unsigned>(r.frame_rms),
                    static_cast<int>(g_diag_peak_16),
                    static_cast<unsigned long>(g_diag_clip_cnt),
                    static_cast<unsigned long>(g_diag_sat_cnt),
                    static_cast<long>(g_last_dc_24));
      g_diag_peak_16 = 0;
      g_diag_clip_cnt = 0;
      g_diag_sat_cnt = 0;
    }
    const bool btn_pressed = (digitalRead(kButtonPin) == LOW);
    if ((!in_guard && r.detected) || btn_pressed) {
      g_triggered_by_button = btn_pressed && !r.detected;
      Serial.printf("[WAKE_DETECTED] src=%s score=%.3f smooth=%.3f preroll=%u\n",
                    r.detected ? "HEY_JARVIS" : "GPIO47",
                    r.confidence,
                    r.smoothed_confidence,
                    static_cast<unsigned>(g_preroll.Available()));
      SetState(WakeState::kWakeDetected);
      SetState(WakeState::kCommandListening);
    }
  } else if (g_state == WakeState::kCommandListening) {
    const bool btn_released = g_triggered_by_button && (digitalRead(kButtonPin) == HIGH);
    const bool wake_sim_done = !g_triggered_by_button && (now_ms - g_state_ms >= 300U);
    if ((now_ms - g_state_ms) >= kMaxCommandMs || btn_released || wake_sim_done) {
      SetState(WakeState::kProcessing);
      SetState(WakeState::kSpeaking);
      FlushSpeakerSilence();
      g_detector.Reset();
      g_preroll.Clear();
      g_guard_until_ms = millis() + kPostCycleGuardMs;
      SetState(WakeState::kIdle);
    }
  }
}

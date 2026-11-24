#pragma once

#include <stddef.h>
#include <stdint.h>

namespace jarvis::duplex {

// Adaptive Voice Activity Detector (no Arduino/ESP dependencies; host-testable).
class VoiceActivityDetector {
 public:
  static constexpr uint16_t kMinNoiseFloorRms = 80U;
  static constexpr uint16_t kMaxNoiseFloorRms = 1500U;
  static constexpr uint16_t kMinSpeechRms = 360U;
  static constexpr uint16_t kMinSilenceRms = 220U;
  static constexpr float kSpeechSnrFactor = 2.4f;
  static constexpr float kSilenceSnrFactor = 1.5f;
  static constexpr uint8_t kSpeechStartChunks = 4U;      // ~64 ms @ 16 ms/chunk
  static constexpr uint32_t kPostWakeHoldoffMs = 300U;   // Ignore wake-word tail/echo without truncating PCM
  static constexpr uint32_t kEndOfSpeechSilenceMs = 1100U;
  static constexpr uint32_t kNoSpeechTimeoutMs = 2500U;

  enum class Decision : uint8_t {
    kContinue = 0,
    kStopEndOfSpeech,
    kStopNoSpeech,
  };

  void ResetNoiseFloor(uint16_t initial_rms = 180U) {
    noise_floor_rms_ = ClampNoise(initial_rms);
  }

  void UpdateAmbientRms(uint16_t chunk_rms) {
    // Slow EMA tracking background noise in IDLE; ignore loud transients.
    if (chunk_rms > noise_floor_rms_ * 3U && chunk_rms > 600U) {
      return;
    }
    const float next = (0.95f * static_cast<float>(noise_floor_rms_)) +
                       (0.05f * static_cast<float>(chunk_rms));
    noise_floor_rms_ = ClampNoise(static_cast<uint16_t>(next));
  }

  void StartSession(uint32_t start_ms) {
    session_start_ms_ = start_ms;
    last_speech_ms_ = start_ms;
    speech_started_ = false;
    consecutive_speech_ = 0;
  }

  Decision ProcessChunk(uint16_t chunk_rms, uint32_t now_ms) {
    const uint16_t speech_thr = SpeechThreshold();
    const uint16_t silence_thr = SilenceThreshold();

    if (!speech_started_) {
      // During initial post-wake holdoff, audio is still recorded into AudioBuffer,
      // but wake-word tail/echo cannot arm speech_started_.
      if ((now_ms - session_start_ms_) < kPostWakeHoldoffMs) {
        consecutive_speech_ = 0;
        return Decision::kContinue;
      }
      if (chunk_rms >= speech_thr) {
        consecutive_speech_++;
        if (consecutive_speech_ >= kSpeechStartChunks) {
          speech_started_ = true;
          last_speech_ms_ = now_ms;
        }
      } else {
        consecutive_speech_ = 0;
        if ((now_ms - session_start_ms_) >= kNoSpeechTimeoutMs) {
          return Decision::kStopNoSpeech;
        }
      }
      return Decision::kContinue;
    }

    if (chunk_rms >= silence_thr) {
      last_speech_ms_ = now_ms;
    } else if ((now_ms - last_speech_ms_) >= kEndOfSpeechSilenceMs) {
      return Decision::kStopEndOfSpeech;
    }
    return Decision::kContinue;
  }

  bool SpeechStarted() const { return speech_started_; }
  uint16_t NoiseFloorRms() const { return noise_floor_rms_; }

  uint16_t SpeechThreshold() const {
    const uint16_t adaptive = static_cast<uint16_t>(static_cast<float>(noise_floor_rms_) * kSpeechSnrFactor);
    return (adaptive > kMinSpeechRms) ? adaptive : kMinSpeechRms;
  }

  uint16_t SilenceThreshold() const {
    const uint16_t adaptive = static_cast<uint16_t>(static_cast<float>(noise_floor_rms_) * kSilenceSnrFactor);
    return (adaptive > kMinSilenceRms) ? adaptive : kMinSilenceRms;
  }

 private:
  static uint16_t ClampNoise(uint16_t v) {
    if (v < kMinNoiseFloorRms) return kMinNoiseFloorRms;
    if (v > kMaxNoiseFloorRms) return kMaxNoiseFloorRms;
    return v;
  }

  uint16_t noise_floor_rms_ = 180U;
  uint32_t session_start_ms_ = 0;
  uint32_t last_speech_ms_ = 0;
  uint8_t consecutive_speech_ = 0;
  bool speech_started_ = false;
};

}  // namespace jarvis::duplex

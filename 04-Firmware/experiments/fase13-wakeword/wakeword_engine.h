#pragma once

#include <stddef.h>
#include <stdint.h>

namespace tflite {
class MicroInterpreter;
class MicroAllocator;
class MicroResourceVariables;
}  // namespace tflite

struct FrontendState;

namespace jarvis::wakeword {

enum class WakeState : uint8_t {
  kBoot = 0,
  kIdle,
  kWakeDetected,
  kCommandListening,
  kProcessing,
  kSpeaking,
  kError,
  kRecovery,
};

const char* WakeStateName(WakeState s);

struct WakeDetectionResult {
  bool ran_inference = false;
  bool detected = false;
  float confidence = 0.0f;
  float smoothed_confidence = 0.0f;
  uint32_t inference_us = 0;
  uint16_t frame_rms = 0;
};

class IWakeWordDetector {
 public:
  virtual ~IWakeWordDetector() = default;
  virtual bool Begin() = 0;
  virtual void Reset() = 0;
  virtual WakeDetectionResult ProcessFrame10ms(const int16_t* pcm16, size_t n_samples) = 0;
  virtual size_t ArenaBytesUsed() const = 0;
  virtual const char* ModelName() const = 0;
};

// Real microWakeWord v2 detector ("Hey Jarvis") backed by TFLite Micro + microfrontend.
class MicroWakeWordDetector final : public IWakeWordDetector {
 public:
  static constexpr size_t kTensorArenaBytes = 32768U;  // >= 22,860 B required by hey_jarvis.json
  static constexpr size_t kFeatureBins = 40U;
  static constexpr size_t kFramesPerInvoke = 3U;       // Input tensor [1, 3, 40]
  static constexpr size_t kSlidingWindowSize = 5U;     // hey_jarvis.json sliding_window_size
  static constexpr float kProbabilityCutoff = 0.97f;   // hey_jarvis.json probability_cutoff

  MicroWakeWordDetector() = default;
  ~MicroWakeWordDetector() override;

  bool Begin() override;
  void Reset() override;
  WakeDetectionResult ProcessFrame10ms(const int16_t* pcm16, size_t n_samples) override;
  size_t ArenaBytesUsed() const override { return arena_used_bytes_; }
  const char* ModelName() const override { return "hey_jarvis_v2_int8"; }

 private:
  uint8_t* tensor_arena_ = nullptr;
  tflite::MicroAllocator* allocator_ = nullptr;
  tflite::MicroResourceVariables* resource_vars_ = nullptr;
  tflite::MicroInterpreter* interpreter_ = nullptr;
  FrontendState* frontend_state_ = nullptr;
  bool frontend_ready_ = false;

  int8_t feature_buf_[kFramesPerInvoke * kFeatureBins] = {};
  size_t feature_frame_idx_ = 0;

  float prob_history_[kSlidingWindowSize] = {};
  size_t prob_idx_ = 0;
  size_t prob_count_ = 0;
  size_t arena_used_bytes_ = 0;
};

// Volatile PSRAM pre-roll ring buffer (500 ms @ 16 kHz = 8,000 samples = 16 KB)
class PreRollRingBuffer {
 public:
  static constexpr size_t kCapacitySamples = 8000U;

  bool AllocatePsram();
  void Clear();
  void Push(const int16_t* samples, size_t count);
  size_t DrainTo(int16_t* dst, size_t max_samples);
  size_t Available() const { return count_; }

 private:
  int16_t* buf_ = nullptr;
  size_t head_ = 0;
  size_t count_ = 0;
};

}  // namespace jarvis::wakeword

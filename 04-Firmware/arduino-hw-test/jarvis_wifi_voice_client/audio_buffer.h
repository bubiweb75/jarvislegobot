#pragma once

#include <stddef.h>
#include <stdint.h>

namespace jarvis::duplex {

class AudioBuffer {
public:
  static constexpr uint32_t kSampleRateHz = 16000U;
  static constexpr size_t kDefaultMaxSeconds = 8U;
  static constexpr size_t kPrimaryCapacitySamples = kSampleRateHz * kDefaultMaxSeconds;  // 128,000 samples (256 KB)
  static constexpr size_t kFallbackCapacitySamples = kSampleRateHz * 1U;                  // 16,000 samples (32 KB)

  bool Allocate();
  bool AllocateWithCapacity(size_t primary_samples, size_t fallback_samples);
  void Release();
  void Clear();

  size_t Append(const int16_t* samples, size_t count);
  bool ReadAt(size_t index, int16_t& out_sample) const;
  const int16_t* Data() const { return data_; }

  bool IsAllocated() const { return data_ != nullptr; }
  bool UsedPsram() const { return used_psram_; }
  size_t CapacitySamples() const { return capacity_samples_; }
  size_t CapacityBytes() const { return capacity_samples_ * sizeof(int16_t); }
  size_t SampleCount() const { return sample_count_; }
  uint32_t DurationMs() const;

private:
  int16_t* data_ = nullptr;
  size_t capacity_samples_ = 0;
  size_t sample_count_ = 0;
  bool used_psram_ = false;
};

}  // namespace jarvis::duplex

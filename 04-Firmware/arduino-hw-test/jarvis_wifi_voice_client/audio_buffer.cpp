#include "audio_buffer.h"

#include <Arduino.h>
#include <esp_heap_caps.h>
#include <stdlib.h>

namespace jarvis::duplex {

bool AudioBuffer::Allocate() {
  return AllocateWithCapacity(kPrimaryCapacitySamples, kFallbackCapacitySamples);
}

bool AudioBuffer::AllocateWithCapacity(size_t primary_samples, size_t fallback_samples) {
  Release();

  if (psramFound() && ESP.getFreePsram() >= (primary_samples * sizeof(int16_t))) {
    data_ = static_cast<int16_t*>(ps_malloc(primary_samples * sizeof(int16_t)));
    if (data_ != nullptr) {
      capacity_samples_ = primary_samples;
      sample_count_ = 0;
      used_psram_ = true;
      Serial.printf("[MEM] AudioBuffer PSRAM alloc=%lu bytes (%lu samples @ %lu Hz)\n",
                    static_cast<unsigned long>(CapacityBytes()),
                    static_cast<unsigned long>(capacity_samples_),
                    static_cast<unsigned long>(kSampleRateHz));
      return true;
    }
  }

  Serial.println(F("[MEM] WARN: PSRAM non disponibile o insufficiente, tentativo buffer ridotto in RAM"));
  data_ = static_cast<int16_t*>(malloc(fallback_samples * sizeof(int16_t)));
  if (data_ != nullptr) {
    capacity_samples_ = fallback_samples;
    sample_count_ = 0;
    used_psram_ = false;
    Serial.printf("[MEM] AudioBuffer RAM fallback alloc=%lu bytes\n",
                  static_cast<unsigned long>(CapacityBytes()));
    return true;
  }

  Serial.println(F("[MEM] ERR: Allocazione AudioBuffer fallita"));
  capacity_samples_ = 0;
  sample_count_ = 0;
  used_psram_ = false;
  return false;
}

void AudioBuffer::Release() {
  if (data_ != nullptr) {
    free(data_);
    data_ = nullptr;
  }
  capacity_samples_ = 0;
  sample_count_ = 0;
  used_psram_ = false;
}

void AudioBuffer::Clear() {
  sample_count_ = 0;
}

size_t AudioBuffer::Append(const int16_t* samples, size_t count) {
  if (data_ == nullptr || samples == nullptr || count == 0 || sample_count_ >= capacity_samples_) {
    return 0;
  }
  const size_t avail = capacity_samples_ - sample_count_;
  const size_t to_copy = (count < avail) ? count : avail;
  for (size_t i = 0; i < to_copy; ++i) {
    data_[sample_count_ + i] = samples[i];
  }
  sample_count_ += to_copy;
  return to_copy;
}

bool AudioBuffer::ReadAt(size_t index, int16_t& out_sample) const {
  if (data_ == nullptr || index >= sample_count_) {
    return false;
  }
  out_sample = data_[index];
  return true;
}

uint32_t AudioBuffer::DurationMs() const {
  return static_cast<uint32_t>((sample_count_ * 1000ULL) / kSampleRateHz);
}

}  // namespace jarvis::duplex

#include "audio_buffer.h"

#include <Arduino.h>
#include <esp_heap_caps.h>
#include <stdlib.h>

namespace jarvis::duplex {

bool AudioBuffer::Allocate() {
  Release();

  if (psramFound() && ESP.getFreePsram() >= (kPrimaryCapacitySamples * sizeof(int16_t))) {
    data_ = static_cast<int16_t*>(ps_malloc(kPrimaryCapacitySamples * sizeof(int16_t)));
    if (data_ != nullptr) {
      capacity_samples_ = kPrimaryCapacitySamples;
      sample_count_ = 0;
      used_psram_ = true;
      Serial.printf("[MEM] AudioBuffer PSRAM alloc=%lu bytes (%u s @ %lu Hz)\n",
                    static_cast<unsigned long>(CapacityBytes()),
                    static_cast<unsigned>(kDefaultMaxSeconds),
                    static_cast<unsigned long>(kSampleRateHz));
      return true;
    }
  }

  Serial.println(F("[MEM] WARN: PSRAM non disponibile o insufficiente, tentativo buffer ridotto (1 s) in RAM"));
  data_ = static_cast<int16_t*>(malloc(kFallbackCapacitySamples * sizeof(int16_t)));
  if (data_ != nullptr) {
    capacity_samples_ = kFallbackCapacitySamples;
    sample_count_ = 0;
    used_psram_ = false;
    Serial.printf("[MEM] AudioBuffer RAM fallback alloc=%lu bytes (1 s)\n",
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

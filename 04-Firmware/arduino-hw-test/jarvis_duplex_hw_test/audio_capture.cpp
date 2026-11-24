#include "audio_capture.h"

#include <Arduino.h>
#include <math.h>

namespace jarvis::duplex {

bool AudioCapture::Begin() {
  i2s_rx_.setPins(kI2sSckPin, kI2sWsPin, -1, kI2sSdPin, -1);
  if (!i2s_rx_.begin(I2S_MODE_STD,
                     kSampleRateHz,
                     I2S_DATA_BIT_WIDTH_32BIT,
                     I2S_SLOT_MODE_MONO,
                     I2S_STD_SLOT_LEFT)) {
    last_err_ = i2s_rx_.lastError();
    i2s_errors_++;
    ready_ = false;
    Serial.printf("[MIC] ERR: I2S0 RX begin() fallito (err=%d)\n", last_err_);
    return false;
  }

  ready_ = true;
  Serial.printf("[MIC] I2S0 RX ready (WS=GPIO%d SCK=GPIO%d SD=GPIO%d, 16kHz, 24->16bit)\n",
                kI2sWsPin, kI2sSckPin, kI2sSdPin);
  return true;
}

MicChunkStats AudioCapture::ReadChunk(int16_t* out_pcm16, size_t max_samples) {
  MicChunkStats stats{};
  if (!ready_ || out_pcm16 == nullptr || max_samples == 0) {
    stats.i2s_error = true;
    return stats;
  }

  const size_t n_req = (max_samples < kChunkSamples) ? max_samples : kChunkSamples;
  const size_t bytes_req = n_req * sizeof(int32_t);
  const size_t bytes_read = i2s_rx_.readBytes(reinterpret_cast<char*>(raw_buf_), bytes_req);
  const int err = i2s_rx_.lastError();

  if (bytes_read == 0 || err != 0) {
    i2s_errors_++;
    last_err_ = err;
    stats.i2s_error = true;
    stats.last_err = err;
  }

  const size_t n = bytes_read / sizeof(int32_t);
  if (n == 0) {
    return stats;
  }

  // Rimozione offset DC sul blocco prima della conversione a 16 bit
  int64_t sum24 = 0;
  for (size_t i = 0; i < n; ++i) {
    sum24 += static_cast<int64_t>(raw_buf_[i] >> 8);
  }
  const int32_t dc_mean = static_cast<int32_t>(sum24 / static_cast<int64_t>(n));

  double sum_sq = 0.0;
  for (size_t i = 0; i < n; ++i) {
    const int32_t ac24 = (raw_buf_[i] >> 8) - dc_mean;
    int32_t scaled = ac24 >> kMicShiftBits;

    if (scaled > 32767) {
      scaled = 32767;
      stats.clipped++;
    } else if (scaled < -32767) {
      scaled = -32767;
      stats.clipped++;
    }

    const int16_t pcm16 = static_cast<int16_t>(scaled);
    out_pcm16[i] = pcm16;

    const int16_t abs_v = (pcm16 < 0) ? static_cast<int16_t>(-pcm16) : pcm16;
    if (abs_v > stats.peak_abs_16) {
      stats.peak_abs_16 = abs_v;
    }
    const double d = static_cast<double>(pcm16);
    sum_sq += d * d;
  }

  stats.samples_read = n;
  stats.rms_16 = static_cast<uint16_t>(sqrt(sum_sq / static_cast<double>(n)));
  return stats;
}

}  // namespace jarvis::duplex

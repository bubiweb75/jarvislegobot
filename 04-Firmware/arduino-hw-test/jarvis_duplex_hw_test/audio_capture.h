#pragma once

#include <ESP_I2S.h>
#include <stddef.h>
#include <stdint.h>

namespace jarvis::duplex {

struct MicChunkStats {
  size_t samples_read = 0;
  int16_t peak_abs_16 = 0;
  uint16_t rms_16 = 0;
  uint32_t clipped = 0;
  bool i2s_error = false;
  int last_err = 0;
};

class AudioCapture {
public:
  static constexpr size_t kChunkSamples = 256;  // 16 ms @ 16 kHz

  bool Begin();
  bool IsReady() const { return ready_; }

  // Legge un blocco (256 campioni = 16 ms), converte da 24-bit in slot 32-bit a PCM 16-bit signed
  MicChunkStats ReadChunk(int16_t* out_pcm16, size_t max_samples);

  uint32_t ErrorCount() const { return i2s_errors_; }
  int LastError() const { return last_err_; }

private:
  static constexpr int8_t kI2sWsPin = 4;
  static constexpr int8_t kI2sSckPin = 5;
  static constexpr int8_t kI2sSdPin = 6;
  static constexpr uint32_t kSampleRateHz = 16000U;

  // Shift 6 bit dal valore 24-bit signed (equivale a >> 8 + guadagno 4x sicuro con clamp)
  static constexpr int kMicShiftBits = 6;

  I2SClass i2s_rx_{I2S_NUM_0};
  int32_t raw_buf_[kChunkSamples] = {};
  bool ready_ = false;
  uint32_t i2s_errors_ = 0;
  int last_err_ = 0;
};

}  // namespace jarvis::duplex

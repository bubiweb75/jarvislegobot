#pragma once

#include <ESP_I2S.h>
#include <stddef.h>
#include <stdint.h>

namespace jarvis::voice {

class AudioPlayer {
public:
  static constexpr uint8_t kMinVolumePct = 1;
  static constexpr uint8_t kMaxVolumePct = 15;
  static constexpr uint8_t kDefaultVolumePct = 5;

  bool Begin();
  bool Start();
  void Stop();
  void Update();

  bool IsReady() const { return ready_; }
  bool IsPlaying() const { return playing_; }

  uint8_t VolumePct() const { return volume_pct_; }
  bool SetVolumePct(uint8_t pct);

  uint32_t ErrorCount() const { return i2s_errors_; }
  int LastError() const { return last_err_; }
  size_t TotalBytesWritten() const { return bytes_written_; }
  size_t FramesPlayed() const { return frame_idx_; }
  size_t TotalFrames() const;
  uint32_t SampleRateHz() const;

private:
  static constexpr int8_t kI2sBclkPin = 15;
  static constexpr int8_t kI2sLrcPin = 16;
  static constexpr int8_t kI2sDinPin = 7;

  static constexpr size_t kChunkFrames = 256;          // 16 ms @ 16 kHz -> non blocca l'OLED
  static constexpr size_t kFadeFrames = 320;           // 20 ms fade-in / fade-out
  static constexpr size_t kSilenceFlushFrames = 960;   // 60 ms silenzio post-frase

  I2SClass i2s_{};
  int16_t stereo_buf_[kChunkFrames * 2] = {};
  bool ready_ = false;
  bool playing_ = false;
  bool flushing_ = false;

  size_t frame_idx_ = 0;
  size_t flush_idx_ = 0;
  size_t bytes_written_ = 0;
  uint8_t volume_pct_ = kDefaultVolumePct;
  uint32_t i2s_errors_ = 0;
  int last_err_ = 0;

  void WriteZeroFlush(size_t frames);
};

}  // namespace jarvis::voice

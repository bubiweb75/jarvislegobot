#pragma once

#include <ESP_I2S.h>
#include <stddef.h>
#include <stdint.h>

namespace jarvis::duplex {

class AudioBuffer;

class AudioPlayback {
public:
  static constexpr uint8_t kMinVolumePct = 1;
  static constexpr uint8_t kMaxVolumePct = 15;
  static constexpr uint8_t kDefaultVolumePct = 3;

  bool Begin();
  bool Start(const AudioBuffer& buffer);
  void Stop();
  void Update(const AudioBuffer& buffer);

  bool IsReady() const { return ready_; }
  bool IsPlaying() const { return playing_; }

  uint8_t VolumePct() const { return volume_pct_; }
  bool SetVolumePct(uint8_t pct);

  uint32_t ErrorCount() const { return i2s_errors_; }
  uint32_t PartialWriteCount() const { return partial_writes_; }
  int LastError() const { return last_err_; }
  size_t BytesWritten() const { return bytes_written_; }
  size_t FramesPlayed() const { return frame_idx_; }

  uint32_t MaxWriteUs() const { return max_write_us_; }
  uint32_t MaxInterWriteUs() const { return max_inter_write_us_; }
  uint32_t InterGt30MsCount() const { return inter_gt_30ms_; }
  uint32_t InterGt90MsCount() const { return inter_gt_90ms_; }

private:
  static constexpr int8_t kI2sBclkPin = 15;
  static constexpr int8_t kI2sLrcPin = 16;
  static constexpr int8_t kI2sDinPin = 7;
  static constexpr uint32_t kSampleRateHz = 16000U;

  static constexpr size_t kChunkFrames = 256;
  static constexpr size_t kFadeFrames = 320;          // 20 ms
  static constexpr size_t kSilenceFlushFrames = 960;  // 60 ms

  I2SClass i2s_tx_{I2S_NUM_1};
  int16_t stereo_buf_[kChunkFrames * 2] = {};
  bool ready_ = false;
  bool playing_ = false;
  bool flushing_ = false;

  size_t frame_idx_ = 0;
  size_t total_frames_ = 0;
  size_t flush_idx_ = 0;
  size_t bytes_written_ = 0;
  uint8_t volume_pct_ = kDefaultVolumePct;
  uint32_t partial_writes_ = 0;
  uint32_t i2s_errors_ = 0;
  int last_err_ = 0;

  uint32_t max_write_us_ = 0;
  uint32_t max_inter_write_us_ = 0;
  uint32_t inter_gt_30ms_ = 0;
  uint32_t inter_gt_90ms_ = 0;
  uint32_t last_write_end_us_ = 0;
  bool has_prev_write_end_ = false;

  void WriteZeroFlush(size_t frames);
};

}  // namespace jarvis::duplex

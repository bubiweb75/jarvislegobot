#pragma once

#include <ESP_I2S.h>
#include <freertos/FreeRTOS.h>
#include <freertos/semphr.h>
#include <freertos/task.h>
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
  bool IsPlaying() const;

  uint8_t VolumePct() const;
  bool SetVolumePct(uint8_t pct);

  uint32_t ErrorCount() const;
  uint32_t PartialWriteCount() const;
  int LastError() const;
  size_t BytesWritten() const;
  size_t FramesPlayed() const;

  uint32_t MaxWriteUs() const;
  uint32_t MaxInterWriteUs() const;
  uint32_t InterGt30MsCount() const;
  uint32_t InterGt90MsCount() const;

private:
  static constexpr int8_t kI2sBclkPin = 15;
  static constexpr int8_t kI2sLrcPin = 16;
  static constexpr int8_t kI2sDinPin = 7;
  static constexpr uint32_t kSampleRateHz = 16000U;

  static constexpr size_t kChunkFrames = 256;
  static constexpr size_t kFadeFrames = 320;          // 20 ms
  static constexpr size_t kSilenceFlushFrames = 960;  // 60 ms

  static constexpr uint32_t kTaskStackBytes = 4096;
  static constexpr UBaseType_t kTaskPriority = 3;
  static constexpr BaseType_t kTaskCore = 0;

  I2SClass i2s_tx_{I2S_NUM_1};
  int16_t stereo_buf_[kChunkFrames * 2] = {};
  bool ready_ = false;

  mutable portMUX_TYPE mux_ = portMUX_INITIALIZER_UNLOCKED;
  TaskHandle_t task_handle_ = nullptr;
  SemaphoreHandle_t done_sem_ = nullptr;

  const AudioBuffer* active_buffer_ = nullptr;
  bool playing_ = false;
  bool stop_requested_ = false;

  size_t frame_idx_ = 0;
  size_t total_frames_ = 0;
  size_t bytes_written_ = 0;
  uint8_t volume_pct_ = kDefaultVolumePct;
  uint8_t active_volume_pct_ = kDefaultVolumePct;
  uint32_t partial_writes_ = 0;
  uint32_t i2s_errors_ = 0;
  int last_err_ = 0;

  uint32_t max_write_us_ = 0;
  uint32_t max_inter_write_us_ = 0;
  uint32_t inter_gt_30ms_ = 0;
  uint32_t inter_gt_90ms_ = 0;

  static void TaskEntry(void* arg);
  void RunTaskLoop();
  void WriteZeroFlush(size_t frames);
};

}  // namespace jarvis::duplex

#pragma once

#include <ESP_I2S.h>
#include <freertos/FreeRTOS.h>
#include <freertos/semphr.h>
#include <freertos/task.h>
#include <stddef.h>
#include <stdint.h>

#include "vad_controller.h"

namespace jarvis::wakeword {
class MicroWakeWordDetector;
class PreRollRingBuffer;
}  // namespace jarvis::wakeword

namespace jarvis::duplex {

class AudioBuffer;

struct MicChunkStats {
  size_t samples_read = 0;
  int16_t min_16 = 0;
  int16_t max_16 = 0;
  int16_t peak_abs_16 = 0;
  uint16_t rms_16 = 0;
  int32_t dc_mean_24 = 0;
  uint32_t saturated = 0;
  uint32_t clipped = 0;
  bool partial_read = false;
  bool timeout_read = false;
  bool i2s_error = false;
  int last_err = 0;
};

struct RxSessionStats {
  int16_t min_16 = 0;
  int16_t max_16 = 0;
  int16_t peak_abs_16 = 0;
  uint32_t rms_16 = 0;
  int32_t dc_mean_24 = 0;
  uint32_t sat_count = 0;
  uint32_t clipped = 0;
  size_t samples = 0;
  uint32_t duration_ms = 0;
  uint32_t elapsed_ms = 0;
  uint32_t rx_errors = 0;
  uint32_t partial_reads = 0;
  uint32_t timeout_reads = 0;
  uint32_t max_inter_read_us = 0;
  uint32_t inter_gt_30ms = 0;
  uint32_t inter_gt_90ms = 0;
  bool stopped_by_timeout = false;
  bool stopped_by_buffer_full = false;
};

class AudioCapture {
public:
  static constexpr size_t kChunkSamples = 256;  // 16 ms @ 16 kHz
  static constexpr int16_t kSatThreshold16 = 32000;

  bool Begin();
  bool IsReady() const { return ready_; }

  // Avvio/arresto task FreeRTOS RX su AudioBuffer dedicato
  bool StartRecording(AudioBuffer& buffer, uint32_t max_duration_ms);
  void StopRecording();
  bool IsRecording() const;

  // Configurazione e controllo modalità Wake Word IDLE su Core 0 (unico proprietario I2S0)
  void SetWakeIdleConfig(jarvis::wakeword::MicroWakeWordDetector* detector,
                         jarvis::wakeword::PreRollRingBuffer* preroll,
                         AudioBuffer* wake_rx_buffer,
                         uint32_t max_record_ms);
  void SetIdleWakeActive(bool active, uint32_t guard_until_ms = 0);
  bool ConsumeWakeTriggered();
  bool HadSpeech() const;
  bool StoppedByNoSpeech() const;
  uint32_t TaskStackHighWaterMarkBytes() const;
  uint16_t NoiseFloorRms() const;
  uint16_t SpeechThresholdRms() const;

  // Lettura diretta bloccante di 1 chunk (usata da MIC_TEST in IDLE e dal task RX)
  MicChunkStats ReadChunk(int16_t* out_pcm16, size_t max_samples);

  RxSessionStats GetSessionStats() const;
  size_t CurrentSamples() const;
  int16_t CurrentPeak() const;
  uint32_t ErrorCount() const;
  int LastError() const;

private:
  static constexpr int8_t kI2sWsPin = 4;
  static constexpr int8_t kI2sSckPin = 5;
  static constexpr int8_t kI2sSdPin = 6;
  static constexpr uint32_t kSampleRateHz = 16000U;
  static constexpr int kMicShiftBits = 6;

  static constexpr uint32_t kTaskStackBytes = 12288;
  static constexpr UBaseType_t kTaskPriority = 3;
  static constexpr BaseType_t kTaskCore = 0;

  I2SClass i2s_rx_{I2S_NUM_0};
  int32_t raw_buf_[kChunkSamples] = {};
  int16_t task_pcm_buf_[kChunkSamples] = {};
  bool ready_ = false;

  mutable portMUX_TYPE mux_ = portMUX_INITIALIZER_UNLOCKED;
  TaskHandle_t task_handle_ = nullptr;
  SemaphoreHandle_t done_sem_ = nullptr;

  AudioBuffer* active_buffer_ = nullptr;
  bool recording_ = false;
  bool stop_requested_ = false;
  uint32_t max_duration_ms_ = 8000U;

  jarvis::wakeword::MicroWakeWordDetector* wake_detector_ = nullptr;
  jarvis::wakeword::PreRollRingBuffer* wake_preroll_ = nullptr;
  AudioBuffer* wake_rx_buffer_ = nullptr;
  uint32_t wake_max_record_ms_ = 8000U;
  bool idle_wake_active_ = false;
  uint32_t wake_guard_until_ms_ = 0;
  uint16_t dma_discard_frames_ = 0;
  static constexpr uint16_t kDmaDiscardFrames = 20U;  // 200 ms @ 10 ms/frame
  bool wake_triggered_ = false;
  bool vad_enabled_ = false;
  bool stopped_by_no_speech_ = false;
  VoiceActivityDetector vad_{};

  uint32_t i2s_errors_ = 0;
  int last_err_ = 0;
  RxSessionStats session_{};
  uint32_t rx_start_ms_ = 0;
  uint32_t rx_end_ms_ = 0;
  double rms_acc_sq_ = 0.0;
  int64_t dc_sum_ = 0;
  uint32_t dc_blocks_ = 0;

  static void TaskEntry(void* arg);
  void RunTaskLoop();
};

}  // namespace jarvis::duplex

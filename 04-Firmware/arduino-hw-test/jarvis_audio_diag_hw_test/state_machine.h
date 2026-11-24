#pragma once

#include <stdint.h>
#include "audio_capture.h"
#include "eye_controller.h"

namespace jarvis::duplex {

class AudioBuffer;
class AudioPlayback;
class ButtonController;

class StateMachine {
public:
  static constexpr uint32_t kMaxRecordMs = 5000U;
  static constexpr uint32_t kLoopbackRecordMs = 3000U;
  static constexpr uint32_t kToneTestDurationMs = 1500U;
  static constexpr uint32_t kMinValidSamples = 4800U;  // 300 ms @ 16 kHz
  static constexpr uint32_t kProcessingHoldMs = 120U;
  static constexpr uint32_t kErrorHoldMs = 2000U;

  void Begin(AudioBuffer& buffer,
             AudioCapture& capture,
             AudioPlayback& playback,
             EyeController& eyes,
             ButtonController& button);

  void Update(uint32_t now_ms);

  // Azioni da comandi seriali
  bool StartRecordCommand(uint32_t now_ms);
  bool StartLoopbackTestCommand(uint32_t now_ms);
  bool StartToneTestCommand(uint32_t now_ms);
  bool StartToneTestNoOledCommand(uint32_t now_ms);
  bool StartPlayCommand(uint32_t now_ms);
  void StopCommand(uint32_t now_ms);
  bool StartMicTestCommand(uint32_t now_ms);

  SystemState State() const { return state_; }
  const char* StateName() const;
  bool IsMicTestActive() const { return mic_test_active_; }
  int16_t LastPeakLevel() const { return rec_peak_16_; }
  uint32_t LastClipCount() const { return rec_clipped_; }

private:
  AudioBuffer* buffer_ = nullptr;
  AudioCapture* capture_ = nullptr;
  AudioPlayback* playback_ = nullptr;
  EyeController* eyes_ = nullptr;
  ButtonController* button_ = nullptr;

  SystemState state_ = SystemState::kIdle;
  uint32_t state_enter_ms_ = 0;
  uint32_t last_progress_ms_ = 0;
  uint32_t record_limit_ms_ = kMaxRecordMs;

  bool record_from_button_ = false;
  bool ignore_button_release_ = false;
  bool suspend_oled_during_play_ = false;

  int16_t chunk_pcm_[AudioCapture::kChunkSamples] = {};

  // Statistiche diagnostiche RX della sessione
  int16_t rec_min_16_ = 0;
  int16_t rec_max_16_ = 0;
  int16_t rec_peak_16_ = 0;
  double rec_rms_acc_sq_ = 0.0;
  int64_t rec_dc_sum_ = 0;
  uint32_t rec_dc_blocks_ = 0;
  uint32_t rec_sat_count_ = 0;
  uint32_t rec_clipped_ = 0;
  uint32_t rec_rx_err_start_ = 0;

  // Statistiche diagnostiche TX e timing loop
  uint32_t play_tx_err_start_ = 0;
  uint32_t play_partial_start_ = 0;
  uint32_t last_loop_tick_ms_ = 0;
  uint32_t max_loop_gap_ms_ = 0;
  uint32_t max_oled_us_ = 0;

  // Diagnostica MIC_TEST non bloccante (solo in IDLE)
  bool mic_test_active_ = false;
  uint32_t mic_test_end_ms_ = 0;
  uint32_t mic_test_report_ms_ = 0;
  int16_t mic_test_min_ = 0;
  int16_t mic_test_max_ = 0;
  int16_t mic_test_peak_ = 0;
  uint32_t mic_test_rms_acc_ = 0;
  uint32_t mic_test_sat_ = 0;
  uint32_t mic_test_blocks_ = 0;
  uint32_t mic_test_samples_ = 0;

  void TransitionTo(SystemState next, uint32_t now_ms);
  bool RunToneTestInternal(bool suspend_oled, uint32_t now_ms);
  bool BeginRecording(bool from_button, uint32_t limit_ms, uint32_t now_ms);
  void UpdateListening(uint32_t now_ms);
  void UpdateProcessing(uint32_t now_ms);
  void UpdatePlaying(uint32_t now_ms);
  void UpdateMicTest(uint32_t now_ms);
  void ResetLoopGap(uint32_t now_ms);
  void TrackLoopGap(uint32_t now_ms);
  void PrintRxDiagnostics() const;
  void PrintTxDiagnostics() const;
};

}  // namespace jarvis::duplex

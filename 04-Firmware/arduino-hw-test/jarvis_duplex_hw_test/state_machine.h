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

  bool record_from_button_ = false;
  bool ignore_button_release_ = false;

  int16_t chunk_pcm_[AudioCapture::kChunkSamples] = {};
  int16_t rec_peak_16_ = 0;
  uint32_t rec_clipped_ = 0;

  // Diagnostica MIC_TEST non bloccante (solo in IDLE)
  bool mic_test_active_ = false;
  uint32_t mic_test_end_ms_ = 0;
  uint32_t mic_test_report_ms_ = 0;
  int16_t mic_test_peak_ = 0;
  uint32_t mic_test_rms_acc_ = 0;
  uint32_t mic_test_blocks_ = 0;
  uint32_t mic_test_samples_ = 0;

  void TransitionTo(SystemState next, uint32_t now_ms);
  bool BeginRecording(bool from_button, uint32_t now_ms);
  void UpdateListening(uint32_t now_ms);
  void UpdateProcessing(uint32_t now_ms);
  void UpdatePlaying(uint32_t now_ms);
  void UpdateMicTest(uint32_t now_ms);
};

}  // namespace jarvis::duplex

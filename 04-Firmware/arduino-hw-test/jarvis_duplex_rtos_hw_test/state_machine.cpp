#include "state_machine.h"

#include <Arduino.h>
#include <limits.h>
#include <math.h>
#include "audio_buffer.h"
#include "audio_capture.h"
#include "audio_playback.h"
#include "button_controller.h"

namespace jarvis::duplex {

namespace {

const char* NameFor(SystemState s) {
  switch (s) {
    case SystemState::kIdle: return "IDLE";
    case SystemState::kListening: return "LISTENING";
    case SystemState::kProcessing: return "PROCESSING";
    case SystemState::kPlaying: return "PLAYING";
    case SystemState::kError: return "ERROR";
  }
  return "UNKNOWN";
}

}  // namespace

void StateMachine::Begin(AudioBuffer& buffer,
                         AudioCapture& capture,
                         AudioPlayback& playback,
                         EyeController& eyes,
                         ButtonController& button) {
  buffer_ = &buffer;
  capture_ = &capture;
  playback_ = &playback;
  eyes_ = &eyes;
  button_ = &button;
  state_ = SystemState::kIdle;
  state_enter_ms_ = millis();
  last_loop_tick_ms_ = state_enter_ms_;
  eyes_->ApplyState(state_, state_enter_ms_);
}

const char* StateMachine::StateName() const {
  return NameFor(state_);
}

void StateMachine::ResetLoopGap(uint32_t now_ms) {
  last_loop_tick_ms_ = now_ms;
  max_loop_gap_ms_ = 0;
  max_oled_us_ = 0;
}

void StateMachine::TrackLoopGap(uint32_t now_ms) {
  const uint32_t gap = now_ms - last_loop_tick_ms_;
  last_loop_tick_ms_ = now_ms;
  if (gap > max_loop_gap_ms_) {
    max_loop_gap_ms_ = gap;
  }
}

void StateMachine::TransitionTo(SystemState next, uint32_t now_ms) {
  if (next == state_) {
    return;
  }
  if (next != SystemState::kPlaying) {
    suspend_oled_during_play_ = false;
  }
  if (next != SystemState::kListening) {
    suspend_oled_during_listen_ = false;
  }
  Serial.printf("[STATE] %s -> %s\n", NameFor(state_), NameFor(next));
  state_ = next;
  state_enter_ms_ = now_ms;
  last_progress_ms_ = now_ms;
  eyes_->ApplyState(state_, now_ms);
}

bool StateMachine::BeginRecording(bool from_button, uint32_t limit_ms, uint32_t now_ms) {
  if (state_ != SystemState::kIdle || mic_test_active_) {
    Serial.printf("[WARN] Impossibile avviare registrazione in stato %s\n", StateName());
    return false;
  }
  if (!capture_->IsReady() || !buffer_->IsAllocated()) {
    Serial.println(F("[ERR] Microfono o AudioBuffer non pronti"));
    TransitionTo(SystemState::kError, now_ms);
    return false;
  }

  record_from_button_ = from_button;
  ResetLoopGap(now_ms);
  if (!capture_->StartRecording(*buffer_, limit_ms)) {
    Serial.println(F("[ERR] Avvio task FreeRTOS RX fallito"));
    TransitionTo(SystemState::kError, now_ms);
    return false;
  }

  TransitionTo(SystemState::kListening, now_ms);
  Serial.printf("[MIC] Recording started (RTOS RX, limit=%lums)\n", static_cast<unsigned long>(limit_ms));
  return true;
}

bool StateMachine::StartRecordCommand(uint32_t now_ms) {
  return BeginRecording(false, kMaxRecordMs, now_ms);
}

bool StateMachine::StartLoopbackTestCommand(uint32_t now_ms) {
  return RunLoopbackTestInternal(false, now_ms);
}

bool StateMachine::StartLoopbackTestNoOledCommand(uint32_t now_ms) {
  return RunLoopbackTestInternal(true, now_ms);
}

bool StateMachine::RunLoopbackTestInternal(bool suspend_oled, uint32_t now_ms) {
  Serial.printf("[%s] Registrazione 3.0 s + riproduzione RTOS (OLED in LISTENING=%s)...\n",
                suspend_oled ? "LOOPBACK_TEST_NO_OLED" : "LOOPBACK_TEST",
                suspend_oled ? "SUSPENDED" : "ACTIVE");
  suspend_oled_during_listen_ = suspend_oled;
  if (!BeginRecording(false, kLoopbackRecordMs, now_ms)) {
    suspend_oled_during_listen_ = false;
    return false;
  }
  return true;
}

bool StateMachine::StartToneTestCommand(uint32_t now_ms) {
  return RunToneTestInternal(false, now_ms);
}

bool StateMachine::StartToneTestNoOledCommand(uint32_t now_ms) {
  return RunToneTestInternal(true, now_ms);
}

bool StateMachine::RunToneTestInternal(bool suspend_oled, uint32_t now_ms) {
  if (state_ != SystemState::kIdle || mic_test_active_) {
    Serial.printf("[WARN] %s disponibile solo in IDLE (stato=%s)\n",
                  suspend_oled ? "TONE_TEST_NO_OLED" : "TONE_TEST",
                  StateName());
    return false;
  }
  if (!buffer_->IsAllocated() || !playback_->IsReady()) {
    Serial.println(F("[TONE_TEST] ERR: AudioBuffer o I2S1 TX non pronti"));
    TransitionTo(SystemState::kError, now_ms);
    return false;
  }

  buffer_->Clear();
  const size_t total_samples = (AudioBuffer::kSampleRateHz * kToneTestDurationMs) / 1000U;
  const size_t cap = buffer_->CapacitySamples();
  const size_t n = (total_samples < cap) ? total_samples : cap;
  const float two_pi_f_over_fs = (2.0f * static_cast<float>(M_PI) * 440.0f) /
                                 static_cast<float>(AudioBuffer::kSampleRateHz);

  constexpr size_t kGenChunk = 256;
  int16_t gen_buf[kGenChunk];
  size_t idx = 0;
  while (idx < n) {
    const size_t k = ((n - idx) < kGenChunk) ? (n - idx) : kGenChunk;
    for (size_t i = 0; i < k; ++i) {
      const float s = sinf(two_pi_f_over_fs * static_cast<float>(idx + i));
      gen_buf[i] = static_cast<int16_t>(lroundf(s * 32000.0f));
    }
    buffer_->Append(gen_buf, k);
    idx += k;
  }

  Serial.printf("[%s] Sinusoide 440Hz: samples=%lu dur=%lums vol=%u%% oled=%s\n",
                suspend_oled ? "TONE_TEST_NO_OLED" : "TONE_TEST",
                static_cast<unsigned long>(buffer_->SampleCount()),
                static_cast<unsigned long>(buffer_->DurationMs()),
                static_cast<unsigned>(playback_->VolumePct()),
                suspend_oled ? "SUSPENDED" : "ACTIVE");

  play_tx_err_start_ = playback_->ErrorCount();
  play_partial_start_ = playback_->PartialWriteCount();
  ResetLoopGap(now_ms);
  suspend_oled_during_play_ = suspend_oled;
  if (!playback_->Start(*buffer_)) {
    suspend_oled_during_play_ = false;
    TransitionTo(SystemState::kError, now_ms);
    return false;
  }
  TransitionTo(SystemState::kPlaying, now_ms);
  return true;
}

bool StateMachine::StartPlayCommand(uint32_t now_ms) {
  if (state_ != SystemState::kIdle || mic_test_active_) {
    Serial.printf("[WARN] Comando PLAY ignorato in stato %s\n", StateName());
    return false;
  }
  if (buffer_->SampleCount() < kMinValidSamples) {
    Serial.println(F("[AUDIO] Nessuna registrazione valida da riprodurre"));
    return false;
  }
  play_tx_err_start_ = playback_->ErrorCount();
  play_partial_start_ = playback_->PartialWriteCount();
  ResetLoopGap(now_ms);
  if (!playback_->Start(*buffer_)) {
    TransitionTo(SystemState::kError, now_ms);
    return false;
  }
  TransitionTo(SystemState::kPlaying, now_ms);
  return true;
}

void StateMachine::StopCommand(uint32_t now_ms) {
  if (mic_test_active_) {
    mic_test_active_ = false;
    Serial.println(F("[MIC_TEST] Interrotto"));
  }
  if (state_ == SystemState::kListening) {
    record_from_button_ = false;
    capture_->StopRecording();
    last_rx_stats_ = capture_->GetSessionStats();
    TransitionTo(SystemState::kProcessing, now_ms);
  } else if (state_ == SystemState::kPlaying) {
    playback_->Stop();
    PrintTxDiagnostics();
    TransitionTo(SystemState::kIdle, now_ms);
  } else if (state_ == SystemState::kProcessing || state_ == SystemState::kError) {
    TransitionTo(SystemState::kIdle, now_ms);
  }
}

bool StateMachine::StartMicTestCommand(uint32_t now_ms) {
  if (state_ != SystemState::kIdle || mic_test_active_) {
    Serial.printf("[WARN] MIC_TEST disponibile solo in IDLE (stato=%s)\n", StateName());
    return false;
  }
  if (!capture_->IsReady()) {
    Serial.println(F("[MIC_TEST] ERR: I2S0 RX non pronto"));
    return false;
  }
  mic_test_active_ = true;
  mic_test_end_ms_ = now_ms + 2500U;
  mic_test_report_ms_ = now_ms;
  mic_test_min_ = INT16_MAX;
  mic_test_max_ = INT16_MIN;
  mic_test_peak_ = 0;
  mic_test_rms_acc_ = 0;
  mic_test_sat_ = 0;
  mic_test_blocks_ = 0;
  mic_test_samples_ = 0;
  Serial.println(F("[MIC_TEST] Avviato per 2.5 s..."));
  return true;
}

void StateMachine::PrintRxDiagnostics() const {
  const auto& s = last_rx_stats_;
  const double sat_pct = (s.samples > 0)
                             ? (100.0 * static_cast<double>(s.sat_count) / static_cast<double>(s.samples))
                             : 0.0;
  // Stima campionamento atteso rispetto al tempo trascorso (16 campioni/ms @ 16 kHz)
  const size_t est_expected = static_cast<size_t>(s.elapsed_ms) * (AudioBuffer::kSampleRateHz / 1000U);
  const size_t est_loss = (est_expected > s.samples) ? (est_expected - s.samples) : 0U;

  Serial.printf(
      "[DIAG_RX] MIN=%d | MAX=%d | DC24=%ld | RMS=%lu | PEAK=%d | SAT=%lu(%.2f%%) | CLIP=%lu | SAMPLES=%lu | DUR=%lums | ELAPSED=%lums | EST_LOSS=%lu | RX_ERR=%lu | PARTIAL=%lu | TIMEOUTS=%lu | MAX_GAP=%.2fms | INTER>30ms=%lu | INTER>90ms=%lu | BUF_FULL=%u\n",
      static_cast<int>(s.min_16),
      static_cast<int>(s.max_16),
      static_cast<long>(s.dc_mean_24),
      static_cast<unsigned long>(s.rms_16),
      static_cast<int>(s.peak_abs_16),
      static_cast<unsigned long>(s.sat_count),
      sat_pct,
      static_cast<unsigned long>(s.clipped),
      static_cast<unsigned long>(s.samples),
      static_cast<unsigned long>(s.duration_ms),
      static_cast<unsigned long>(s.elapsed_ms),
      static_cast<unsigned long>(est_loss),
      static_cast<unsigned long>(s.rx_errors),
      static_cast<unsigned long>(s.partial_reads),
      static_cast<unsigned long>(s.timeout_reads),
      static_cast<double>(s.max_inter_read_us) / 1000.0,
      static_cast<unsigned long>(s.inter_gt_30ms),
      static_cast<unsigned long>(s.inter_gt_90ms),
      s.stopped_by_buffer_full ? 1U : 0U);
}

void StateMachine::PrintTxDiagnostics() const {
  const uint32_t tx_err = playback_->ErrorCount() - play_tx_err_start_;
  const uint32_t partial = playback_->PartialWriteCount() - play_partial_start_;
  Serial.printf(
      "[DIAG_TX] BYTES=%lu | PARTIAL=%lu | TX_ERR=%lu | MAX_GAP=%lums | MAX_WRITE=%.2fms | MAX_INTER_WRITE=%.2fms | INTER>30ms=%lu | INTER>90ms=%lu | MAX_OLED=%.2fms\n",
      static_cast<unsigned long>(playback_->BytesWritten()),
      static_cast<unsigned long>(partial),
      static_cast<unsigned long>(tx_err),
      static_cast<unsigned long>(max_loop_gap_ms_),
      static_cast<double>(playback_->MaxWriteUs()) / 1000.0,
      static_cast<double>(playback_->MaxInterWriteUs()) / 1000.0,
      static_cast<unsigned long>(playback_->InterGt30MsCount()),
      static_cast<unsigned long>(playback_->InterGt90MsCount()),
      static_cast<double>(max_oled_us_) / 1000.0);
}

void StateMachine::UpdateListening(uint32_t now_ms) {
  if ((now_ms - last_progress_ms_) >= 1000U) {
    last_progress_ms_ = now_ms;
    Serial.printf("[MIC] Recording... samples=%lu peak=%d\n",
                  static_cast<unsigned long>(capture_->CurrentSamples()),
                  static_cast<int>(capture_->CurrentPeak()));
  }

  if (!capture_->IsRecording()) {
    last_rx_stats_ = capture_->GetSessionStats();
    Serial.printf("[MIC] Limite raggiunto (%lums, %lu campioni)\n",
                  static_cast<unsigned long>(last_rx_stats_.elapsed_ms),
                  static_cast<unsigned long>(last_rx_stats_.samples));
    if (record_from_button_ && button_->IsPressed()) {
      ignore_button_release_ = true;
    }
    TransitionTo(SystemState::kProcessing, now_ms);
    return;
  }

  if (record_from_button_ && button_->ConsumeReleasedEdge()) {
    capture_->StopRecording();
    last_rx_stats_ = capture_->GetSessionStats();
    TransitionTo(SystemState::kProcessing, now_ms);
  }
}

void StateMachine::UpdateProcessing(uint32_t now_ms) {
  if ((now_ms - state_enter_ms_) < kProcessingHoldMs) {
    return;
  }

  PrintRxDiagnostics();

  if (buffer_->SampleCount() < kMinValidSamples) {
    Serial.println(F("[MIC] Pressione troppo breve: nessuna riproduzione avviata"));
    buffer_->Clear();
    TransitionTo(SystemState::kIdle, now_ms);
    return;
  }

  play_tx_err_start_ = playback_->ErrorCount();
  play_partial_start_ = playback_->PartialWriteCount();
  ResetLoopGap(now_ms);
  if (!playback_->Start(*buffer_)) {
    TransitionTo(SystemState::kError, now_ms);
    return;
  }
  TransitionTo(SystemState::kPlaying, now_ms);
}

void StateMachine::UpdatePlaying(uint32_t now_ms) {
  TrackLoopGap(now_ms);
  playback_->Update(*buffer_);
  if (!playback_->IsPlaying()) {
    PrintTxDiagnostics();
    TransitionTo(SystemState::kIdle, now_ms);
  }
}

void StateMachine::UpdateMicTest(uint32_t now_ms) {
  const MicChunkStats st = capture_->ReadChunk(chunk_pcm_, AudioCapture::kChunkSamples);
  if (st.samples_read > 0) {
    if (st.min_16 < mic_test_min_) mic_test_min_ = st.min_16;
    if (st.max_16 > mic_test_max_) mic_test_max_ = st.max_16;
    if (st.peak_abs_16 > mic_test_peak_) mic_test_peak_ = st.peak_abs_16;
    mic_test_rms_acc_ += st.rms_16;
    mic_test_sat_ += st.saturated;
    mic_test_blocks_++;
    mic_test_samples_ += static_cast<uint32_t>(st.samples_read);
  }

  if ((now_ms - mic_test_report_ms_) >= 500U) {
    mic_test_report_ms_ = now_ms;
    const uint32_t avg_rms = (mic_test_blocks_ > 0) ? (mic_test_rms_acc_ / mic_test_blocks_) : 0;
    const double sat_pct = (mic_test_samples_ > 0)
                               ? (100.0 * static_cast<double>(mic_test_sat_) / static_cast<double>(mic_test_samples_))
                               : 0.0;
    Serial.printf("[MIC_TEST] MIN=%d MAX=%d RMS=%lu PEAK=%d SAT=%.2f%% SAMPLES=%lu I2S_ERR=%lu\n",
                  static_cast<int>(mic_test_samples_ > 0 ? mic_test_min_ : 0),
                  static_cast<int>(mic_test_samples_ > 0 ? mic_test_max_ : 0),
                  static_cast<unsigned long>(avg_rms),
                  static_cast<int>(mic_test_peak_),
                  sat_pct,
                  static_cast<unsigned long>(mic_test_samples_),
                  static_cast<unsigned long>(capture_->ErrorCount()));
    mic_test_min_ = INT16_MAX;
    mic_test_max_ = INT16_MIN;
    mic_test_peak_ = 0;
    mic_test_rms_acc_ = 0;
    mic_test_sat_ = 0;
    mic_test_blocks_ = 0;
    mic_test_samples_ = 0;
  }

  if (static_cast<int32_t>(now_ms - mic_test_end_ms_) >= 0) {
    mic_test_active_ = false;
    Serial.println(F("[MIC_TEST] Completato"));
  }
}

void StateMachine::Update(uint32_t now_ms) {
  button_->Update(now_ms);

  if (ignore_button_release_ && button_->ConsumeReleasedEdge()) {
    ignore_button_release_ = false;
  }

  if (state_ == SystemState::kIdle) {
    if (mic_test_active_) {
      UpdateMicTest(now_ms);
    } else if (button_->ConsumePressedEdge()) {
      BeginRecording(true, kMaxRecordMs, now_ms);
    }
  } else if (state_ == SystemState::kListening) {
    UpdateListening(now_ms);
  } else if (state_ == SystemState::kProcessing) {
    UpdateProcessing(now_ms);
  } else if (state_ == SystemState::kPlaying) {
    UpdatePlaying(now_ms);
  } else if (state_ == SystemState::kError) {
    if ((now_ms - state_enter_ms_) >= kErrorHoldMs || button_->ConsumePressedEdge()) {
      TransitionTo(SystemState::kIdle, now_ms);
    }
  }

  if (state_ == SystemState::kPlaying) {
    if (!suspend_oled_during_play_) {
      const uint32_t oled_t0 = micros();
      eyes_->Update(now_ms);
      const uint32_t oled_dt = micros() - oled_t0;
      if (oled_dt > max_oled_us_) {
        max_oled_us_ = oled_dt;
      }
    }
  } else if (state_ == SystemState::kListening && suspend_oled_during_listen_) {
    // Test A/B: OLED sospeso esclusivamente durante LISTENING
  } else {
    eyes_->Update(now_ms);
  }
}

}  // namespace jarvis::duplex

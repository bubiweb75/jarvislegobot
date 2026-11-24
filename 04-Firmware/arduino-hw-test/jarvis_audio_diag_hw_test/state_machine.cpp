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

  buffer_->Clear();
  record_limit_ms_ = limit_ms;
  rec_min_16_ = INT16_MAX;
  rec_max_16_ = INT16_MIN;
  rec_peak_16_ = 0;
  rec_rms_acc_sq_ = 0.0;
  rec_dc_sum_ = 0;
  rec_dc_blocks_ = 0;
  rec_sat_count_ = 0;
  rec_clipped_ = 0;
  rec_rx_err_start_ = capture_->ErrorCount();
  record_from_button_ = from_button;
  ResetLoopGap(now_ms);
  TransitionTo(SystemState::kListening, now_ms);
  Serial.printf("[MIC] Recording started (limit=%lums)\n", static_cast<unsigned long>(limit_ms));
  return true;
}

bool StateMachine::StartRecordCommand(uint32_t now_ms) {
  return BeginRecording(false, kMaxRecordMs, now_ms);
}

bool StateMachine::StartLoopbackTestCommand(uint32_t now_ms) {
  Serial.println(F("[LOOPBACK_TEST] Avvio registrazione 3.0 s + riproduzione sequenziale..."));
  return BeginRecording(false, kLoopbackRecordMs, now_ms);
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

  // Genera sinusoide pura 440 Hz a +-32000 nel buffer (scalata poi da VolumePct() = 3..15%)
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
  const size_t n = buffer_->SampleCount();
  const uint32_t rms = (n > 0) ? static_cast<uint32_t>(sqrt(rec_rms_acc_sq_ / static_cast<double>(n))) : 0U;
  const int32_t dc24 = (rec_dc_blocks_ > 0) ? static_cast<int32_t>(rec_dc_sum_ / static_cast<int64_t>(rec_dc_blocks_)) : 0;
  const double sat_pct = (n > 0) ? (100.0 * static_cast<double>(rec_sat_count_) / static_cast<double>(n)) : 0.0;
  const uint32_t rx_err = capture_->ErrorCount() - rec_rx_err_start_;

  Serial.printf(
      "[DIAG_RX] MIN=%d | MAX=%d | DC24=%ld | RMS=%lu | PEAK=%d | SAT=%lu(%.2f%%) | CLIP=%lu | SAMPLES=%lu | DUR=%lums | RX_ERR=%lu | MAX_GAP=%lums\n",
      static_cast<int>(n > 0 ? rec_min_16_ : 0),
      static_cast<int>(n > 0 ? rec_max_16_ : 0),
      static_cast<long>(dc24),
      static_cast<unsigned long>(rms),
      static_cast<int>(rec_peak_16_),
      static_cast<unsigned long>(rec_sat_count_),
      sat_pct,
      static_cast<unsigned long>(rec_clipped_),
      static_cast<unsigned long>(n),
      static_cast<unsigned long>(buffer_->DurationMs()),
      static_cast<unsigned long>(rx_err),
      static_cast<unsigned long>(max_loop_gap_ms_));
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
  TrackLoopGap(now_ms);
  const MicChunkStats st = capture_->ReadChunk(chunk_pcm_, AudioCapture::kChunkSamples);
  if (st.samples_read > 0) {
    buffer_->Append(chunk_pcm_, st.samples_read);
    if (st.min_16 < rec_min_16_) rec_min_16_ = st.min_16;
    if (st.max_16 > rec_max_16_) rec_max_16_ = st.max_16;
    if (st.peak_abs_16 > rec_peak_16_) rec_peak_16_ = st.peak_abs_16;
    const double r = static_cast<double>(st.rms_16);
    rec_rms_acc_sq_ += r * r * static_cast<double>(st.samples_read);
    rec_dc_sum_ += static_cast<int64_t>(st.dc_mean_24);
    rec_dc_blocks_++;
    rec_sat_count_ += st.saturated;
    rec_clipped_ += st.clipped;
  }

  if ((now_ms - last_progress_ms_) >= 1000U) {
    last_progress_ms_ = now_ms;
    Serial.printf("[MIC] Recording... samples=%lu peak=%d max_gap=%lums\n",
                  static_cast<unsigned long>(buffer_->SampleCount()),
                  static_cast<int>(rec_peak_16_),
                  static_cast<unsigned long>(max_loop_gap_ms_));
  }

  const bool hit_timeout = (now_ms - state_enter_ms_) >= record_limit_ms_;
  const bool hit_capacity = (buffer_->SampleCount() >= buffer_->CapacitySamples());

  if (hit_timeout || hit_capacity) {
    Serial.printf("[MIC] Limite raggiunto (%lums, %lu campioni)\n",
                  static_cast<unsigned long>(now_ms - state_enter_ms_),
                  static_cast<unsigned long>(buffer_->SampleCount()));
    if (record_from_button_ && button_->IsPressed()) {
      ignore_button_release_ = true;
    }
    TransitionTo(SystemState::kProcessing, now_ms);
    return;
  }

  if (record_from_button_ && button_->ConsumeReleasedEdge()) {
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
  } else {
    eyes_->Update(now_ms);
  }
}

}  // namespace jarvis::duplex

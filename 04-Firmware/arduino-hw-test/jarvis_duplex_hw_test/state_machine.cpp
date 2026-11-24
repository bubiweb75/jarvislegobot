#include "state_machine.h"

#include <Arduino.h>
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
  eyes_->ApplyState(state_, state_enter_ms_);
}

const char* StateMachine::StateName() const {
  return NameFor(state_);
}

void StateMachine::TransitionTo(SystemState next, uint32_t now_ms) {
  if (next == state_) {
    return;
  }
  Serial.printf("[STATE] %s -> %s\n", NameFor(state_), NameFor(next));
  state_ = next;
  state_enter_ms_ = now_ms;
  last_progress_ms_ = now_ms;
  eyes_->ApplyState(state_, now_ms);
}

bool StateMachine::BeginRecording(bool from_button, uint32_t now_ms) {
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
  rec_peak_16_ = 0;
  rec_clipped_ = 0;
  record_from_button_ = from_button;
  TransitionTo(SystemState::kListening, now_ms);
  Serial.println(F("[MIC] Recording started"));
  return true;
}

bool StateMachine::StartRecordCommand(uint32_t now_ms) {
  return BeginRecording(false, now_ms);
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
  mic_test_peak_ = 0;
  mic_test_rms_acc_ = 0;
  mic_test_blocks_ = 0;
  mic_test_samples_ = 0;
  Serial.println(F("[MIC_TEST] Avviato per 2.5 s..."));
  return true;
}

void StateMachine::UpdateListening(uint32_t now_ms) {
  const MicChunkStats st = capture_->ReadChunk(chunk_pcm_, AudioCapture::kChunkSamples);
  if (st.samples_read > 0) {
    buffer_->Append(chunk_pcm_, st.samples_read);
    if (st.peak_abs_16 > rec_peak_16_) {
      rec_peak_16_ = st.peak_abs_16;
    }
    rec_clipped_ += st.clipped;
  }

  if ((now_ms - last_progress_ms_) >= 1000U) {
    last_progress_ms_ = now_ms;
    Serial.printf("[MIC] Recording... samples=%lu peak=%d\n",
                  static_cast<unsigned long>(buffer_->SampleCount()),
                  static_cast<int>(rec_peak_16_));
  }

  const bool hit_timeout = (now_ms - state_enter_ms_) >= kMaxRecordMs;
  const bool hit_capacity = (buffer_->SampleCount() >= buffer_->CapacitySamples());

  if (hit_timeout || hit_capacity) {
    Serial.printf("[MIC] Limite massimo raggiunto (%lums, %lu campioni)\n",
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

  Serial.printf("[MIC] Samples captured: %lu (%lums)\n",
                static_cast<unsigned long>(buffer_->SampleCount()),
                static_cast<unsigned long>(buffer_->DurationMs()));
  Serial.printf("[MIC] Peak level: %d (clipped=%lu)\n",
                static_cast<int>(rec_peak_16_),
                static_cast<unsigned long>(rec_clipped_));

  if (buffer_->SampleCount() < kMinValidSamples) {
    Serial.println(F("[MIC] Pressione troppo breve: nessuna riproduzione avviata"));
    buffer_->Clear();
    TransitionTo(SystemState::kIdle, now_ms);
    return;
  }

  if (!playback_->Start(*buffer_)) {
    TransitionTo(SystemState::kError, now_ms);
    return;
  }
  TransitionTo(SystemState::kPlaying, now_ms);
}

void StateMachine::UpdatePlaying(uint32_t now_ms) {
  playback_->Update(*buffer_);
  if (!playback_->IsPlaying()) {
    TransitionTo(SystemState::kIdle, now_ms);
  }
}

void StateMachine::UpdateMicTest(uint32_t now_ms) {
  const MicChunkStats st = capture_->ReadChunk(chunk_pcm_, AudioCapture::kChunkSamples);
  if (st.samples_read > 0) {
    if (st.peak_abs_16 > mic_test_peak_) {
      mic_test_peak_ = st.peak_abs_16;
    }
    mic_test_rms_acc_ += st.rms_16;
    mic_test_blocks_++;
    mic_test_samples_ += static_cast<uint32_t>(st.samples_read);
  }

  if ((now_ms - mic_test_report_ms_) >= 500U) {
    mic_test_report_ms_ = now_ms;
    const uint32_t avg_rms = (mic_test_blocks_ > 0) ? (mic_test_rms_acc_ / mic_test_blocks_) : 0;
    Serial.printf("[MIC_TEST] RMS=%lu | PEAK=%d | SAMPLES=%lu | I2S_ERR=%lu\n",
                  static_cast<unsigned long>(avg_rms),
                  static_cast<int>(mic_test_peak_),
                  static_cast<unsigned long>(mic_test_samples_),
                  static_cast<unsigned long>(capture_->ErrorCount()));
    mic_test_peak_ = 0;
    mic_test_rms_acc_ = 0;
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
      BeginRecording(true, now_ms);
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

  eyes_->Update(now_ms);
}

}  // namespace jarvis::duplex

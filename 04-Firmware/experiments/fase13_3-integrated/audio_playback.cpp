#include "audio_playback.h"

#include <Arduino.h>
#include <string.h>

#include "audio_buffer.h"

namespace jarvis::duplex {

void AudioPlayback::TaskEntry(void* arg) {
  auto* self = static_cast<AudioPlayback*>(arg);
  if (self != nullptr) {
    self->RunTaskLoop();
  }
  vTaskDelete(nullptr);
}

bool AudioPlayback::Begin() {
  i2s_tx_.setPins(kI2sBclkPin, kI2sLrcPin, kI2sDinPin, -1, -1);
  if (!i2s_tx_.begin(I2S_MODE_STD,
                     kSampleRateHz,
                     I2S_DATA_BIT_WIDTH_16BIT,
                     I2S_SLOT_MODE_STEREO,
                     I2S_STD_SLOT_BOTH)) {
    last_err_ = i2s_tx_.lastError();
    i2s_errors_++;
    ready_ = false;
    Serial.printf("[AUDIO] ERR: I2S1 TX begin() fallito (err=%d)\n", last_err_);
    return false;
  }

  done_sem_ = xSemaphoreCreateBinary();
  if (done_sem_ == nullptr) {
    ready_ = false;
    Serial.println(F("[AUDIO] ERR: creazione semaforo FreeRTOS fallita"));
    return false;
  }

  const BaseType_t ok = xTaskCreatePinnedToCore(
      TaskEntry,
      "jarvis_audio_tx",
      kTaskStackBytes,
      this,
      kTaskPriority,
      &task_handle_,
      kTaskCore);
  if (ok != pdPASS || task_handle_ == nullptr) {
    vSemaphoreDelete(done_sem_);
    done_sem_ = nullptr;
    ready_ = false;
    Serial.println(F("[AUDIO] ERR: creazione task FreeRTOS AudioTX fallita"));
    return false;
  }

  ready_ = true;
  Serial.printf("[AUDIO] I2S1 TX ready (RTOS task Core=%d Prio=%u, BCLK=GPIO%d LRC=GPIO%d DIN=GPIO%d, 16kHz, vol=%u%%)\n",
                static_cast<int>(kTaskCore),
                static_cast<unsigned>(kTaskPriority),
                kI2sBclkPin,
                kI2sLrcPin,
                kI2sDinPin,
                static_cast<unsigned>(volume_pct_));
  WriteZeroFlush(kSilenceFlushFrames);
  return true;
}

bool AudioPlayback::IsPlaying() const {
  portENTER_CRITICAL(&mux_);
  const bool p = playing_;
  portEXIT_CRITICAL(&mux_);
  return p;
}

uint8_t AudioPlayback::VolumePct() const {
  portENTER_CRITICAL(&mux_);
  const uint8_t v = volume_pct_;
  portEXIT_CRITICAL(&mux_);
  return v;
}

bool AudioPlayback::SetVolumePct(uint8_t pct) {
  if (pct < kMinVolumePct || pct > kMaxVolumePct) {
    return false;
  }
  portENTER_CRITICAL(&mux_);
  volume_pct_ = pct;
  portEXIT_CRITICAL(&mux_);
  return true;
}

uint32_t AudioPlayback::ErrorCount() const {
  portENTER_CRITICAL(&mux_);
  const uint32_t v = i2s_errors_;
  portEXIT_CRITICAL(&mux_);
  return v;
}

uint32_t AudioPlayback::PartialWriteCount() const {
  portENTER_CRITICAL(&mux_);
  const uint32_t v = partial_writes_;
  portEXIT_CRITICAL(&mux_);
  return v;
}

int AudioPlayback::LastError() const {
  portENTER_CRITICAL(&mux_);
  const int v = last_err_;
  portEXIT_CRITICAL(&mux_);
  return v;
}

size_t AudioPlayback::BytesWritten() const {
  portENTER_CRITICAL(&mux_);
  const size_t v = bytes_written_;
  portEXIT_CRITICAL(&mux_);
  return v;
}

size_t AudioPlayback::FramesPlayed() const {
  portENTER_CRITICAL(&mux_);
  const size_t v = frame_idx_;
  portEXIT_CRITICAL(&mux_);
  return v;
}

uint32_t AudioPlayback::MaxWriteUs() const {
  portENTER_CRITICAL(&mux_);
  const uint32_t v = max_write_us_;
  portEXIT_CRITICAL(&mux_);
  return v;
}

uint32_t AudioPlayback::MaxInterWriteUs() const {
  portENTER_CRITICAL(&mux_);
  const uint32_t v = max_inter_write_us_;
  portEXIT_CRITICAL(&mux_);
  return v;
}

uint32_t AudioPlayback::InterGt30MsCount() const {
  portENTER_CRITICAL(&mux_);
  const uint32_t v = inter_gt_30ms_;
  portEXIT_CRITICAL(&mux_);
  return v;
}

uint32_t AudioPlayback::InterGt90MsCount() const {
  portENTER_CRITICAL(&mux_);
  const uint32_t v = inter_gt_90ms_;
  portEXIT_CRITICAL(&mux_);
  return v;
}

bool AudioPlayback::Start(const AudioBuffer& buffer) {
  if (!ready_ || task_handle_ == nullptr) {
    Serial.println(F("[AUDIO] ERR: TX non inizializzato"));
    return false;
  }
  if (buffer.SampleCount() == 0) {
    Serial.println(F("[AUDIO] WARN: buffer vuoto"));
    return false;
  }

  portENTER_CRITICAL(&mux_);
  if (playing_) {
    portEXIT_CRITICAL(&mux_);
    Serial.println(F("[AUDIO] WARN: riproduzione gia in corso"));
    return false;
  }
  active_buffer_ = &buffer;
  total_frames_ = buffer.SampleCount();
  frame_idx_ = 0;
  bytes_written_ = 0;
  active_volume_pct_ = volume_pct_;
  stop_requested_ = false;
  max_write_us_ = 0;
  max_inter_write_us_ = 0;
  inter_gt_30ms_ = 0;
  inter_gt_90ms_ = 0;
  playing_ = true;
  portEXIT_CRITICAL(&mux_);

  // Pulisce eventuale token residuo e sveglia il task audio
  xSemaphoreTake(done_sem_, 0);
  xTaskNotifyGive(task_handle_);

  Serial.printf("[AUDIO] Playback started (samples=%lu, dur=%lums, vol=%u%%)\n",
                static_cast<unsigned long>(total_frames_),
                static_cast<unsigned long>(buffer.DurationMs()),
                static_cast<unsigned>(active_volume_pct_));
  return true;
}

void AudioPlayback::Stop() {
  if (!IsPlaying()) {
    return;
  }

  portENTER_CRITICAL(&mux_);
  stop_requested_ = true;
  portEXIT_CRITICAL(&mux_);

  if (done_sem_ != nullptr) {
    xSemaphoreTake(done_sem_, pdMS_TO_TICKS(150));
  }

  Serial.printf("[AUDIO] Playback stopped (frames=%lu/%lu, bytes=%lu)\n",
                static_cast<unsigned long>(FramesPlayed()),
                static_cast<unsigned long>(total_frames_),
                static_cast<unsigned long>(BytesWritten()));
}

void AudioPlayback::Update(const AudioBuffer& /*buffer*/) {
  // La riproduzione I2S TX gira nel task FreeRTOS dedicato (AudioTxTask)
}

void AudioPlayback::WriteZeroFlush(size_t frames) {
  if (frames == 0U) {
    return;
  }

  memset(stereo_buf_, 0, sizeof(stereo_buf_));
  static constexpr uint8_t kMaxConsecutiveZeroWrites = 3U;
  uint8_t zero_write_retries = 0;
  size_t remaining = frames;

  while (remaining > 0U) {
    const size_t chunk_frames = (remaining < kChunkFrames) ? remaining : kChunkFrames;
    const size_t bytes_to_write = chunk_frames * 2U * sizeof(int16_t);

    const size_t written = i2s_tx_.write(reinterpret_cast<const uint8_t*>(stereo_buf_), bytes_to_write);
    const int err = i2s_tx_.lastError();

    portENTER_CRITICAL(&mux_);
    bytes_written_ += written;
    if (written != bytes_to_write) {
      partial_writes_++;
    }
    if (err != 0) {
      i2s_errors_++;
      last_err_ = err;
    }
    portEXIT_CRITICAL(&mux_);

    if (err != 0) {
      break;
    }
    if (written == 0U) {
      zero_write_retries++;
      if (zero_write_retries >= kMaxConsecutiveZeroWrites) {
        break;
      }
      continue;
    }

    zero_write_retries = 0;
    const size_t frames_written = written / (2U * sizeof(int16_t));
    if (frames_written == 0U) {
      break;
    }
    remaining = (frames_written < remaining) ? (remaining - frames_written) : 0U;
  }
}

void AudioPlayback::RunTaskLoop() {
  for (;;) {
    // Attende notifica di avvio (0% CPU a riposo, nessun busy-wait)
    ulTaskNotifyTake(pdTRUE, portMAX_DELAY);

    portENTER_CRITICAL(&mux_);
    const AudioBuffer* buf = active_buffer_;
    const size_t total = total_frames_;
    portEXIT_CRITICAL(&mux_);

    if (buf == nullptr || total == 0) {
      portENTER_CRITICAL(&mux_);
      playing_ = false;
      active_buffer_ = nullptr;
      portEXIT_CRITICAL(&mux_);
      xSemaphoreGive(done_sem_);
      continue;
    }

    const size_t fade = (total < (kFadeFrames * 2U)) ? (total / 4U) : kFadeFrames;
    size_t idx_base = 0;
    uint32_t last_write_end_us = 0;
    bool has_prev_end = false;

    while (idx_base < total) {
      portENTER_CRITICAL(&mux_);
      const bool stop_now = stop_requested_;
      const uint8_t vol = volume_pct_;
      portEXIT_CRITICAL(&mux_);
      if (stop_now) {
        break;
      }

      const size_t rem = total - idx_base;
      const size_t n = (rem < kChunkFrames) ? rem : kChunkFrames;

      for (size_t i = 0; i < n; ++i) {
        const size_t idx = idx_base + i;
        int16_t raw = 0;
        buf->ReadAt(idx, raw);

        int32_t scaled = (static_cast<int32_t>(raw) * static_cast<int32_t>(vol)) / 100;
        if (fade > 0) {
          if (idx < fade) {
            scaled = (scaled * static_cast<int32_t>(idx)) / static_cast<int32_t>(fade);
          } else if (idx >= (total - fade)) {
            const size_t tail = total - 1U - idx;
            scaled = (scaled * static_cast<int32_t>(tail)) / static_cast<int32_t>(fade);
          }
        }
        if (scaled > 32767) scaled = 32767;
        if (scaled < -32767) scaled = -32767;

        const int16_t sample = static_cast<int16_t>(scaled);
        stereo_buf_[2U * i] = sample;
        stereo_buf_[2U * i + 1U] = sample;
      }

      const size_t bytes_to_write = n * 2U * sizeof(int16_t);
      const uint32_t t_start_us = micros();
      if (has_prev_end) {
        const uint32_t inter_us = t_start_us - last_write_end_us;
        portENTER_CRITICAL(&mux_);
        if (inter_us > max_inter_write_us_) max_inter_write_us_ = inter_us;
        if (inter_us > 30000U) inter_gt_30ms_++;
        if (inter_us > 90000U) inter_gt_90ms_++;
        portEXIT_CRITICAL(&mux_);
      }

      const size_t written = i2s_tx_.write(reinterpret_cast<const uint8_t*>(stereo_buf_), bytes_to_write);
      const uint32_t t_end_us = micros();
      const uint32_t write_us = t_end_us - t_start_us;
      last_write_end_us = t_end_us;
      has_prev_end = true;
      const int err = i2s_tx_.lastError();

      idx_base += n;

      portENTER_CRITICAL(&mux_);
      bytes_written_ += written;
      frame_idx_ = idx_base;
      if (write_us > max_write_us_) max_write_us_ = write_us;
      if (written != bytes_to_write) partial_writes_++;
      if (err != 0) {
        i2s_errors_++;
        last_err_ = err;
      }
      portEXIT_CRITICAL(&mux_);
    }

    // Flush silenzioso finale (60 ms) anche su interruzione per evitare clic
    WriteZeroFlush(kSilenceFlushFrames);

    portENTER_CRITICAL(&mux_);
    playing_ = false;
    active_buffer_ = nullptr;
    portEXIT_CRITICAL(&mux_);
    xSemaphoreGive(done_sem_);
  }
}

}  // namespace jarvis::duplex

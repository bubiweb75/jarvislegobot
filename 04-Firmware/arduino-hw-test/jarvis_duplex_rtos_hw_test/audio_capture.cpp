#include "audio_capture.h"

#include <Arduino.h>
#include <limits.h>
#include <math.h>

#include "audio_buffer.h"

namespace jarvis::duplex {

void AudioCapture::TaskEntry(void* arg) {
  auto* self = static_cast<AudioCapture*>(arg);
  if (self != nullptr) {
    self->RunTaskLoop();
  }
  vTaskDelete(nullptr);
}

bool AudioCapture::Begin() {
  i2s_rx_.setPins(kI2sSckPin, kI2sWsPin, -1, kI2sSdPin, -1);
  if (!i2s_rx_.begin(I2S_MODE_STD,
                     kSampleRateHz,
                     I2S_DATA_BIT_WIDTH_32BIT,
                     I2S_SLOT_MODE_MONO,
                     I2S_STD_SLOT_LEFT)) {
    last_err_ = i2s_rx_.lastError();
    i2s_errors_++;
    ready_ = false;
    Serial.printf("[MIC] ERR: I2S0 RX begin() fallito (err=%d)\n", last_err_);
    return false;
  }

  done_sem_ = xSemaphoreCreateBinary();
  if (done_sem_ == nullptr) {
    ready_ = false;
    Serial.println(F("[MIC] ERR: creazione semaforo FreeRTOS RX fallita"));
    return false;
  }

  const BaseType_t ok = xTaskCreatePinnedToCore(
      TaskEntry,
      "jarvis_audio_rx",
      kTaskStackBytes,
      this,
      kTaskPriority,
      &task_handle_,
      kTaskCore);
  if (ok != pdPASS || task_handle_ == nullptr) {
    vSemaphoreDelete(done_sem_);
    done_sem_ = nullptr;
    ready_ = false;
    Serial.println(F("[MIC] ERR: creazione task FreeRTOS AudioRX fallita"));
    return false;
  }

  ready_ = true;
  Serial.printf("[MIC] I2S0 RX ready (RTOS task Core=%d Prio=%u, WS=GPIO%d SCK=GPIO%d SD=GPIO%d, 16kHz, shift=%d)\n",
                static_cast<int>(kTaskCore),
                static_cast<unsigned>(kTaskPriority),
                kI2sWsPin,
                kI2sSckPin,
                kI2sSdPin,
                kMicShiftBits);
  return true;
}

bool AudioCapture::IsRecording() const {
  portENTER_CRITICAL(&mux_);
  const bool r = recording_;
  portEXIT_CRITICAL(&mux_);
  return r;
}

uint32_t AudioCapture::ErrorCount() const {
  portENTER_CRITICAL(&mux_);
  const uint32_t v = i2s_errors_;
  portEXIT_CRITICAL(&mux_);
  return v;
}

int AudioCapture::LastError() const {
  portENTER_CRITICAL(&mux_);
  const int v = last_err_;
  portEXIT_CRITICAL(&mux_);
  return v;
}

size_t AudioCapture::CurrentSamples() const {
  portENTER_CRITICAL(&mux_);
  const size_t s = session_.samples;
  portEXIT_CRITICAL(&mux_);
  return s;
}

int16_t AudioCapture::CurrentPeak() const {
  portENTER_CRITICAL(&mux_);
  const int16_t p = session_.peak_abs_16;
  portEXIT_CRITICAL(&mux_);
  return p;
}

RxSessionStats AudioCapture::GetSessionStats() const {
  portENTER_CRITICAL(&mux_);
  RxSessionStats out = session_;
  portEXIT_CRITICAL(&mux_);
  return out;
}

bool AudioCapture::StartRecording(AudioBuffer& buffer, uint32_t max_duration_ms) {
  if (!ready_ || task_handle_ == nullptr || !buffer.IsAllocated()) {
    return false;
  }

  portENTER_CRITICAL(&mux_);
  if (recording_) {
    portEXIT_CRITICAL(&mux_);
    return false;
  }
  buffer.Clear();
  active_buffer_ = &buffer;
  max_duration_ms_ = max_duration_ms;
  stop_requested_ = false;
  recording_ = true;

  session_ = RxSessionStats{};
  session_.min_16 = INT16_MAX;
  session_.max_16 = INT16_MIN;
  rx_start_ms_ = millis();
  rx_end_ms_ = rx_start_ms_;
  rms_acc_sq_ = 0.0;
  dc_sum_ = 0;
  dc_blocks_ = 0;
  portEXIT_CRITICAL(&mux_);

  xSemaphoreTake(done_sem_, 0);
  xTaskNotifyGive(task_handle_);
  return true;
}

void AudioCapture::StopRecording() {
  if (!IsRecording()) {
    return;
  }
  portENTER_CRITICAL(&mux_);
  stop_requested_ = true;
  portEXIT_CRITICAL(&mux_);

  if (done_sem_ != nullptr) {
    xSemaphoreTake(done_sem_, pdMS_TO_TICKS(150));
  }
}

MicChunkStats AudioCapture::ReadChunk(int16_t* out_pcm16, size_t max_samples) {
  MicChunkStats stats{};
  if (!ready_ || out_pcm16 == nullptr || max_samples == 0) {
    stats.i2s_error = true;
    return stats;
  }

  const size_t n_req = (max_samples < kChunkSamples) ? max_samples : kChunkSamples;
  const size_t bytes_req = n_req * sizeof(int32_t);
  const size_t bytes_read = i2s_rx_.readBytes(reinterpret_cast<char*>(raw_buf_), bytes_req);
  const int err = i2s_rx_.lastError();

  if (bytes_read == 0) {
    stats.timeout_read = true;
  } else if (bytes_read < bytes_req) {
    stats.partial_read = true;
  }
  if (bytes_read == 0 || err != 0) {
    portENTER_CRITICAL(&mux_);
    i2s_errors_++;
    last_err_ = err;
    portEXIT_CRITICAL(&mux_);
    stats.i2s_error = true;
    stats.last_err = err;
  }

  const size_t n = bytes_read / sizeof(int32_t);
  if (n == 0) {
    return stats;
  }

  int64_t sum24 = 0;
  for (size_t i = 0; i < n; ++i) {
    sum24 += static_cast<int64_t>(raw_buf_[i] >> 8);
  }
  const int32_t dc_mean = static_cast<int32_t>(sum24 / static_cast<int64_t>(n));
  stats.dc_mean_24 = dc_mean;

  int16_t min_v = INT16_MAX;
  int16_t max_v = INT16_MIN;
  double sum_sq = 0.0;

  for (size_t i = 0; i < n; ++i) {
    const int32_t ac24 = (raw_buf_[i] >> 8) - dc_mean;
    int32_t scaled = ac24 >> kMicShiftBits;

    if (scaled > 32767) {
      scaled = 32767;
      stats.clipped++;
    } else if (scaled < -32767) {
      scaled = -32767;
      stats.clipped++;
    }

    const int16_t pcm16 = static_cast<int16_t>(scaled);
    out_pcm16[i] = pcm16;

    if (pcm16 < min_v) min_v = pcm16;
    if (pcm16 > max_v) max_v = pcm16;

    const int16_t abs_v = (pcm16 < 0) ? static_cast<int16_t>(-pcm16) : pcm16;
    if (abs_v > stats.peak_abs_16) {
      stats.peak_abs_16 = abs_v;
    }
    if (abs_v >= kSatThreshold16) {
      stats.saturated++;
    }
    const double d = static_cast<double>(pcm16);
    sum_sq += d * d;
  }

  stats.samples_read = n;
  stats.min_16 = min_v;
  stats.max_16 = max_v;
  stats.rms_16 = static_cast<uint16_t>(sqrt(sum_sq / static_cast<double>(n)));
  return stats;
}

void AudioCapture::RunTaskLoop() {
  for (;;) {
    ulTaskNotifyTake(pdTRUE, portMAX_DELAY);

    portENTER_CRITICAL(&mux_);
    AudioBuffer* buf = active_buffer_;
    const uint32_t limit_ms = max_duration_ms_;
    const uint32_t start_ms = rx_start_ms_;
    const uint32_t err_start = i2s_errors_;
    portEXIT_CRITICAL(&mux_);

    if (buf == nullptr) {
      portENTER_CRITICAL(&mux_);
      recording_ = false;
      portEXIT_CRITICAL(&mux_);
      xSemaphoreGive(done_sem_);
      continue;
    }

    uint32_t last_read_end_us = 0;
    bool has_prev_end = false;
    bool hit_timeout = false;
    bool hit_full = false;

    for (;;) {
      portENTER_CRITICAL(&mux_);
      const bool stop_now = stop_requested_;
      portEXIT_CRITICAL(&mux_);
      if (stop_now) {
        break;
      }

      if ((millis() - start_ms) >= limit_ms) {
        hit_timeout = true;
        break;
      }
      if (buf->SampleCount() >= buf->CapacitySamples()) {
        hit_full = true;
        break;
      }

      const uint32_t t_start_us = micros();
      if (has_prev_end) {
        const uint32_t inter_us = t_start_us - last_read_end_us;
        portENTER_CRITICAL(&mux_);
        if (inter_us > session_.max_inter_read_us) session_.max_inter_read_us = inter_us;
        if (inter_us > 30000U) session_.inter_gt_30ms++;
        if (inter_us > 90000U) session_.inter_gt_90ms++;
        portEXIT_CRITICAL(&mux_);
      }

      const MicChunkStats st = ReadChunk(task_pcm_buf_, kChunkSamples);
      last_read_end_us = micros();
      has_prev_end = true;

      if (st.samples_read > 0) {
        const size_t appended = buf->Append(task_pcm_buf_, st.samples_read);
        if (appended < st.samples_read) {
          hit_full = true;
        }
      }

      portENTER_CRITICAL(&mux_);
      if (st.samples_read > 0) {
        if (st.min_16 < session_.min_16) session_.min_16 = st.min_16;
        if (st.max_16 > session_.max_16) session_.max_16 = st.max_16;
        if (st.peak_abs_16 > session_.peak_abs_16) session_.peak_abs_16 = st.peak_abs_16;
        const double r = static_cast<double>(st.rms_16);
        rms_acc_sq_ += r * r * static_cast<double>(st.samples_read);
        dc_sum_ += static_cast<int64_t>(st.dc_mean_24);
        dc_blocks_++;
        session_.sat_count += st.saturated;
        session_.clipped += st.clipped;
        session_.samples = buf->SampleCount();
      }
      if (st.partial_read) session_.partial_reads++;
      if (st.timeout_read) session_.timeout_reads++;
      portEXIT_CRITICAL(&mux_);

      if (hit_full) {
        break;
      }
    }

    const uint32_t end_ms = millis();
    portENTER_CRITICAL(&mux_);
    rx_end_ms_ = end_ms;
    session_.elapsed_ms = end_ms - start_ms;
    session_.duration_ms = buf->DurationMs();
    session_.samples = buf->SampleCount();
    session_.rx_errors = i2s_errors_ - err_start;
    session_.stopped_by_timeout = hit_timeout;
    session_.stopped_by_buffer_full = hit_full;
    if (session_.samples > 0) {
      session_.rms_16 = static_cast<uint32_t>(sqrt(rms_acc_sq_ / static_cast<double>(session_.samples)));
    } else {
      session_.min_16 = 0;
      session_.max_16 = 0;
    }
    if (dc_blocks_ > 0) {
      session_.dc_mean_24 = static_cast<int32_t>(dc_sum_ / static_cast<int64_t>(dc_blocks_));
    }
    recording_ = false;
    active_buffer_ = nullptr;
    portEXIT_CRITICAL(&mux_);

    xSemaphoreGive(done_sem_);
  }
}

}  // namespace jarvis::duplex

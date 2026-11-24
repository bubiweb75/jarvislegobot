#include "audio_playback.h"

#include <Arduino.h>
#include <string.h>

#include "audio_buffer.h"

namespace jarvis::duplex {

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

  ready_ = true;
  playing_ = false;
  flushing_ = false;
  Serial.printf("[AUDIO] I2S1 TX ready (BCLK=GPIO%d LRC=GPIO%d DIN=GPIO%d, 16kHz, vol=%u%%)\n",
                kI2sBclkPin,
                kI2sLrcPin,
                kI2sDinPin,
                static_cast<unsigned>(volume_pct_));
  return true;
}

bool AudioPlayback::SetVolumePct(uint8_t pct) {
  if (pct < kMinVolumePct || pct > kMaxVolumePct) {
    return false;
  }
  volume_pct_ = pct;
  return true;
}

bool AudioPlayback::Start(const AudioBuffer& buffer) {
  if (!ready_) {
    Serial.println(F("[AUDIO] ERR: TX non inizializzato"));
    return false;
  }
  if (playing_) {
    Serial.println(F("[AUDIO] WARN: riproduzione gia in corso"));
    return false;
  }
  if (buffer.SampleCount() == 0) {
    Serial.println(F("[AUDIO] WARN: buffer vuoto"));
    return false;
  }

  frame_idx_ = 0;
  total_frames_ = buffer.SampleCount();
  flush_idx_ = 0;
  bytes_written_ = 0;
  flushing_ = false;
  max_write_us_ = 0;
  max_inter_write_us_ = 0;
  inter_gt_30ms_ = 0;
  inter_gt_90ms_ = 0;
  last_write_end_us_ = 0;
  has_prev_write_end_ = false;
  playing_ = true;
  Serial.printf("[AUDIO] Playback started (samples=%lu, dur=%lums, vol=%u%%)\n",
                static_cast<unsigned long>(total_frames_),
                static_cast<unsigned long>(buffer.DurationMs()),
                static_cast<unsigned>(volume_pct_));
  return true;
}

void AudioPlayback::WriteZeroFlush(size_t frames) {
  memset(stereo_buf_, 0, frames * 2U * sizeof(int16_t));
  const size_t bytes_to_write = frames * 2U * sizeof(int16_t);
  const size_t written = i2s_tx_.write(reinterpret_cast<const uint8_t*>(stereo_buf_), bytes_to_write);
  const int err = i2s_tx_.lastError();
  bytes_written_ += written;
  if (written != bytes_to_write) {
    partial_writes_++;
  }
  if (err != 0) {
    i2s_errors_++;
    last_err_ = err;
  }
}

void AudioPlayback::Stop() {
  if (!playing_) {
    return;
  }
  playing_ = false;
  flushing_ = false;
  if (ready_) {
    WriteZeroFlush(kChunkFrames);
  }
  Serial.printf("[AUDIO] Playback stopped (frames=%lu/%lu, bytes=%lu)\n",
                static_cast<unsigned long>(frame_idx_),
                static_cast<unsigned long>(total_frames_),
                static_cast<unsigned long>(bytes_written_));
}

void AudioPlayback::Update(const AudioBuffer& buffer) {
  if (!ready_ || !playing_) {
    return;
  }

  if (!flushing_) {
    const size_t remaining = (frame_idx_ < total_frames_) ? (total_frames_ - frame_idx_) : 0;
    if (remaining == 0) {
      flushing_ = true;
      flush_idx_ = 0;
    } else {
      const size_t n = (remaining < kChunkFrames) ? remaining : kChunkFrames;
      const size_t fade = (total_frames_ < (kFadeFrames * 2U))
                              ? (total_frames_ / 4U)
                              : kFadeFrames;

      for (size_t i = 0; i < n; ++i) {
        const size_t idx = frame_idx_ + i;
        int16_t raw = 0;
        buffer.ReadAt(idx, raw);

        int32_t scaled = (static_cast<int32_t>(raw) * static_cast<int32_t>(volume_pct_)) / 100;
        if (fade > 0) {
          if (idx < fade) {
            scaled = (scaled * static_cast<int32_t>(idx)) / static_cast<int32_t>(fade);
          } else if (idx >= (total_frames_ - fade)) {
            const size_t tail = total_frames_ - 1U - idx;
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
      if (has_prev_write_end_) {
        const uint32_t inter_us = t_start_us - last_write_end_us_;
        if (inter_us > max_inter_write_us_) max_inter_write_us_ = inter_us;
        if (inter_us > 30000U) inter_gt_30ms_++;
        if (inter_us > 90000U) inter_gt_90ms_++;
      }
      const size_t written = i2s_tx_.write(reinterpret_cast<const uint8_t*>(stereo_buf_), bytes_to_write);
      const uint32_t t_end_us = micros();
      const uint32_t write_us = t_end_us - t_start_us;
      if (write_us > max_write_us_) max_write_us_ = write_us;
      last_write_end_us_ = t_end_us;
      has_prev_write_end_ = true;
      const int err = i2s_tx_.lastError();
      bytes_written_ += written;
      if (written != bytes_to_write) {
        partial_writes_++;
      }
      if (err != 0) {
        i2s_errors_++;
        last_err_ = err;
        Serial.printf("[AUDIO] ERR: I2S1 write err=%d (%lu/%lu)\n",
                      err,
                      static_cast<unsigned long>(written),
                      static_cast<unsigned long>(bytes_to_write));
      }

      frame_idx_ += n;
      if (frame_idx_ >= total_frames_) {
        flushing_ = true;
        flush_idx_ = 0;
      }
      return;
    }
  }

  if (flushing_) {
    const size_t rem_sil = kSilenceFlushFrames - flush_idx_;
    if (rem_sil == 0) {
      playing_ = false;
      flushing_ = false;
      Serial.printf("[AUDIO] Playback completed (bytes=%lu, partial=%lu, err=%lu)\n",
                    static_cast<unsigned long>(bytes_written_),
                    static_cast<unsigned long>(partial_writes_),
                    static_cast<unsigned long>(i2s_errors_));
      return;
    }
    const size_t n = (rem_sil < kChunkFrames) ? rem_sil : kChunkFrames;
    WriteZeroFlush(n);
    flush_idx_ += n;
  }
}

}  // namespace jarvis::duplex

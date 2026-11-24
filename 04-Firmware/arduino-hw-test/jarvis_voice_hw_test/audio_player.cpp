#include "audio_player.h"

#include <Arduino.h>
#include <pgmspace.h>
#include <string.h>

#include "generated/jarvis_voice_pcm.h"

namespace jarvis::voice {

size_t AudioPlayer::TotalFrames() const {
  return kJarvisVoiceNumSamples;
}

uint32_t AudioPlayer::SampleRateHz() const {
  return kJarvisVoiceSampleRateHz;
}

bool AudioPlayer::Begin() {
  i2s_.setPins(kI2sBclkPin, kI2sLrcPin, kI2sDinPin, -1, -1);
  if (!i2s_.begin(I2S_MODE_STD,
                  kJarvisVoiceSampleRateHz,
                  I2S_DATA_BIT_WIDTH_16BIT,
                  I2S_SLOT_MODE_STEREO,
                  I2S_STD_SLOT_BOTH)) {
    last_err_ = i2s_.lastError();
    i2s_errors_++;
    ready_ = false;
    Serial.printf("ERR:AUDIO_INIT_FAIL lastError=%d\n", last_err_);
    return false;
  }

  ready_ = true;
  playing_ = false;
  flushing_ = false;
  Serial.printf("AUDIO:READY BCLK=GPIO%d LRC=GPIO%d DIN=GPIO%d SR=%luHz VOL=%u%%\n",
                kI2sBclkPin,
                kI2sLrcPin,
                kI2sDinPin,
                static_cast<unsigned long>(kJarvisVoiceSampleRateHz),
                static_cast<unsigned>(volume_pct_));
  return true;
}

bool AudioPlayer::SetVolumePct(uint8_t pct) {
  if (pct < kMinVolumePct || pct > kMaxVolumePct) {
    return false;
  }
  volume_pct_ = pct;
  return true;
}

bool AudioPlayer::Start() {
  if (!ready_) {
    Serial.println(F("ERR:AUDIO_NOT_READY"));
    return false;
  }
  if (playing_) {
    Serial.println(F("AUDIO:BUSY (riproduzione gia in corso)"));
    return false;
  }

  frame_idx_ = 0;
  flush_idx_ = 0;
  bytes_written_ = 0;
  flushing_ = false;
  playing_ = true;
  Serial.printf("AUDIO:START samples=%lu vol=%u%%\n",
                static_cast<unsigned long>(kJarvisVoiceNumSamples),
                static_cast<unsigned>(volume_pct_));
  return true;
}

void AudioPlayer::WriteZeroFlush(size_t frames) {
  memset(stereo_buf_, 0, frames * 2U * sizeof(int16_t));
  const size_t bytes_to_write = frames * 2U * sizeof(int16_t);
  const size_t written = i2s_.write(reinterpret_cast<const uint8_t*>(stereo_buf_), bytes_to_write);
  const int err = i2s_.lastError();
  bytes_written_ += written;
  if (written != bytes_to_write || err != 0) {
    i2s_errors_++;
    last_err_ = err;
  }
}

void AudioPlayer::Stop() {
  if (!playing_) {
    return;
  }
  playing_ = false;
  flushing_ = false;
  if (ready_) {
    WriteZeroFlush(kChunkFrames);
  }
  Serial.printf("AUDIO:STOPPED frames=%lu/%lu bytes=%lu errors=%lu\n",
                static_cast<unsigned long>(frame_idx_),
                static_cast<unsigned long>(kJarvisVoiceNumSamples),
                static_cast<unsigned long>(bytes_written_),
                static_cast<unsigned long>(i2s_errors_));
}

void AudioPlayer::Update() {
  if (!ready_ || !playing_) {
    return;
  }

  if (!flushing_) {
    const size_t remaining = kJarvisVoiceNumSamples - frame_idx_;
    if (remaining == 0) {
      flushing_ = true;
      flush_idx_ = 0;
    } else {
      const size_t n = (remaining < kChunkFrames) ? remaining : kChunkFrames;
      for (size_t i = 0; i < n; ++i) {
        const size_t idx = frame_idx_ + i;
        const int16_t raw = static_cast<int16_t>(pgm_read_word(&kJarvisVoicePcm[idx]));

        // Applicazione volume conservativo + fade-in / fade-out (20 ms)
        int32_t scaled = (static_cast<int32_t>(raw) * static_cast<int32_t>(volume_pct_)) / 100;
        if (idx < kFadeFrames) {
          scaled = (scaled * static_cast<int32_t>(idx)) / static_cast<int32_t>(kFadeFrames);
        } else if (idx >= (kJarvisVoiceNumSamples - kFadeFrames)) {
          const size_t tail = kJarvisVoiceNumSamples - 1U - idx;
          scaled = (scaled * static_cast<int32_t>(tail)) / static_cast<int32_t>(kFadeFrames);
        }

        const int16_t sample = static_cast<int16_t>(scaled);
        stereo_buf_[2U * i] = sample;
        stereo_buf_[2U * i + 1U] = sample;
      }

      const size_t bytes_to_write = n * 2U * sizeof(int16_t);
      const size_t written = i2s_.write(reinterpret_cast<const uint8_t*>(stereo_buf_), bytes_to_write);
      const int err = i2s_.lastError();
      bytes_written_ += written;
      if (written != bytes_to_write || err != 0) {
        i2s_errors_++;
        last_err_ = err;
        Serial.printf("ERR:I2S_WRITE written=%lu/%lu err=%d\n",
                      static_cast<unsigned long>(written),
                      static_cast<unsigned long>(bytes_to_write),
                      err);
      }
      frame_idx_ += n;
      if (frame_idx_ >= kJarvisVoiceNumSamples) {
        flushing_ = true;
        flush_idx_ = 0;
      }
      return;
    }
  }

  // Flush finale silenzioso (60 ms)
  if (flushing_) {
    const size_t rem_sil = kSilenceFlushFrames - flush_idx_;
    if (rem_sil == 0) {
      playing_ = false;
      flushing_ = false;
      Serial.printf("AUDIO:DONE frames=%lu bytes=%lu errors=%lu(last=%d)\n",
                    static_cast<unsigned long>(frame_idx_),
                    static_cast<unsigned long>(bytes_written_),
                    static_cast<unsigned long>(i2s_errors_),
                    last_err_);
      return;
    }
    const size_t n = (rem_sil < kChunkFrames) ? rem_sil : kChunkFrames;
    WriteZeroFlush(n);
    flush_idx_ += n;
  }
}

}  // namespace jarvis::voice

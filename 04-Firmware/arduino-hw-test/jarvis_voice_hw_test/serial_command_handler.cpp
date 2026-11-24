#include "serial_command_handler.h"

#include <Arduino.h>
#include <ctype.h>
#include <stdlib.h>
#include <string.h>

#include "audio_player.h"
#include "eye_controller.h"
#include "pinout_config.h"

namespace jarvis::voice {

void SerialCommandHandler::Begin(AudioPlayer& audio, EyeController& eyes) {
  audio_ = &audio;
  eyes_ = &eyes;
  rx_len_ = 0;
}

void SerialCommandHandler::Poll() {
  while (Serial.available() > 0) {
    const char ch = static_cast<char>(Serial.read());
    if (ch == '\n' || ch == '\r') {
      if (rx_len_ > 0) {
        rx_buf_[rx_len_] = '\0';
        HandleLine(rx_buf_);
        rx_len_ = 0;
      }
    } else if (rx_len_ < (kRxBufSize - 1U)) {
      rx_buf_[rx_len_++] = ch;
    } else {
      rx_len_ = 0;
    }
  }
}

void SerialCommandHandler::PrintHelp() const {
  Serial.println(F("COMANDI: HELP | SPEAK | STOP | STATUS | VOLUME | VOLUME:<1..15>"));
}

void SerialCommandHandler::PrintStatus() const {
  if (audio_ == nullptr || eyes_ == nullptr) return;
  const size_t pcm_bytes = audio_->TotalFrames() * sizeof(int16_t);
  const float dur_s = static_cast<float>(audio_->TotalFrames()) /
                      static_cast<float>(audio_->SampleRateHz());

  Serial.printf(
      "STATUS: AUDIO=%s(%s) | FMT=%luHz_16bit_MONO_TO_STEREO | PCM=%lu_samples(%luB,%.2fs) | VOL=%u%%(max=%u%%) | I2S_ERR=%lu(last=%d) | OLED=0x%02X(%s) | BTN=GPIO%u\n",
      audio_->IsReady() ? "READY" : "ERR",
      audio_->IsPlaying() ? "PLAYING" : "IDLE",
      static_cast<unsigned long>(audio_->SampleRateHz()),
      static_cast<unsigned long>(audio_->TotalFrames()),
      static_cast<unsigned long>(pcm_bytes),
      static_cast<double>(dur_s),
      static_cast<unsigned>(audio_->VolumePct()),
      static_cast<unsigned>(AudioPlayer::kMaxVolumePct),
      static_cast<unsigned long>(audio_->ErrorCount()),
      audio_->LastError(),
      eyes_->DetectedOledAddr(),
      eyes_->CurrentExpressionName(),
      pins::kButtonActivate);
}

void SerialCommandHandler::HandleLine(const char* raw_line) {
  if (audio_ == nullptr || eyes_ == nullptr) return;

  char cmd[kRxBufSize];
  strncpy(cmd, raw_line, kRxBufSize - 1U);
  cmd[kRxBufSize - 1U] = '\0';

  size_t len = strlen(cmd);
  while (len > 0 && (cmd[len - 1] == ' ' || cmd[len - 1] == '\t')) {
    cmd[--len] = '\0';
  }
  for (size_t i = 0; i < len; ++i) {
    cmd[i] = static_cast<char>(toupper(static_cast<unsigned char>(cmd[i])));
  }
  if (cmd[0] == '\0') return;

  if (strcmp(cmd, "HELP") == 0) {
    PrintHelp();
  } else if (strcmp(cmd, "SPEAK") == 0) {
    audio_->Start();
  } else if (strcmp(cmd, "STOP") == 0) {
    audio_->Stop();
  } else if (strcmp(cmd, "STATUS") == 0) {
    PrintStatus();
  } else if (strcmp(cmd, "VOLUME") == 0) {
    Serial.printf("VOLUME=%u%% (range conservativo: %u..%u%%)\n",
                  static_cast<unsigned>(audio_->VolumePct()),
                  static_cast<unsigned>(AudioPlayer::kMinVolumePct),
                  static_cast<unsigned>(AudioPlayer::kMaxVolumePct));
  } else if (strncmp(cmd, "VOLUME:", 7) == 0) {
    const long val = strtol(cmd + 7, nullptr, 10);
    if (val < static_cast<long>(AudioPlayer::kMinVolumePct) ||
        val > static_cast<long>(AudioPlayer::kMaxVolumePct)) {
      Serial.printf("ERR:VOLUME_RANGE (%u..%u%% consentito)\n",
                    static_cast<unsigned>(AudioPlayer::kMinVolumePct),
                    static_cast<unsigned>(AudioPlayer::kMaxVolumePct));
    } else {
      audio_->SetVolumePct(static_cast<uint8_t>(val));
      Serial.printf("OK:VOLUME=%u%%\n", static_cast<unsigned>(audio_->VolumePct()));
    }
  } else {
    Serial.printf("ERR:UNKNOWN_CMD=%s\n", cmd);
  }
}

}  // namespace jarvis::voice

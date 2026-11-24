#include "serial_commands.h"

#include <Arduino.h>
#include <ctype.h>
#include <stdlib.h>
#include <string.h>

#include "audio_buffer.h"
#include "audio_capture.h"
#include "audio_playback.h"
#include "eye_controller.h"
#include "state_machine.h"

namespace jarvis::duplex {

void SerialCommands::Begin(StateMachine& sm,
                           AudioBuffer& buffer,
                           AudioCapture& capture,
                           AudioPlayback& playback,
                           EyeController& eyes) {
  sm_ = &sm;
  buffer_ = &buffer;
  capture_ = &capture;
  playback_ = &playback;
  eyes_ = &eyes;
  rx_len_ = 0;
}

void SerialCommands::Poll(uint32_t now_ms) {
  while (Serial.available() > 0) {
    const char ch = static_cast<char>(Serial.read());
    if (ch == '\n' || ch == '\r') {
      if (rx_len_ > 0) {
        rx_buf_[rx_len_] = '\0';
        HandleLine(rx_buf_, now_ms);
        rx_len_ = 0;
      }
    } else if (rx_len_ < (kRxBufSize - 1U)) {
      rx_buf_[rx_len_++] = ch;
    } else {
      rx_len_ = 0;
    }
  }
}

void SerialCommands::PrintHelp() const {
  Serial.println(F("COMANDI: HELP | STATUS | MIC_TEST | RECORD | STOP | PLAY | VOLUME | VOLUME:<1..15> | MEMORY | AUDIO_INFO"));
}

void SerialCommands::PrintStatus() const {
  Serial.printf(
      "[STATUS] STATE=%s | EYES=%s(OLED=0x%02X) | MIC=%s(err=%lu) | SPK=%s(vol=%u%%,err=%lu) | REC=%lu/%lu(%lums)\n",
      sm_->StateName(),
      eyes_->CurrentExpressionName(),
      eyes_->DetectedOledAddr(),
      capture_->IsReady() ? "OK" : "ERR",
      static_cast<unsigned long>(capture_->ErrorCount()),
      playback_->IsReady() ? "OK" : "ERR",
      static_cast<unsigned>(playback_->VolumePct()),
      static_cast<unsigned long>(playback_->ErrorCount()),
      static_cast<unsigned long>(buffer_->SampleCount()),
      static_cast<unsigned long>(buffer_->CapacitySamples()),
      static_cast<unsigned long>(buffer_->DurationMs()));
}

void SerialCommands::PrintMemory() const {
  Serial.printf(
      "[MEMORY] FREE_HEAP=%lu B | FREE_PSRAM=%lu B | PSRAM_FOUND=%s | AUDIO_BUF=%lu B (%s)\n",
      static_cast<unsigned long>(ESP.getFreeHeap()),
      static_cast<unsigned long>(ESP.getFreePsram()),
      psramFound() ? "YES" : "NO",
      static_cast<unsigned long>(buffer_->CapacityBytes()),
      buffer_->UsedPsram() ? "PSRAM" : "RAM");
}

void SerialCommands::PrintAudioInfo() const {
  Serial.printf(
      "[AUDIO_INFO] SR=%luHz | RX=I2S0_32to16bit_MONO_L | TX=I2S1_16bit_STEREO_DUP | SAMPLES=%lu | DUR=%lums | PEAK=%d | CLIP=%lu\n",
      static_cast<unsigned long>(AudioBuffer::kSampleRateHz),
      static_cast<unsigned long>(buffer_->SampleCount()),
      static_cast<unsigned long>(buffer_->DurationMs()),
      static_cast<int>(sm_->LastPeakLevel()),
      static_cast<unsigned long>(sm_->LastClipCount()));
}

void SerialCommands::HandleLine(const char* raw_line, uint32_t now_ms) {
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
  } else if (strcmp(cmd, "STATUS") == 0) {
    PrintStatus();
  } else if (strcmp(cmd, "MIC_TEST") == 0) {
    sm_->StartMicTestCommand(now_ms);
  } else if (strcmp(cmd, "RECORD") == 0) {
    sm_->StartRecordCommand(now_ms);
  } else if (strcmp(cmd, "STOP") == 0) {
    sm_->StopCommand(now_ms);
  } else if (strcmp(cmd, "PLAY") == 0) {
    sm_->StartPlayCommand(now_ms);
  } else if (strcmp(cmd, "VOLUME") == 0) {
    Serial.printf("[VOLUME] %u%% (range consentito: %u..%u%%)\n",
                  static_cast<unsigned>(playback_->VolumePct()),
                  static_cast<unsigned>(AudioPlayback::kMinVolumePct),
                  static_cast<unsigned>(AudioPlayback::kMaxVolumePct));
  } else if (strncmp(cmd, "VOLUME:", 7) == 0) {
    const long v = strtol(cmd + 7, nullptr, 10);
    if (v < static_cast<long>(AudioPlayback::kMinVolumePct) ||
        v > static_cast<long>(AudioPlayback::kMaxVolumePct)) {
      Serial.printf("[VOLUME] ERR: range consentito %u..%u%%\n",
                    static_cast<unsigned>(AudioPlayback::kMinVolumePct),
                    static_cast<unsigned>(AudioPlayback::kMaxVolumePct));
    } else {
      playback_->SetVolumePct(static_cast<uint8_t>(v));
      Serial.printf("[VOLUME] OK: %u%%\n", static_cast<unsigned>(playback_->VolumePct()));
    }
  } else if (strcmp(cmd, "MEMORY") == 0) {
    PrintMemory();
  } else if (strcmp(cmd, "AUDIO_INFO") == 0) {
    PrintAudioInfo();
  } else {
    Serial.printf("[SERIAL] Comando sconosciuto: %s (usa HELP)\n", cmd);
  }
}

}  // namespace jarvis::duplex

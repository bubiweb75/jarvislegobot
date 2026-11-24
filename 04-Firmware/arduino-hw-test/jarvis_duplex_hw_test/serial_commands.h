#pragma once

#include <stdint.h>

namespace jarvis::duplex {

class AudioBuffer;
class AudioCapture;
class AudioPlayback;
class EyeController;
class StateMachine;

class SerialCommands {
public:
  void Begin(StateMachine& sm,
             AudioBuffer& buffer,
             AudioCapture& capture,
             AudioPlayback& playback,
             EyeController& eyes);
  void Poll(uint32_t now_ms);

private:
  static constexpr uint8_t kRxBufSize = 48;
  StateMachine* sm_ = nullptr;
  AudioBuffer* buffer_ = nullptr;
  AudioCapture* capture_ = nullptr;
  AudioPlayback* playback_ = nullptr;
  EyeController* eyes_ = nullptr;

  char rx_buf_[kRxBufSize] = {};
  uint8_t rx_len_ = 0;

  void HandleLine(const char* raw_line, uint32_t now_ms);
  void PrintHelp() const;
  void PrintStatus() const;
  void PrintMemory() const;
  void PrintAudioInfo() const;
};

}  // namespace jarvis::duplex

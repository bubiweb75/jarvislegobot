#pragma once

#include <stdint.h>

namespace jarvis::voice {

class AudioPlayer;
class EyeController;

class SerialCommandHandler {
public:
  void Begin(AudioPlayer& audio, EyeController& eyes);
  void Poll();

private:
  static constexpr uint8_t kRxBufSize = 48;
  AudioPlayer* audio_ = nullptr;
  EyeController* eyes_ = nullptr;
  char rx_buf_[kRxBufSize] = {};
  uint8_t rx_len_ = 0;

  void HandleLine(const char* raw_line);
  void PrintHelp() const;
  void PrintStatus() const;
};

}  // namespace jarvis::voice

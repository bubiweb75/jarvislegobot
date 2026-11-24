#pragma once

#include <stddef.h>
#include <stdint.h>

namespace jarvis::wifi_voice {

enum class RobotState : uint8_t {
  kIdle = 0,
  kWifiConnecting,
  kWifiConnected,
  kRecording,
  kUploading,
  kProcessing,
  kReceiving,
  kPlaying,
  kError,
  kCancelled,
};

const char* RobotStateName(RobotState s);

struct WsControlMessage {
  char type[24] = {};
  char request_id[40] = {};
  char code[32] = {};
  uint32_t sample_rate = 16000;
  uint8_t channels = 1;
  uint8_t bits = 16;
  uint32_t total_bytes = 0;
  uint32_t max_audio_bytes = 256000;
  uint32_t max_tts_bytes = 640000;
  uint32_t chunk_bytes = 2048;
};

size_t BuildAuthJson(char* out, size_t cap, const char* device_id, const char* token);
size_t BuildPingJson(char* out, size_t cap, uint32_t ts_ms);
size_t BuildAudioStartJson(char* out, size_t cap, const char* request_id, uint32_t sr, uint8_t ch, uint8_t bits);
size_t BuildAudioEndJson(char* out, size_t cap, const char* request_id, uint32_t samples);
size_t BuildCancelJson(char* out, size_t cap, const char* request_id);

bool ParseControlMessage(const char* json, size_t len, WsControlMessage& out);

}  // namespace jarvis::wifi_voice

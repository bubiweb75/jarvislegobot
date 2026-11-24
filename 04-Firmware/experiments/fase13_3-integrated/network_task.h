#pragma once

#include <stddef.h>
#include <stdint.h>
#include "ws_protocol.h"

namespace jarvis::wifi_voice {

struct NetworkConfig {
  const char* ssid = "";
  const char* password = "";
  const char* host = "";
  uint16_t port = 8765;
  const char* ws_path = "/ws/v1/esp32";
  const char* device_id = "jarvis-lego-01";
  const char* device_token = "";
  bool use_tls = false;
  bool allow_insecure_lan_ws = false;
  const char* ca_cert = "";
};

enum class NetEventType : uint8_t {
  kNone = 0,
  kWifiConnecting,
  kWifiConnected,
  kWsAuthenticated,
  kWsDisconnected,
  kTtsReady,
  kTtsError,
  kCancelled,
};

struct NetEvent {
  NetEventType type = NetEventType::kNone;
  uint32_t tts_bytes = 0;
  char code[32] = {};
};

class NetworkBridgeClient {
public:
  static constexpr size_t kMaxTtsPsramBytes = 640000U;  // 20 s @ 16 kHz PCM16 mono
  static constexpr uint32_t kHeartbeatIntervalMs = 15000U;
  static constexpr uint32_t kReconnectBaseMs = 1000U;
  static constexpr uint32_t kReconnectMaxMs = 15000U;

  bool Begin(const NetworkConfig& cfg);
  void Stop();

  // Called by Core 1 robot state machine (non-blocking).
  bool SubmitVoiceUpload(const int16_t* pcm16, size_t sample_count, const char* request_id);
  bool RequestCancel(const char* request_id);
  bool PollEvent(NetEvent& out_event);

  bool IsWifiConnected() const;
  bool IsWsAuthenticated() const;
  const int16_t* TtsBuffer() const { return tts_buf_; }
  size_t TtsSampleCount() const;
  void ReleaseTtsBuffer();

private:
  NetworkConfig cfg_{};
  int16_t* tts_buf_ = nullptr;
  size_t tts_bytes_expected_ = 0;
  size_t tts_bytes_received_ = 0;
  bool receiving_tts_ = false;
};

}  // namespace jarvis::wifi_voice

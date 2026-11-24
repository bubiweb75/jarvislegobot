#include "ws_protocol.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

namespace jarvis::wifi_voice {

const char* RobotStateName(RobotState s) {
  switch (s) {
    case RobotState::kIdle:           return "IDLE";
    case RobotState::kWifiConnecting: return "WIFI_CONNECTING";
    case RobotState::kWifiConnected:  return "WIFI_CONNECTED";
    case RobotState::kRecording:      return "RECORDING";
    case RobotState::kUploading:      return "UPLOADING";
    case RobotState::kProcessing:     return "PROCESSING";
    case RobotState::kReceiving:      return "RECEIVING";
    case RobotState::kPlaying:        return "PLAYING";
    case RobotState::kError:          return "ERROR";
    case RobotState::kCancelled:      return "CANCELLED";
    default:                          return "UNKNOWN";
  }
}

static bool ExtractJsonString(const char* json, const char* key, char* out, size_t cap) {
  char pattern[48];
  snprintf(pattern, sizeof(pattern), "\"%s\"", key);
  const char* p = strstr(json, pattern);
  if (!p) return false;
  p += strlen(pattern);
  while (*p == ' ' || *p == ':' || *p == '\t') ++p;
  if (*p != '"') return false;
  ++p;
  size_t i = 0;
  while (*p && *p != '"' && i + 1 < cap) {
    if (*p == '\\' && *(p + 1)) ++p;
    out[i++] = *p++;
  }
  out[i] = '\0';
  return true;
}

static bool ExtractJsonUInt(const char* json, const char* key, uint32_t& out) {
  char pattern[48];
  snprintf(pattern, sizeof(pattern), "\"%s\"", key);
  const char* p = strstr(json, pattern);
  if (!p) return false;
  p += strlen(pattern);
  while (*p == ' ' || *p == ':' || *p == '\t') ++p;
  if (*p < '0' || *p > '9') return false;
  out = static_cast<uint32_t>(strtoul(p, nullptr, 10));
  return true;
}

size_t BuildAuthJson(char* out, size_t cap, const char* device_id, const char* token) {
  return static_cast<size_t>(snprintf(
      out, cap,
      "{\"v\":\"1.0\",\"type\":\"auth\",\"device_id\":\"%s\",\"token\":\"%s\"}",
      device_id ? device_id : "", token ? token : ""));
}

size_t BuildPingJson(char* out, size_t cap, uint32_t ts_ms) {
  return static_cast<size_t>(snprintf(
      out, cap, "{\"v\":\"1.0\",\"type\":\"ping\",\"ts\":%lu}", static_cast<unsigned long>(ts_ms)));
}

size_t BuildAudioStartJson(char* out, size_t cap, const char* request_id, uint32_t sr, uint8_t ch, uint8_t bits) {
  return static_cast<size_t>(snprintf(
      out, cap,
      "{\"v\":\"1.0\",\"type\":\"audio_start\",\"request_id\":\"%s\",\"sr\":%lu,\"ch\":%u,\"bits\":%u}",
      request_id ? request_id : "", static_cast<unsigned long>(sr), ch, bits));
}

size_t BuildAudioEndJson(char* out, size_t cap, const char* request_id, uint32_t samples) {
  return static_cast<size_t>(snprintf(
      out, cap,
      "{\"v\":\"1.0\",\"type\":\"audio_end\",\"request_id\":\"%s\",\"samples\":%lu}",
      request_id ? request_id : "", static_cast<unsigned long>(samples)));
}

size_t BuildCancelJson(char* out, size_t cap, const char* request_id) {
  return static_cast<size_t>(snprintf(
      out, cap,
      "{\"v\":\"1.0\",\"type\":\"cancel\",\"request_id\":\"%s\"}",
      request_id ? request_id : ""));
}

bool ParseControlMessage(const char* json, size_t len, WsControlMessage& out) {
  if (!json || len == 0) return false;
  out = WsControlMessage{};
  if (!ExtractJsonString(json, "type", out.type, sizeof(out.type))) return false;
  ExtractJsonString(json, "request_id", out.request_id, sizeof(out.request_id));
  ExtractJsonString(json, "code", out.code, sizeof(out.code));
  ExtractJsonUInt(json, "sr", out.sample_rate);
  ExtractJsonUInt(json, "total_bytes", out.total_bytes);
  ExtractJsonUInt(json, "max_audio_bytes", out.max_audio_bytes);
  ExtractJsonUInt(json, "max_tts_bytes", out.max_tts_bytes);
  ExtractJsonUInt(json, "chunk_bytes", out.chunk_bytes);
  return true;
}

}  // namespace jarvis::wifi_voice

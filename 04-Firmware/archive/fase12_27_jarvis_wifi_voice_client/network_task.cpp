#include "network_task.h"

#include <Arduino.h>
#include <WiFi.h>
#include <WebSocketsClient.h>
#include <esp_heap_caps.h>
#include <freertos/FreeRTOS.h>
#include <freertos/queue.h>
#include <freertos/task.h>
#include <string.h>

namespace jarvis::wifi_voice {

namespace {

enum class TxCmdType : uint8_t {
  kUpload = 1,
  kCancel = 2,
};

struct TxCommand {
  TxCmdType type = TxCmdType::kUpload;
  const int16_t* pcm16 = nullptr;
  size_t sample_count = 0;
  char request_id[40] = {};
};

WebSocketsClient g_ws;
QueueHandle_t g_tx_queue = nullptr;
QueueHandle_t g_ev_queue = nullptr;
TaskHandle_t g_net_task = nullptr;
volatile bool g_wifi_connected = false;
volatile bool g_ws_connected = false;
volatile bool g_ws_authed = false;
volatile bool g_running = false;

NetworkBridgeClient* g_client_instance = nullptr;
NetworkConfig g_cfg{};
int16_t* g_tts_buf = nullptr;
size_t g_tts_expected = 0;
size_t g_tts_received = 0;
bool g_receiving_tts = false;
uint32_t g_chunk_bytes = 2048U;

void PushEvent(NetEventType t, uint32_t bytes = 0, const char* code = nullptr) {
  if (!g_ev_queue) return;
  NetEvent ev{};
  ev.type = t;
  ev.tts_bytes = bytes;
  if (code) {
    strncpy(ev.code, code, sizeof(ev.code) - 1);
  }
  xQueueSend(g_ev_queue, &ev, 0);
}

void OnWsEvent(WStype_t type, uint8_t* payload, size_t length) {
  switch (type) {
    case WStype_DISCONNECTED:
      g_ws_connected = false;
      g_ws_authed = false;
      g_receiving_tts = false;
      PushEvent(NetEventType::kWsDisconnected);
      break;

    case WStype_CONNECTED: {
      g_ws_connected = true;
      g_ws_authed = false;
      char auth_buf[256];
      size_t n = BuildAuthJson(auth_buf, sizeof(auth_buf), g_cfg.device_id, g_cfg.device_token);
      g_ws.sendTXT(auth_buf, n);
      break;
    }

    case WStype_TEXT: {
      WsControlMessage msg{};
      if (!ParseControlMessage(reinterpret_cast<const char*>(payload), length, msg)) {
        break;
      }
      if (strcmp(msg.type, "auth_ok") == 0) {
        g_ws_authed = true;
        if (msg.chunk_bytes >= 512U && msg.chunk_bytes <= 8192U) {
          g_chunk_bytes = msg.chunk_bytes;
        }
        PushEvent(NetEventType::kWsAuthenticated);
      } else if (strcmp(msg.type, "tts_start") == 0) {
        if (msg.total_bytes > NetworkBridgeClient::kMaxTtsPsramBytes || !g_tts_buf) {
          g_receiving_tts = false;
          PushEvent(NetEventType::kTtsError, 0, "TTS_TOO_LONG");
        } else {
          g_tts_expected = msg.total_bytes;
          g_tts_received = 0;
          g_receiving_tts = true;
        }
      } else if (strcmp(msg.type, "tts_end") == 0) {
        g_receiving_tts = false;
        PushEvent(NetEventType::kTtsReady, static_cast<uint32_t>(g_tts_received));
      } else if (strcmp(msg.type, "cancelled") == 0) {
        g_receiving_tts = false;
        g_tts_received = 0;
        PushEvent(NetEventType::kCancelled);
      } else if (strcmp(msg.type, "error") == 0) {
        g_receiving_tts = false;
        PushEvent(NetEventType::kTtsError, 0, msg.code);
      }
      break;
    }

    case WStype_BIN:
      if (g_receiving_tts && g_tts_buf && (g_tts_received + length <= NetworkBridgeClient::kMaxTtsPsramBytes)) {
        memcpy(reinterpret_cast<uint8_t*>(g_tts_buf) + g_tts_received, payload, length);
        g_tts_received += length;
      } else if (g_receiving_tts) {
        g_receiving_tts = false;
        PushEvent(NetEventType::kTtsError, 0, "PSRAM_OVERFLOW");
      }
      break;

    default:
      break;
  }
}

void NetworkTaskMain(void* /*arg*/) {
  uint32_t last_ping_ms = 0;
  uint32_t backoff_ms = NetworkBridgeClient::kReconnectBaseMs;
  uint32_t next_reconnect_ms = 0;
  bool ws_started = false;

  WiFi.mode(WIFI_STA);
  WiFi.begin(g_cfg.ssid, g_cfg.password);
  PushEvent(NetEventType::kWifiConnecting);

  while (g_running) {
    uint32_t now = millis();
    bool wifi_ok = (WiFi.status() == WL_CONNECTED);
    if (wifi_ok && !g_wifi_connected) {
      g_wifi_connected = true;
      backoff_ms = NetworkBridgeClient::kReconnectBaseMs;
      PushEvent(NetEventType::kWifiConnected);
    } else if (!wifi_ok && g_wifi_connected) {
      g_wifi_connected = false;
      g_ws_connected = false;
      g_ws_authed = false;
      ws_started = false;
      PushEvent(NetEventType::kWsDisconnected);
    }

    if (wifi_ok && !ws_started && now >= next_reconnect_ms) {
      g_ws.onEvent(OnWsEvent);
      g_ws.setReconnectInterval(backoff_ms);
      if (g_cfg.use_tls && g_cfg.ca_cert && g_cfg.ca_cert[0] != '\0') {
        g_ws.beginSslWithCA(g_cfg.host, g_cfg.port, g_cfg.ws_path, g_cfg.ca_cert);
        ws_started = true;
      } else if (g_cfg.allow_insecure_lan_ws) {
        g_ws.begin(g_cfg.host, g_cfg.port, g_cfg.ws_path);
        ws_started = true;
      } else {
        PushEvent(NetEventType::kTtsError, 0, "TLS_REQUIRED");
        next_reconnect_ms = now + backoff_ms;
      }
      backoff_ms = (backoff_ms * 2U <= NetworkBridgeClient::kReconnectMaxMs)
                       ? (backoff_ms * 2U)
                       : NetworkBridgeClient::kReconnectMaxMs;
    }

    if (ws_started) {
      g_ws.loop();
    }

    if (g_ws_authed && (now - last_ping_ms >= NetworkBridgeClient::kHeartbeatIntervalMs)) {
      last_ping_ms = now;
      char ping_buf[96];
      size_t pn = BuildPingJson(ping_buf, sizeof(ping_buf), now);
      g_ws.sendTXT(ping_buf, pn);
    }

    TxCommand cmd{};
    if (xQueueReceive(g_tx_queue, &cmd, 0) == pdTRUE) {
      if (!g_ws_authed) {
        PushEvent(NetEventType::kTtsError, 0, "WS_NOT_READY");
      } else if (cmd.type == TxCmdType::kCancel) {
        char cancel_buf[128];
        size_t cn = BuildCancelJson(cancel_buf, sizeof(cancel_buf), cmd.request_id);
        g_ws.sendTXT(cancel_buf, cn);
      } else if (cmd.type == TxCmdType::kUpload && cmd.pcm16 && cmd.sample_count > 0) {
        char start_buf[192];
        size_t sn = BuildAudioStartJson(start_buf, sizeof(start_buf), cmd.request_id, 16000U, 1U, 16U);
        g_ws.sendTXT(start_buf, sn);

        const uint8_t* raw = reinterpret_cast<const uint8_t*>(cmd.pcm16);
        size_t total_bytes = cmd.sample_count * sizeof(int16_t);
        for (size_t off = 0; off < total_bytes; off += g_chunk_bytes) {
          size_t n = (total_bytes - off < g_chunk_bytes) ? (total_bytes - off) : g_chunk_bytes;
          g_ws.sendBIN(raw + off, n);
          g_ws.loop();
          vTaskDelay(pdMS_TO_TICKS(1));
        }

        char end_buf[160];
        size_t en = BuildAudioEndJson(end_buf, sizeof(end_buf), cmd.request_id, static_cast<uint32_t>(cmd.sample_count));
        g_ws.sendTXT(end_buf, en);
      }
    }

    vTaskDelay(pdMS_TO_TICKS(5));
  }

  g_ws.disconnect();
  vTaskDelete(nullptr);
}

}  // namespace

bool NetworkBridgeClient::Begin(const NetworkConfig& cfg) {
  g_cfg = cfg;
  g_client_instance = this;
  tts_buf_ = static_cast<int16_t*>(heap_caps_malloc(kMaxTtsPsramBytes, MALLOC_CAP_SPIRAM | MALLOC_CAP_8BIT));
  if (!tts_buf_) {
    return false;
  }
  g_tts_buf = tts_buf_;
  g_tx_queue = xQueueCreate(4, sizeof(TxCommand));
  g_ev_queue = xQueueCreate(8, sizeof(NetEvent));
  if (!g_tx_queue || !g_ev_queue) {
    return false;
  }
  g_running = true;
  BaseType_t ok = xTaskCreatePinnedToCore(
      NetworkTaskMain, "jarvis_net", 8192U, nullptr, 1U, &g_net_task, 1);  // Core 1, low priority vs Core 0 I2S
  return ok == pdPASS;
}

void NetworkBridgeClient::Stop() {
  g_running = false;
  if (tts_buf_) {
    heap_caps_free(tts_buf_);
    tts_buf_ = nullptr;
    g_tts_buf = nullptr;
  }
}

bool NetworkBridgeClient::SubmitVoiceUpload(const int16_t* pcm16, size_t sample_count, const char* request_id) {
  if (!g_tx_queue || !g_ws_authed) return false;
  TxCommand cmd{};
  cmd.type = TxCmdType::kUpload;
  cmd.pcm16 = pcm16;
  cmd.sample_count = sample_count;
  strncpy(cmd.request_id, request_id ? request_id : "", sizeof(cmd.request_id) - 1);
  return xQueueSend(g_tx_queue, &cmd, 0) == pdTRUE;
}

bool NetworkBridgeClient::RequestCancel(const char* request_id) {
  if (!g_tx_queue || !g_ws_authed) return false;
  TxCommand cmd{};
  cmd.type = TxCmdType::kCancel;
  strncpy(cmd.request_id, request_id ? request_id : "", sizeof(cmd.request_id) - 1);
  return xQueueSend(g_tx_queue, &cmd, 0) == pdTRUE;
}

bool NetworkBridgeClient::PollEvent(NetEvent& out_event) {
  if (!g_ev_queue) return false;
  return xQueueReceive(g_ev_queue, &out_event, 0) == pdTRUE;
}

bool NetworkBridgeClient::IsWifiConnected() const { return g_wifi_connected; }
bool NetworkBridgeClient::IsWsAuthenticated() const { return g_ws_authed; }
size_t NetworkBridgeClient::TtsSampleCount() const { return g_tts_received / sizeof(int16_t); }
void NetworkBridgeClient::ReleaseTtsBuffer() { g_tts_received = 0; g_tts_expected = 0; }

}  // namespace jarvis::wifi_voice

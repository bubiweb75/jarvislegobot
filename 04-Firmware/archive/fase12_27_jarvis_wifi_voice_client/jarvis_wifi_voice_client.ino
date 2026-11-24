// =============================================================================
// JARVIS LEGO BOT — FASE 11.3A/11.3B: Isolated Wi-Fi WebSocket Voice Client
// Board: ESP32-S3-DevKitC-1 N16R8
// Reuses Core 0 FreeRTOS I2S RX/TX + Eyes 3.0 + GPIO47 from FASE 10.8.
// NOTE: Do NOT flash without FASE 11.3B/11.3C authorization.
// =============================================================================

#include <Arduino.h>

#if __has_include("wifi_secrets.h")
#include "wifi_secrets.h"
#else
#include "wifi_secrets.example.h"
#endif

#include "audio_buffer.h"
#include "audio_capture.h"
#include "audio_playback.h"
#include "button_controller.h"
#include "eye_controller.h"
#include "network_task.h"
#include "ws_protocol.h"

using namespace jarvis::duplex;
using namespace jarvis::wifi_voice;

namespace {

constexpr uint32_t kMaxRecordMs = 8000U;
static_assert(AudioBuffer::kPrimaryCapacitySamples == (AudioBuffer::kSampleRateHz * (kMaxRecordMs / 1000U)),
              "RX buffer capacity must match kMaxRecordMs");
constexpr size_t kMinValidSamples = 4800U;  // 300 ms @ 16 kHz
constexpr size_t kTtsBufferSamples = NetworkBridgeClient::kMaxTtsPsramBytes / sizeof(int16_t);

AudioBuffer g_rx_buffer;
AudioBuffer g_tx_buffer;
AudioCapture g_capture;
AudioPlayback g_playback;
EyeController g_eyes;
ButtonController g_button;
NetworkBridgeClient g_net;

RobotState g_state = RobotState::kWifiConnecting;
uint32_t g_state_enter_ms = 0;
uint32_t g_req_seq = 0;
char g_active_req_id[40] = {};
char g_serial_line[48] = {};
size_t g_serial_len = 0;

void HandleSerialLine(const char* line) {
  if (!line || line[0] == '\0') return;
  if (strncmp(line, "VOL", 3) == 0 && (line[3] == ' ' || line[3] == '\t' || line[3] == '\0')) {
    const char* p = line + 3;
    while (*p == ' ' || *p == '\t') ++p;
    if (*p < '0' || *p > '9') {
      Serial.printf("[AUDIO] ERR: uso VOL <1..25> (corrente=%u%%)\n", static_cast<unsigned>(g_playback.VolumePct()));
      return;
    }
    long val = 0;
    while (*p >= '0' && *p <= '9') {
      val = val * 10L + (*p - '0');
      if (val > 100L) break;
      ++p;
    }
    while (*p == ' ' || *p == '\t') ++p;
    if (*p != '\0' || val < 1L || val > 25L) {
      Serial.printf("[AUDIO] ERR: valore volume non valido (1..25, corrente=%u%%)\n",
                    static_cast<unsigned>(g_playback.VolumePct()));
      return;
    }
    if (g_playback.SetVolumePct(static_cast<uint8_t>(val))) {
      Serial.printf("[AUDIO] Volume impostato a %u%%\n", static_cast<unsigned>(g_playback.VolumePct()));
    }
    return;
  }
  Serial.printf("[SERIAL] Comando sconosciuto (disponibile: VOL <1..25>, corrente=%u%%)\n",
                static_cast<unsigned>(g_playback.VolumePct()));
}

void PollSerialCommands() {
  while (Serial.available() > 0) {
    const int ch = Serial.read();
    if (ch < 0) break;
    if (ch == '\r' || ch == '\n') {
      if (g_serial_len > 0) {
        g_serial_line[g_serial_len] = '\0';
        HandleSerialLine(g_serial_line);
        g_serial_len = 0;
      }
    } else if (g_serial_len + 1U < sizeof(g_serial_line)) {
      g_serial_line[g_serial_len++] = static_cast<char>(ch);
    } else {
      g_serial_len = 0;
    }
  }
}

void NextRequestId() {
  ++g_req_seq;
  snprintf(g_active_req_id, sizeof(g_active_req_id), "esp-%lu", static_cast<unsigned long>(g_req_seq));
}

SystemState MapToEyeState(RobotState s) {
  switch (s) {
    case RobotState::kRecording:
      return SystemState::kListening;
    case RobotState::kUploading:
    case RobotState::kProcessing:
    case RobotState::kReceiving:
      return SystemState::kProcessing;
    case RobotState::kPlaying:
      return SystemState::kPlaying;
    case RobotState::kError:
      return SystemState::kError;
    default:
      return SystemState::kIdle;
  }
}

void TransitionState(RobotState next, uint32_t now_ms) {
  if (g_state == next) return;
  g_state = next;
  g_state_enter_ms = now_ms;
  g_eyes.ApplyState(MapToEyeState(next), now_ms);
  Serial.printf("[STATE] -> %s\n", RobotStateName(next));
}

}  // namespace

void setup() {
  Serial.begin(115200);
  delay(200);
  Serial.println(F("[FASE 11.3B] JARVIS Wi-Fi Voice Client (isolated)"));

  if (!g_rx_buffer.Allocate() || !g_tx_buffer.AllocateWithCapacity(kTtsBufferSamples, 16000U)) {
    Serial.println(F("[ERR] PSRAM audio buffer allocation failed"));
    TransitionState(RobotState::kError, millis());
    return;
  }
  g_button.Begin();
  if (!g_eyes.Begin() || !g_capture.Begin() || !g_playback.Begin()) {
    Serial.println(F("[ERR] Hardware driver init failed"));
    TransitionState(RobotState::kError, millis());
    return;
  }

  NetworkConfig cfg{};
  cfg.ssid = JARVIS_WIFI_SSID;
  cfg.password = JARVIS_WIFI_PASSWORD;
  cfg.host = JARVIS_BRIDGE_HOST;
  cfg.port = JARVIS_BRIDGE_PORT;
  cfg.ws_path = JARVIS_BRIDGE_WS_PATH;
  cfg.device_id = JARVIS_ESP_DEVICE_ID;
  cfg.device_token = JARVIS_ESP_TOKEN;
  cfg.use_tls = (JARVIS_WS_USE_TLS != 0);
  cfg.allow_insecure_lan_ws = (JARVIS_ALLOW_INSECURE_LAN_WS != 0);
  cfg.ca_cert = JARVIS_WS_CA_CERT;

  if (!g_net.Begin(cfg)) {
    Serial.println(F("[ERR] NetworkTask init failed"));
    TransitionState(RobotState::kError, millis());
    return;
  }

  TransitionState(RobotState::kWifiConnecting, millis());
}

void loop() {
  const uint32_t now_ms = millis();

  // 1. Poll non-blocking Core 1 NetworkTask events
  NetEvent ev{};
  while (g_net.PollEvent(ev)) {
    switch (ev.type) {
      case NetEventType::kWifiConnecting:
        if (g_state != RobotState::kPlaying) TransitionState(RobotState::kWifiConnecting, now_ms);
        break;
      case NetEventType::kWifiConnected:
        if (g_state == RobotState::kWifiConnecting) TransitionState(RobotState::kWifiConnected, now_ms);
        break;
      case NetEventType::kWsAuthenticated:
        if (g_state == RobotState::kWifiConnecting || g_state == RobotState::kWifiConnected) {
          TransitionState(RobotState::kIdle, now_ms);
        }
        break;
      case NetEventType::kWsDisconnected:
        g_capture.StopRecording();
        g_playback.Stop();
        TransitionState(RobotState::kWifiConnecting, now_ms);
        break;
      case NetEventType::kTtsReady: {
        g_tx_buffer.Clear();
        const size_t n = g_net.TtsSampleCount();
        g_tx_buffer.Append(g_net.TtsBuffer(), n);
        g_net.ReleaseTtsBuffer();
        if (g_tx_buffer.SampleCount() > 0 && g_playback.Start(g_tx_buffer)) {
          TransitionState(RobotState::kPlaying, now_ms);
        } else {
          TransitionState(RobotState::kError, now_ms);
        }
        break;
      }
      case NetEventType::kCancelled:
        TransitionState(RobotState::kCancelled, now_ms);
        TransitionState(RobotState::kIdle, now_ms);
        break;
      case NetEventType::kTtsError:
        Serial.printf("[NET] Error: %s\n", ev.code);
        TransitionState(RobotState::kError, now_ms);
        break;
      default:
        break;
    }
  }

  // 2. GPIO47 Push-to-Talk & STOP/CANCEL
  g_button.Update(now_ms);
  if (g_button.ConsumePressedEdge()) {
    if (g_state == RobotState::kIdle && g_net.IsWsAuthenticated()) {
      g_rx_buffer.Clear();
      if (g_capture.StartRecording(g_rx_buffer, kMaxRecordMs)) {
        TransitionState(RobotState::kRecording, now_ms);
      } else {
        TransitionState(RobotState::kError, now_ms);
      }
    } else if (g_state == RobotState::kUploading || g_state == RobotState::kProcessing ||
               g_state == RobotState::kReceiving || g_state == RobotState::kPlaying) {
      g_playback.Stop();
      g_net.RequestCancel(g_active_req_id);
      TransitionState(RobotState::kCancelled, now_ms);
      TransitionState(RobotState::kIdle, now_ms);
    }
  } else if (g_button.ConsumeReleasedEdge() && g_state == RobotState::kRecording) {
    g_capture.StopRecording();
    if (g_rx_buffer.SampleCount() >= kMinValidSamples && g_rx_buffer.Data() != nullptr) {
      NextRequestId();
      if (g_net.SubmitVoiceUpload(g_rx_buffer.Data(), g_rx_buffer.SampleCount(), g_active_req_id)) {
        TransitionState(RobotState::kUploading, now_ms);
      } else {
        TransitionState(RobotState::kError, now_ms);
      }
    } else {
      TransitionState(RobotState::kIdle, now_ms);
    }
  }

  // Auto-stop recording if 5 s limit reached
  if (g_state == RobotState::kRecording && !g_capture.IsRecording()) {
    if (g_rx_buffer.SampleCount() >= kMinValidSamples && g_rx_buffer.Data() != nullptr) {
      NextRequestId();
      if (g_net.SubmitVoiceUpload(g_rx_buffer.Data(), g_rx_buffer.SampleCount(), g_active_req_id)) {
        TransitionState(RobotState::kUploading, now_ms);
      } else {
        TransitionState(RobotState::kError, now_ms);
      }
    } else {
      TransitionState(RobotState::kIdle, now_ms);
    }
  }

  // 3. Playback completion & error auto-recovery
  if (g_state == RobotState::kPlaying) {
    g_playback.Update(g_tx_buffer);
    if (!g_playback.IsPlaying()) {
      TransitionState(RobotState::kIdle, now_ms);
    }
  } else if (g_state == RobotState::kError && (now_ms - g_state_enter_ms >= 2000U)) {
    TransitionState(g_net.IsWsAuthenticated() ? RobotState::kIdle : RobotState::kWifiConnecting, now_ms);
  }

  // 4. Non-blocking Eyes 3.0 OLED animation & serial VOL command
  PollSerialCommands();
  g_eyes.Update(now_ms);
  delay(5);
}

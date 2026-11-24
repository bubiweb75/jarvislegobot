#pragma once

// Copy this file to wifi_secrets.h (do NOT commit real credentials to Git).
// Real SSID, password, and device token must never be stored in versioned files.

#define JARVIS_WIFI_SSID       "YOUR_WIFI_SSID"
#define JARVIS_WIFI_PASSWORD   "YOUR_WIFI_PASSWORD"

#define JARVIS_BRIDGE_HOST     "192.168.1.100"
#define JARVIS_BRIDGE_PORT     8765
#define JARVIS_BRIDGE_WS_PATH  "/ws/v1/esp32"

// Dedicated device token (JARVIS_ESP_DEVICE_TOKEN), separate from browser token.
#define JARVIS_ESP_DEVICE_ID   "jarvis-lego-01"
#define JARVIS_ESP_TOKEN       "REPLACE_WITH_JARVIS_ESP_DEVICE_TOKEN"

// Security: prefer WSS with local CA certificate (JARVIS_WS_USE_TLS 1).
// Defining JARVIS_ALLOW_INSECURE_LAN_WS=1 is strictly for isolated LAN dev testing
// after explicit user authorization (token is sent unencrypted on LAN in ws://).
#define JARVIS_WS_USE_TLS             0
#define JARVIS_ALLOW_INSECURE_LAN_WS  0
#define JARVIS_WS_CA_CERT             ""

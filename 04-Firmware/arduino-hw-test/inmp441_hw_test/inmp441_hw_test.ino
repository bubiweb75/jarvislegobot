// =============================================================================
// JARVIS LEGO BOT — FASE 10.3: Diagnostica Estesa Microfono I2S INMP441
// Target: Espressif ESP32-S3-DevKitC-1 N16R8 (Arduino-ESP32 3.3.12 / ESP_I2S)
// Collegamenti:
//   VDD -> 3V3 | GND -> GND | L/R -> GND (Left)
//   WS  -> GPIO4 | SCK -> GPIO5 | SD -> GPIO6
//
// Comandi Serial Monitor (115200 baud):
//   STEREO  -> Acquisizione I2S_SLOT_MODE_STEREO (confronta LEFT [pari] vs RIGHT [dispari])
//   MONO_L  -> Acquisizione I2S_SLOT_MODE_MONO + I2S_STD_SLOT_LEFT
//   MONO_R  -> Acquisizione I2S_SLOT_MODE_MONO + I2S_STD_SLOT_RIGHT
//   HELP    -> Mostra i comandi disponibili
// =============================================================================

#include <Arduino.h>
#include <ESP_I2S.h>
#include <ctype.h>
#include <limits.h>
#include <math.h>
#include <stdint.h>
#include <string.h>

namespace {

constexpr int8_t kI2sWsPin = 4;
constexpr int8_t kI2sSckPin = 5;
constexpr int8_t kI2sSdPin = 6;

constexpr uint32_t kSampleRateHz = 16000;
constexpr size_t kBlockSamples = 512;          // 512 word da 32-bit (in STEREO = 256 coppie L/R)
constexpr uint32_t kReportIntervalMs = 500;    // Stampa ogni 500 ms
constexpr int32_t kSatThreshold24 = 7000000;   // Soglia prossima alla saturazione 24-bit (+/-8388607)

enum class DiagMode : uint8_t {
  kMonoLeft = 0,
  kMonoRight = 1,
  kStereo = 2,
};

// Costante di compilazione per la modalità iniziale
constexpr DiagMode kDefaultDiagMode = DiagMode::kStereo;

struct ChannelStats {
  uint32_t count = 0;
  int32_t min_val = INT32_MAX;
  int32_t max_val = INT32_MIN;
  int64_t sum = 0;
  double sum_sq = 0.0;
  uint32_t sat_count = 0;
  int32_t peak_abs = 0;
  uint32_t raw_hex[4] = {0, 0, 0, 0};
  uint8_t raw_hex_count = 0;

  void Reset() {
    count = 0;
    min_val = INT32_MAX;
    max_val = INT32_MIN;
    sum = 0;
    sum_sq = 0.0;
    sat_count = 0;
    peak_abs = 0;
    raw_hex_count = 0;
    for (uint8_t i = 0; i < 4; ++i) {
      raw_hex[i] = 0;
    }
  }

  void AddSample(int32_t raw32) {
    if (raw_hex_count < 4) {
      raw_hex[raw_hex_count++] = static_cast<uint32_t>(raw32);
    }
    const int32_t s24 = raw32 >> 8;  // Estrazione 24-bit signed (MSB-aligned in slot 32-bit)
    if (s24 < min_val) min_val = s24;
    if (s24 > max_val) max_val = s24;
    sum += static_cast<int64_t>(s24);

    const int64_t abs64 = (s24 < 0) ? -static_cast<int64_t>(s24) : static_cast<int64_t>(s24);
    if (abs64 >= kSatThreshold24) {
      sat_count++;
    }
    count++;
  }
};

// Buffer per rimozione DC esatta sulla finestra corrente (fino a 512 campioni per blocco)
int32_t g_raw_buffer[kBlockSamples];

I2SClass g_i2s;
DiagMode g_mode = kDefaultDiagMode;
ChannelStats g_left_stats;
ChannelStats g_right_stats;

uint32_t g_last_report_ms = 0;
uint32_t g_i2s_errors = 0;
int g_last_i2s_err = 0;

char g_rx_buf[32];
uint8_t g_rx_len = 0;

const char* ModeName(DiagMode m) {
  switch (m) {
    case DiagMode::kMonoLeft: return "MONO_L";
    case DiagMode::kMonoRight: return "MONO_R";
    case DiagMode::kStereo: return "STEREO";
  }
  return "UNKNOWN";
}

bool StartI2sMode(DiagMode mode) {
  g_i2s.end();
  g_i2s.setPins(kI2sSckPin, kI2sWsPin, -1, kI2sSdPin, -1);

  i2s_slot_mode_t slot_mode = I2S_SLOT_MODE_MONO;
  int8_t slot_mask = I2S_STD_SLOT_LEFT;
  if (mode == DiagMode::kMonoRight) {
    slot_mode = I2S_SLOT_MODE_MONO;
    slot_mask = I2S_STD_SLOT_RIGHT;
  } else if (mode == DiagMode::kStereo) {
    // In Arduino-ESP32 3.3.12 (ESP32-S3, ws_pol=false):
    // indice pari (0,2,4...) = LEFT (WS LOW), indice dispari (1,3,5...) = RIGHT (WS HIGH)
    slot_mode = I2S_SLOT_MODE_STEREO;
    slot_mask = I2S_STD_SLOT_BOTH;
  }

  if (!g_i2s.begin(I2S_MODE_STD,
                   kSampleRateHz,
                   I2S_DATA_BIT_WIDTH_32BIT,
                   slot_mode,
                   slot_mask)) {
    Serial.printf("ERRORE: I2S begin(%s) fallito (lastError=%d)\n",
                  ModeName(mode), g_i2s.lastError());
    return false;
  }

  g_mode = mode;
  g_left_stats.Reset();
  g_right_stats.Reset();
  g_i2s_errors = 0;
  g_last_i2s_err = 0;
  g_last_report_ms = millis();
  Serial.printf("MODE=%s attiva (16kHz, 32bit slot)\n", ModeName(g_mode));
  return true;
}

void PrintChannelLine(const char* label, const ChannelStats& st, uint32_t i2s_err, int last_err) {
  if (st.count == 0) {
    Serial.printf("[%s] SAMPLES=0 | I2S_ERR=%lu (last=%d)\n",
                  label, static_cast<unsigned long>(i2s_err), last_err);
    return;
  }

  const int32_t dc_mean = static_cast<int32_t>(st.sum / static_cast<int64_t>(st.count));
  const uint32_t rms = static_cast<uint32_t>(sqrt(st.sum_sq / static_cast<double>(st.count)));
  const double sat_pct = (100.0 * static_cast<double>(st.sat_count)) / static_cast<double>(st.count);

  Serial.printf(
      "[%s] MIN=%ld | MAX=%ld | DC=%ld | RMS=%lu | PEAK=%ld | SAT=%.1f%% | SAMPLES=%lu | I2S_ERR=%lu(last=%d) | HEX=0x%08lX,0x%08lX,0x%08lX,0x%08lX\n",
      label,
      static_cast<long>(st.min_val),
      static_cast<long>(st.max_val),
      static_cast<long>(dc_mean),
      static_cast<unsigned long>(rms),
      static_cast<long>(st.peak_abs),
      sat_pct,
      static_cast<unsigned long>(st.count),
      static_cast<unsigned long>(i2s_err),
      last_err,
      static_cast<unsigned long>(st.raw_hex[0]),
      static_cast<unsigned long>(st.raw_hex[1]),
      static_cast<unsigned long>(st.raw_hex[2]),
      static_cast<unsigned long>(st.raw_hex[3]));
}

void AccumulateBlock(const int32_t* buf, size_t count, size_t start_idx, size_t step, ChannelStats& st) {
  if (count <= start_idx) return;

  int64_t blk_sum = 0;
  size_t blk_n = 0;
  for (size_t i = start_idx; i < count; i += step) {
    const int32_t raw32 = buf[i];
    st.AddSample(raw32);
    blk_sum += static_cast<int64_t>(raw32 >> 8);
    blk_n++;
  }
  if (blk_n == 0) return;

  const int64_t blk_mean = blk_sum / static_cast<int64_t>(blk_n);
  for (size_t i = start_idx; i < count; i += step) {
    const int64_t ac = static_cast<int64_t>(buf[i] >> 8) - blk_mean;
    const double ac_d = static_cast<double>(ac);
    st.sum_sq += ac_d * ac_d;
    const int32_t abs_val = static_cast<int32_t>(ac < 0 ? -ac : ac);
    if (abs_val > st.peak_abs) {
      st.peak_abs = abs_val;
    }
  }
}

void PollSerial() {
  while (Serial.available() > 0) {
    const char ch = static_cast<char>(Serial.read());
    if (ch == '\n' || ch == '\r') {
      if (g_rx_len > 0) {
        g_rx_buf[g_rx_len] = '\0';
        for (uint8_t i = 0; i < g_rx_len; ++i) {
          g_rx_buf[i] = static_cast<char>(toupper(static_cast<unsigned char>(g_rx_buf[i])));
        }
        if (strcmp(g_rx_buf, "STEREO") == 0) {
          StartI2sMode(DiagMode::kStereo);
        } else if (strcmp(g_rx_buf, "MONO_L") == 0) {
          StartI2sMode(DiagMode::kMonoLeft);
        } else if (strcmp(g_rx_buf, "MONO_R") == 0) {
          StartI2sMode(DiagMode::kMonoRight);
        } else if (strcmp(g_rx_buf, "HELP") == 0) {
          Serial.println(F("Comandi: STEREO | MONO_L | MONO_R | HELP"));
        } else {
          Serial.printf("Comando sconosciuto: %s (usa STEREO, MONO_L, MONO_R, HELP)\n", g_rx_buf);
        }
        g_rx_len = 0;
      }
    } else if (g_rx_len < (sizeof(g_rx_buf) - 1)) {
      g_rx_buf[g_rx_len++] = ch;
    } else {
      g_rx_len = 0;
    }
  }
}

}  // namespace

void setup() {
  Serial.begin(115200);
  const uint32_t wait_start = millis();
  while (!Serial && (millis() - wait_start) < 1200U) {
  }

  Serial.println();
  Serial.println(F("=== JARVIS FASE 10.3 — Diagnostica Estesa INMP441 ==="));
  Serial.printf("Pin I2S: WS=GPIO%d, SCK=GPIO%d, SD=GPIO%d | L/R=GND\n",
                kI2sWsPin, kI2sSckPin, kI2sSdPin);
  Serial.println(F("Comandi seriali: STEREO | MONO_L | MONO_R | HELP"));

  if (!StartI2sMode(kDefaultDiagMode)) {
    while (true) {
      delay(1000);
    }
  }
}

void loop() {
  PollSerial();

  const size_t bytes_read = g_i2s.readBytes(reinterpret_cast<char*>(g_raw_buffer), sizeof(g_raw_buffer));
  const int err = g_i2s.lastError();
  if (bytes_read == 0 || err != 0) {
    g_i2s_errors++;
    g_last_i2s_err = err;
  }

  const size_t count = bytes_read / sizeof(int32_t);
  if (count > 0) {
    if (g_mode == DiagMode::kStereo) {
      AccumulateBlock(g_raw_buffer, count, 0, 2, g_left_stats);   // Slot 0 = LEFT (WS LOW)
      AccumulateBlock(g_raw_buffer, count, 1, 2, g_right_stats);  // Slot 1 = RIGHT (WS HIGH)
    } else if (g_mode == DiagMode::kMonoLeft) {
      AccumulateBlock(g_raw_buffer, count, 0, 1, g_left_stats);
    } else {
      AccumulateBlock(g_raw_buffer, count, 0, 1, g_right_stats);
    }
  }

  const uint32_t now_ms = millis();
  if ((now_ms - g_last_report_ms) >= kReportIntervalMs) {
    g_last_report_ms = now_ms;

    if (g_mode == DiagMode::kStereo) {
      PrintChannelLine("LEFT ", g_left_stats, g_i2s_errors, g_last_i2s_err);
      PrintChannelLine("RIGHT", g_right_stats, g_i2s_errors, g_last_i2s_err);
      g_left_stats.Reset();
      g_right_stats.Reset();
    } else if (g_mode == DiagMode::kMonoLeft) {
      PrintChannelLine("MONO_L", g_left_stats, g_i2s_errors, g_last_i2s_err);
      g_left_stats.Reset();
    } else {
      PrintChannelLine("MONO_R", g_right_stats, g_i2s_errors, g_last_i2s_err);
      g_right_stats.Reset();
    }
  }
}

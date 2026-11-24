#include <Arduino.h>
#include <esp_chip_info.h>
#include <esp_flash.h>

static uint32_t g_tick = 0;

static void printHardwareReport() {
  esp_chip_info_t chip_info;
  esp_chip_info(&chip_info);

  uint32_t flash_bytes = 0;
  esp_flash_get_size(NULL, &flash_bytes);

  Serial.println("========================================");
  Serial.println("JARVIS ESP32-S3-N16R8 DIAGNOSTIC (10.1)");
  Serial.printf("Chip Model   : %s (rev %d, cores=%d)\n",
                ESP.getChipModel(),
                ESP.getChipRevision(),
                chip_info.cores);
  Serial.printf("CPU Freq     : %u MHz\n", ESP.getCpuFreqMHz());
  Serial.printf("Flash Size   : %u bytes (%.2f MB) | SDK=%u\n",
                flash_bytes,
                flash_bytes / (1024.0 * 1024.0),
                ESP.getFlashChipSize());
  Serial.printf("PSRAM Found  : %s\n", psramFound() ? "YES" : "NO");
  Serial.printf("PSRAM Size   : %u bytes (%.2f MB) | Free=%u bytes\n",
                ESP.getPsramSize(),
                ESP.getPsramSize() / (1024.0 * 1024.0),
                ESP.getFreePsram());
  Serial.printf("Heap Free    : %u / %u bytes\n", ESP.getFreeHeap(), ESP.getHeapSize());
  Serial.println("========================================");
}

void setup() {
  Serial.begin(115200);
  delay(1500);
  printHardwareReport();
}

void loop() {
  delay(2000);
  g_tick++;
  if (g_tick % 3 == 1) {
    printHardwareReport();
  }
  Serial.printf("[HEARTBEAT #%lu] uptime=%lu ms | CPU=%u MHz | Flash=%u MB | PSRAM=%s (%u MB)\n",
                (unsigned long)g_tick,
                (unsigned long)millis(),
                ESP.getCpuFreqMHz(),
                (unsigned int)(ESP.getFlashChipSize() / (1024U * 1024U)),
                psramFound() ? "OK" : "MISSING",
                (unsigned int)(ESP.getPsramSize() / (1024U * 1024U)));
}

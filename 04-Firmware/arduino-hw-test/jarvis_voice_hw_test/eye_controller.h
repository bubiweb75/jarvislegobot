#pragma once

#include <stdint.h>
#include "eye_engine.h"

namespace jarvis::voice {

class EyeController {
public:
  bool Begin();
  void SetSpeaking(bool speaking, uint32_t now_ms);
  void Update(uint32_t now_ms);

  uint8_t DetectedOledAddr() const { return oled_addr_; }
  bool IsSpeaking() const { return speaking_; }
  const char* CurrentExpressionName() const;

private:
  eyes::EyeEngine eyes_{};
  uint8_t oled_addr_ = 0;
  bool speaking_ = false;
  uint32_t last_pulse_ms_ = 0;
  uint8_t pulse_step_ = 0;
};

}  // namespace jarvis::voice

#pragma once

#include <stdint.h>
#include "eye_engine.h"

namespace jarvis::duplex {

enum class SystemState : uint8_t {
  kIdle = 0,
  kListening,
  kProcessing,
  kPlaying,
  kError
};

class EyeController {
public:
  bool Begin();
  void ApplyState(SystemState state, uint32_t now_ms);
  void Update(uint32_t now_ms);

  uint8_t DetectedOledAddr() const { return oled_addr_; }
  const char* CurrentExpressionName() const;

private:
  eyes::EyeEngine eyes_{};
  uint8_t oled_addr_ = 0;
  SystemState active_state_ = SystemState::kIdle;
  uint32_t last_anim_ms_ = 0;
  uint8_t anim_step_ = 0;
};

}  // namespace jarvis::duplex

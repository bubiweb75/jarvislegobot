#pragma once

#include <stdint.h>

namespace jarvis::duplex {

class ButtonController {
public:
  void Begin();
  void Update(uint32_t now_ms);

  bool IsPressed() const { return !stable_high_; }
  bool ConsumePressedEdge();
  bool ConsumeReleasedEdge();

private:
  static constexpr uint32_t kDebounceMs = 40;
  bool last_raw_high_ = true;
  bool stable_high_ = true;
  uint32_t last_change_ms_ = 0;
  bool pressed_edge_ = false;
  bool released_edge_ = false;
};

}  // namespace jarvis::duplex

#pragma once

#include <stdint.h>

namespace jarvis::voice {

class ButtonController {
public:
  void Begin();
  // Restituisce true una sola volta per ogni pressione breve valida (anti-rimbalzo)
  bool PollShortPress(uint32_t now_ms);

private:
  static constexpr uint32_t kDebounceMs = 40;
  bool last_raw_ = true;
  bool stable_ = true;
  uint32_t last_change_ms_ = 0;
  bool pressed_armed_ = false;
};

}  // namespace jarvis::voice

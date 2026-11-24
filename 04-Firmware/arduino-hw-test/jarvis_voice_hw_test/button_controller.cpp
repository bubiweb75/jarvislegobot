#include "button_controller.h"

#include <Arduino.h>
#include "pinout_config.h"

namespace jarvis::voice {

void ButtonController::Begin() {
  pinMode(pins::kButtonActivate, INPUT_PULLUP);
  last_raw_ = (digitalRead(pins::kButtonActivate) == HIGH);
  stable_ = last_raw_;
  last_change_ms_ = millis();
  pressed_armed_ = false;
}

bool ButtonController::PollShortPress(uint32_t now_ms) {
  const bool raw = (digitalRead(pins::kButtonActivate) == HIGH);
  if (raw != last_raw_) {
    last_raw_ = raw;
    last_change_ms_ = now_ms;
  }

  if ((now_ms - last_change_ms_) >= kDebounceMs && raw != stable_) {
    stable_ = raw;
    if (!stable_) {
      // Transizione stabile HIGH -> LOW (pressione)
      pressed_armed_ = true;
    } else if (pressed_armed_) {
      // Transizione stabile LOW -> HIGH (rilascio): attiva una sola volta
      pressed_armed_ = false;
      return true;
    }
  }
  return false;
}

}  // namespace jarvis::voice

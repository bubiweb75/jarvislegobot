#include "button_controller.h"

#include <Arduino.h>
#include "pinout_config.h"

namespace jarvis::duplex {

void ButtonController::Begin() {
  pinMode(pins::kButtonActivate, INPUT_PULLUP);
  last_raw_high_ = (digitalRead(pins::kButtonActivate) == HIGH);
  stable_high_ = last_raw_high_;
  last_change_ms_ = millis();
  pressed_edge_ = false;
  released_edge_ = false;
}

void ButtonController::Update(uint32_t now_ms) {
  const bool raw_high = (digitalRead(pins::kButtonActivate) == HIGH);
  if (raw_high != last_raw_high_) {
    last_raw_high_ = raw_high;
    last_change_ms_ = now_ms;
  }

  if ((now_ms - last_change_ms_) >= kDebounceMs && raw_high != stable_high_) {
    stable_high_ = raw_high;
    if (!stable_high_) {
      pressed_edge_ = true;
    } else {
      released_edge_ = true;
    }
  }
}

bool ButtonController::ConsumePressedEdge() {
  const bool v = pressed_edge_;
  pressed_edge_ = false;
  return v;
}

bool ButtonController::ConsumeReleasedEdge() {
  const bool v = released_edge_;
  released_edge_ = false;
  return v;
}

}  // namespace jarvis::duplex

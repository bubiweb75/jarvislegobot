#include "eye_controller.h"

#include <Arduino.h>
#include "display_driver.h"
#include "pinout_config.h"

namespace jarvis::voice {

bool EyeController::Begin() {
  const auto scan = display::Begin();
  oled_addr_ = scan.detected_addr;

  if (oled_addr_ != 0) {
    Serial.printf("OLED:READY addr=0x%02X SDA=GPIO%u SCL=GPIO%u driver=%s\n",
                  oled_addr_,
                  pins::kOledSda,
                  pins::kOledScl,
                  kOledDriverName);
  } else {
    Serial.println(F("WARN:OLED_NO_ACK (0x3C/0x3D)"));
  }

  eyes_.Begin(30, 12);
  eyes_.SetVisualProfile(eyes::VisualProfile::kLively);
  eyes_.SetExpression(eyes::Expression::kNeutral);
  speaking_ = false;
  return (oled_addr_ != 0);
}

void EyeController::SetSpeaking(bool speaking, uint32_t now_ms) {
  if (speaking == speaking_) {
    return;
  }
  speaking_ = speaking;
  if (speaking_) {
    eyes_.SetExpression(eyes::Expression::kSpeaking);
    eyes_.TriggerBlink(now_ms);
    last_pulse_ms_ = now_ms;
    pulse_step_ = 0;
  } else {
    eyes_.SetExpression(eyes::Expression::kNeutral);
  }
}

void EyeController::Update(uint32_t now_ms) {
  // Leggera animazione vivace durante la riproduzione vocale (senza lip-sync complesso)
  if (speaking_ && (now_ms - last_pulse_ms_) >= 450U) {
    last_pulse_ms_ = now_ms;
    static constexpr int8_t kDx[] = {2, -2, 0, 1};
    static constexpr int8_t kDy[] = {-1, 0, -2, 0};
    eyes_.SetGazeOffset(kDx[pulse_step_ & 0x03U], kDy[pulse_step_ & 0x03U], 420U, now_ms);
    pulse_step_++;
  }
  eyes_.Update(now_ms);
}

const char* EyeController::CurrentExpressionName() const {
  return eyes::ExpressionToString(eyes_.GetExpression());
}

}  // namespace jarvis::voice

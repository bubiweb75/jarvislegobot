#include "eye_controller.h"

#include <Arduino.h>
#include "display_driver.h"
#include "pinout_config.h"

namespace jarvis::duplex {

bool EyeController::Begin() {
  const auto scan = display::Begin();
  oled_addr_ = scan.detected_addr;

  if (oled_addr_ != 0) {
    Serial.printf("[OLED] Ready addr=0x%02X SDA=GPIO%u SCL=GPIO%u driver=%s\n",
                  oled_addr_,
                  pins::kOledSda,
                  pins::kOledScl,
                  kOledDriverName);
  } else {
    Serial.println(F("[OLED] WARN: nessun ACK a 0x3C/0x3D"));
  }

  eyes_.Begin(30, 12);
  eyes_.SetVisualProfile(eyes::VisualProfile::kLively);
  eyes_.SetExpression(eyes::Expression::kNeutral);
  active_state_ = SystemState::kIdle;
  return (oled_addr_ != 0);
}

void EyeController::ApplyState(SystemState state, uint32_t now_ms) {
  if (state == active_state_) {
    return;
  }
  active_state_ = state;
  last_anim_ms_ = now_ms;
  anim_step_ = 0;

  switch (state) {
    case SystemState::kIdle:
      eyes_.SetExpression(eyes::Expression::kNeutral);
      break;
    case SystemState::kListening:
      eyes_.SetExpression(eyes::Expression::kListening);
      break;
    case SystemState::kProcessing:
      eyes_.SetExpression(eyes::Expression::kThinking);
      break;
    case SystemState::kPlaying:
      eyes_.SetExpression(eyes::Expression::kSpeaking);
      eyes_.TriggerBlink(now_ms);
      break;
    case SystemState::kError:
      eyes_.SetExpression(eyes::Expression::kConfused);
      break;
  }
}

void EyeController::Update(uint32_t now_ms) {
  if (active_state_ == SystemState::kPlaying && (now_ms - last_anim_ms_) >= 420U) {
    last_anim_ms_ = now_ms;
    static constexpr int8_t kDx[] = {2, -2, 0, 1};
    static constexpr int8_t kDy[] = {-1, 0, -2, 0};
    eyes_.SetGazeOffset(kDx[anim_step_ & 0x03U], kDy[anim_step_ & 0x03U], 400U, now_ms);
    anim_step_++;
  }
  eyes_.Update(now_ms);
}

const char* EyeController::CurrentExpressionName() const {
  return eyes::ExpressionToString(eyes_.GetExpression());
}

}  // namespace jarvis::duplex

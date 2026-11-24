// =============================================================================
// JARVIS AI Desk Buddy — Animated Eye Rendering Engine (v2 Organic Companion)
//
// Attribution:
//   Non-blocking blinker, eyelid masking concept, and idle gaze architecture
//   originally inspired by Carmoruda/Jarvis (MIT License, Copyright (c) 2026
//   Carmoruda). Redesigned for JARVIS AI Desk Buddy with original organic
//   super-capsule geometry, curved eyelids, and FPS-independent motion.
// =============================================================================
#include "eye_engine.h"

#include <Arduino.h>
#include <math.h>
#include "display_driver.h"

namespace jarvis::eyes {

namespace {

int ClampInt(int val, int lo, int hi) {
    if (val < lo) return lo;
    if (val > hi) return hi;
    return val;
}

float ClampFloat(float val, float lo, float hi) {
    if (val < lo) return lo;
    if (val > hi) return hi;
    return val;
}

int RoundHalfAway(float val) {
    return (val >= 0.0f) ? static_cast<int>(floorf(val + 0.5f))
                         : -static_cast<int>(floorf(-val + 0.5f));
}

float SmoothExp(float current, float target, float rate, float dt_sec) {
    const float diff = target - current;
    if (fabsf(diff) < 0.05f) return target;
    const float alpha = 1.0f - expf(-rate * dt_sec);
    return current + diff * alpha;
}

}  // namespace

const char* ExpressionToString(Expression expr) {
    switch (expr) {
        case Expression::kNeutral:     return "NEUTRAL";
        case Expression::kHappy:       return "HAPPY";
        case Expression::kCurious:     return "CURIOUS";
        case Expression::kSleepy:      return "SLEEPY";
        case Expression::kListening:   return "LISTENING";
        case Expression::kThinking:    return "THINKING";
        case Expression::kSpeaking:    return "SPEAKING";
        case Expression::kSurprised:   return "SURPRISED";
        case Expression::kShy:         return "SHY";
        case Expression::kLove:        return "LOVE";
        case Expression::kWink:        return "WINK";
        case Expression::kConfused:    return "CONFUSED";
        case Expression::kMischievous: return "MISCHIEVOUS";
        case Expression::kSleeping:    return "SLEEPING";
        default:                       return "UNKNOWN";
    }
}

const char* VisualProfileToString(VisualProfile profile) {
    switch (profile) {
        case VisualProfile::kCalm:    return "CALM";
        case VisualProfile::kLively:  return "LIVELY";
        case VisualProfile::kPlayful: return "PLAYFUL";
        default:                      return "LIVELY";
    }
}

float EyeEngine::ProfileSpeedScale() const {
    switch (profile_) {
        case VisualProfile::kCalm:    return 0.72f;
        case VisualProfile::kPlayful: return 1.22f;
        case VisualProfile::kLively:
        default:                      return 1.00f;
    }
}

float EyeEngine::ProfileGazeFreqScale() const {
    switch (profile_) {
        case VisualProfile::kCalm:    return 0.65f;
        case VisualProfile::kPlayful: return 1.35f;
        case VisualProfile::kLively:
        default:                      return 1.00f;
    }
}

float EyeEngine::ProfileMicroFreqScale() const {
    switch (profile_) {
        case VisualProfile::kCalm:    return 0.45f;
        case VisualProfile::kPlayful: return 1.65f;
        case VisualProfile::kLively:
        default:                      return 1.00f;
    }
}

float EyeEngine::ProfileBlinkFreqScale() const {
    switch (profile_) {
        case VisualProfile::kCalm:    return 0.80f;
        case VisualProfile::kPlayful: return 1.15f;
        case VisualProfile::kLively:
        default:                      return 1.00f;
    }
}

void EyeEngine::SeedRng(uint32_t seed) {
    rng_state_ = (seed != 0U) ? seed : 0xA511E9B3U;
}

uint32_t EyeEngine::NextRand() {
    uint32_t x = rng_state_;
    x ^= x << 13;
    x ^= x >> 17;
    x ^= x << 5;
    rng_state_ = x;
    return x;
}

int EyeEngine::RandRange(int lo, int hi) {
    if (hi <= lo) return lo;
    const uint32_t span = static_cast<uint32_t>(hi - lo + 1);
    return lo + static_cast<int>(NextRand() % span);
}

void EyeEngine::Begin(uint16_t fps, int spacing_px) {
    frame_interval_ms_ = (fps > 0) ? (1000U / fps) : 20U;
    spacing_px_ = spacing_px;
    RecalculateBasePositions();

    const uint32_t now = millis();
    last_frame_ms_ = now;
    next_blink_ms_ = now + 2200U;
    next_gaze_ms_ = now + 2400U;
    next_micro_expr_ms_ = now + 3800U;
    expr_start_ms_ = now;
    actual_fps_ = (fps > 0) ? static_cast<float>(fps) : 30.0f;

    expr_ = Expression::kNeutral;
    ApplyExpressionTargets();
    RenderFrame(now);
}

void EyeEngine::RecalculateBasePositions() {
    const int total_w = kDefaultEyeWidth + spacing_px_ + kDefaultEyeWidth;
    const int start_x = (gfx::kWidth - total_w) / 2;

    left_.base_x = start_x + kDefaultEyeWidth / 2;
    right_.base_x = start_x + kDefaultEyeWidth + spacing_px_ + kDefaultEyeWidth / 2;
    left_.base_y = gfx::kHeight / 2 + 2;
    right_.base_y = gfx::kHeight / 2 + 2;

    left_.x = left_.target_x = static_cast<float>(left_.base_x);
    right_.x = right_.target_x = static_cast<float>(right_.base_x);
    left_.y = left_.target_y = static_cast<float>(left_.base_y);
    right_.y = right_.target_y = static_cast<float>(right_.base_y);
}

void EyeEngine::SetExpression(Expression expr) {
    SetExpressionAt(expr, millis());
}

void EyeEngine::SetExpressionAt(Expression expr, uint32_t now_ms) {
    if (expr_ == expr) return;
    expr_ = expr;
    expr_start_ms_ = now_ms;
    micro_expr_ = MicroExprType::kNone;
    transition_boost_ = (expr == Expression::kSurprised) ? 1.85f : 1.05f;
    ApplyExpressionTargets();
}

void EyeEngine::ApplyExpressionTargets() {
    for (EyeState* eye : {&left_, &right_}) {
        eye->target_width = static_cast<float>(kDefaultEyeWidth);
        eye->target_height = static_cast<float>(kDefaultEyeHeight);
        eye->target_shape_power = 2.6f;
        eye->target_taper = 0.10f;
        eye->target_corner_radius = static_cast<float>(kDefaultCornerRadius);
        eye->target_lower_lid = 0.0f;
        eye->target_lower_arch = 0.0f;
        eye->target_upper_lid_l = 0.0f;
        eye->target_upper_lid_r = 0.0f;
        eye->target_upper_arch = 0.0f;
        eye->target_pupil_dx = 0.0f;
        eye->target_pupil_dy = 0.0f;
        eye->target_pupil_radius = 7.0f;
        eye->target_brow_offset = 4.0f;
        eye->target_brow_tilt = 0.0f;
        eye->target_brow_arch = 2.2f;
        eye->target_x = static_cast<float>(eye->base_x);
        eye->target_y = static_cast<float>(eye->base_y);
    }

    switch (expr_) {
        case Expression::kNeutral:
            break;

        case Expression::kHappy:
            left_.target_width = right_.target_width = 36.0f;
            left_.target_height = right_.target_height = 24.0f;
            left_.target_pupil_radius = right_.target_pupil_radius = 0.0f;
            left_.target_brow_offset = right_.target_brow_offset = 6.0f;
            left_.target_brow_arch = right_.target_brow_arch = 3.5f;
            left_.target_y = right_.target_y = static_cast<float>(left_.base_y + 1);
            break;

        case Expression::kCurious:
            left_.target_width = 30.0f;
            left_.target_height = 28.0f;
            left_.target_shape_power = 2.4f;
            left_.target_upper_lid_l = 2.0f;
            left_.target_upper_lid_r = 7.0f;
            left_.target_pupil_dx = 3.0f;
            left_.target_pupil_radius = 6.0f;
            left_.target_brow_offset = 3.5f;
            left_.target_brow_tilt = 2.5f;
            left_.target_brow_arch = 1.0f;
            left_.target_x = static_cast<float>(left_.base_x + 2);
            left_.target_y = static_cast<float>(left_.base_y + 3);

            right_.target_width = 42.0f;
            right_.target_height = 42.0f;
            right_.target_shape_power = 2.2f;
            right_.target_taper = -0.06f;
            right_.target_pupil_dx = 3.0f;
            right_.target_pupil_dy = -2.0f;
            right_.target_pupil_radius = 7.5f;
            right_.target_brow_offset = 6.5f;
            right_.target_brow_tilt = -2.5f;
            right_.target_brow_arch = 4.0f;
            right_.target_x = static_cast<float>(right_.base_x + 2);
            right_.target_y = static_cast<float>(right_.base_y - 2);
            break;

        case Expression::kSleepy:
            left_.target_width = right_.target_width = 36.0f;
            left_.target_height = right_.target_height = 30.0f;
            left_.target_upper_lid_l = left_.target_upper_lid_r = 11.0f;
            right_.target_upper_lid_l = right_.target_upper_lid_r = 11.0f;
            left_.target_upper_arch = right_.target_upper_arch = 2.0f;
            left_.target_pupil_radius = right_.target_pupil_radius = 5.0f;
            left_.target_pupil_dy = right_.target_pupil_dy = 3.0f;
            left_.target_brow_offset = right_.target_brow_offset = 2.0f;
            left_.target_brow_arch = right_.target_brow_arch = 0.5f;
            left_.target_y = right_.target_y = static_cast<float>(left_.base_y + 3);
            break;

        case Expression::kListening:
            left_.target_width = right_.target_width = 38.0f;
            left_.target_height = right_.target_height = 42.0f;
            left_.target_shape_power = right_.target_shape_power = 2.4f;
            left_.target_pupil_radius = right_.target_pupil_radius = 8.5f;
            left_.target_brow_offset = right_.target_brow_offset = 5.5f;
            left_.target_brow_arch = right_.target_brow_arch = 3.0f;
            break;

        case Expression::kThinking:
            left_.target_width = right_.target_width = 35.0f;
            left_.target_height = right_.target_height = 31.0f;
            left_.target_x = static_cast<float>(left_.base_x + 4);
            right_.target_x = static_cast<float>(right_.base_x + 4);
            left_.target_y = static_cast<float>(left_.base_y - 3);
            right_.target_y = static_cast<float>(right_.base_y - 3);
            left_.target_upper_lid_l = 8.0f;
            left_.target_upper_lid_r = 5.0f;
            right_.target_upper_lid_l = 4.0f;
            right_.target_upper_lid_r = 6.0f;
            left_.target_lower_lid = right_.target_lower_lid = 3.0f;
            left_.target_pupil_dx = right_.target_pupil_dx = 5.5f;
            left_.target_pupil_dy = right_.target_pupil_dy = -3.0f;
            left_.target_pupil_radius = right_.target_pupil_radius = 5.5f;
            left_.target_brow_offset = 3.5f;
            left_.target_brow_tilt = 3.0f;
            right_.target_brow_offset = 5.5f;
            right_.target_brow_tilt = -1.5f;
            break;

        case Expression::kSpeaking:
            left_.target_width = right_.target_width = 37.0f;
            left_.target_height = right_.target_height = 35.0f;
            left_.target_lower_lid = right_.target_lower_lid = 4.0f;
            left_.target_lower_arch = right_.target_lower_arch = 6.0f;
            left_.target_pupil_radius = right_.target_pupil_radius = 6.5f;
            left_.target_brow_offset = right_.target_brow_offset = 4.5f;
            break;

        case Expression::kSurprised:
            left_.target_width = right_.target_width = 39.0f;
            left_.target_height = right_.target_height = 45.0f;
            left_.target_shape_power = right_.target_shape_power = 2.1f;
            left_.target_taper = right_.target_taper = 0.0f;
            left_.target_pupil_radius = right_.target_pupil_radius = 3.5f;
            left_.target_brow_offset = right_.target_brow_offset = 6.0f;
            left_.target_brow_arch = right_.target_brow_arch = 4.5f;
            left_.target_y = right_.target_y = static_cast<float>(left_.base_y);
            break;

        case Expression::kShy:
            left_.target_width = right_.target_width = 32.0f;
            left_.target_height = right_.target_height = 28.0f;
            left_.target_upper_lid_l = left_.target_upper_lid_r = 6.0f;
            right_.target_upper_lid_l = right_.target_upper_lid_r = 6.0f;
            left_.target_pupil_dx = right_.target_pupil_dx = -4.0f;
            left_.target_pupil_dy = right_.target_pupil_dy = 2.5f;
            left_.target_pupil_radius = right_.target_pupil_radius = 6.0f;
            left_.target_brow_offset = right_.target_brow_offset = 4.5f;
            left_.target_brow_tilt = -3.5f;
            right_.target_brow_tilt = 3.5f;
            left_.target_x = static_cast<float>(left_.base_x - 3);
            right_.target_x = static_cast<float>(right_.base_x - 3);
            left_.target_y = right_.target_y = static_cast<float>(left_.base_y + 4);
            break;

        case Expression::kLove:
            left_.target_width = right_.target_width = 34.0f;
            left_.target_height = right_.target_height = 34.0f;
            left_.target_pupil_radius = right_.target_pupil_radius = 0.0f;
            left_.target_brow_offset = right_.target_brow_offset = 0.0f;
            left_.target_y = right_.target_y = static_cast<float>(left_.base_y);
            break;

        case Expression::kWink:
            left_.target_width = 38.0f;
            left_.target_height = 38.0f;
            left_.target_pupil_radius = 7.0f;
            left_.target_brow_offset = 5.5f;
            left_.target_brow_arch = 3.0f;
            right_.target_width = 36.0f;
            right_.target_height = 26.0f;
            right_.target_pupil_radius = 0.0f;
            right_.target_brow_offset = 5.0f;
            right_.target_y = static_cast<float>(right_.base_y + 2);
            break;

        case Expression::kConfused:
            left_.target_width = 31.0f;
            left_.target_height = 27.0f;
            left_.target_upper_lid_l = 8.0f;
            left_.target_upper_lid_r = 3.0f;
            left_.target_pupil_dx = -3.0f;
            left_.target_pupil_radius = 5.5f;
            left_.target_brow_offset = 4.0f;
            left_.target_brow_tilt = 3.5f;
            left_.target_y = static_cast<float>(left_.base_y + 2);
            right_.target_width = 40.0f;
            right_.target_height = 40.0f;
            right_.target_pupil_dx = 3.0f;
            right_.target_pupil_dy = -2.0f;
            right_.target_pupil_radius = 7.0f;
            right_.target_brow_offset = 6.0f;
            right_.target_brow_tilt = -3.5f;
            right_.target_brow_arch = 4.0f;
            right_.target_y = static_cast<float>(right_.base_y - 2);
            break;

        case Expression::kMischievous:
            left_.target_width = right_.target_width = 37.0f;
            left_.target_height = right_.target_height = 32.0f;
            left_.target_upper_lid_l = 2.0f;
            left_.target_upper_lid_r = 14.0f;
            right_.target_upper_lid_l = 14.0f;
            right_.target_upper_lid_r = 2.0f;
            left_.target_lower_lid = right_.target_lower_lid = 4.0f;
            left_.target_lower_arch = right_.target_lower_arch = 7.0f;
            left_.target_pupil_dx = right_.target_pupil_dx = 5.0f;
            left_.target_pupil_radius = right_.target_pupil_radius = 5.5f;
            left_.target_brow_offset = right_.target_brow_offset = 4.5f;
            left_.target_brow_tilt = 4.5f;
            right_.target_brow_tilt = -4.5f;
            left_.target_x = static_cast<float>(left_.base_x + 3);
            right_.target_x = static_cast<float>(right_.base_x + 3);
            break;

        case Expression::kSleeping:
            left_.target_width = right_.target_width = 34.0f;
            left_.target_height = right_.target_height = 24.0f;
            left_.target_pupil_radius = right_.target_pupil_radius = 0.0f;
            left_.target_brow_offset = right_.target_brow_offset = 0.0f;
            left_.target_y = right_.target_y = static_cast<float>(left_.base_y + 3);
            break;
    }
}

void EyeEngine::TriggerBlink(uint32_t now_ms) {
    if (blink_phase_ == BlinkPhase::kOpen) {
        blink_phase_ = BlinkPhase::kClosing;
        next_blink_ms_ = now_ms + 3200U;
    }
}

void EyeEngine::SetGazeOffset(int8_t dx, int8_t dy, uint32_t hold_ms, uint32_t now_ms) {
    const int clamped_dx = ClampInt(dx, -11, 11);
    const int clamped_dy = ClampInt(dy, -6, 6);
    micro_expr_ = MicroExprType::kNone;
    gaze_is_micro_ = false;
    left_.target_x = static_cast<float>(left_.base_x) + static_cast<float>(clamped_dx) * 0.45f;
    right_.target_x = static_cast<float>(right_.base_x) + static_cast<float>(clamped_dx) * 0.45f;
    left_.target_y = static_cast<float>(left_.base_y) + static_cast<float>(clamped_dy) * 0.40f;
    right_.target_y = static_cast<float>(right_.base_y) + static_cast<float>(clamped_dy) * 0.40f;
    left_.target_pupil_dx = right_.target_pupil_dx = static_cast<float>(clamped_dx) * 0.55f;
    left_.target_pupil_dy = right_.target_pupil_dy = static_cast<float>(clamped_dy) * 0.45f;
    gaze_override_until_ms_ = now_ms + hold_ms;
}

void EyeEngine::UpdateBlinker(uint32_t now_ms, float dt_sec) {
    if (expr_ == Expression::kHappy || expr_ == Expression::kWink || expr_ == Expression::kSleeping) {
        blink_phase_ = BlinkPhase::kOpen;
        left_.blink_squeeze = 0.0f;
        right_.blink_squeeze = 0.0f;
        return;
    }

    const float speed = ProfileSpeedScale();
    const float close_rate = ((expr_ == Expression::kSleepy) ? 6.0f :
                             ((expr_ == Expression::kSurprised) ? 24.0f : 18.0f)) * speed;
    const float open_rate = ((expr_ == Expression::kSleepy) ? 4.2f :
                            ((expr_ == Expression::kSurprised) ? 18.0f : 14.0f)) * speed;

    switch (blink_phase_) {
        case BlinkPhase::kOpen:
            if (now_ms >= next_blink_ms_) {
                blink_phase_ = BlinkPhase::kClosing;
                if ((expr_ == Expression::kNeutral || expr_ == Expression::kHappy) && !double_blink_pending_) {
                    const int dbl_chance = (profile_ == VisualProfile::kPlayful) ? 28
                                         : ((profile_ == VisualProfile::kCalm) ? 8 : 20);
                    double_blink_pending_ = (RandRange(0, 99) < dbl_chance);
                }
            }
            break;

        case BlinkPhase::kClosing:
            left_.blink_squeeze += close_rate * dt_sec;
            right_.blink_squeeze += close_rate * dt_sec;
            if (left_.blink_squeeze >= 1.0f) {
                left_.blink_squeeze = right_.blink_squeeze = 1.0f;
                blink_phase_ = BlinkPhase::kHoldClosed;
                blink_hold_until_ms_ = now_ms + ((expr_ == Expression::kSleepy) ? 130U : 42U);
            }
            break;

        case BlinkPhase::kHoldClosed:
            if (now_ms >= blink_hold_until_ms_) {
                blink_phase_ = BlinkPhase::kOpening;
            }
            break;

        case BlinkPhase::kOpening: {
            // Smooth ease-out near full open for organic eyelid settle
            const float ease = 0.45f + 0.55f * left_.blink_squeeze;
            left_.blink_squeeze -= open_rate * ease * dt_sec;
            right_.blink_squeeze -= open_rate * ease * dt_sec;
            if (left_.blink_squeeze <= 0.0f) {
                left_.blink_squeeze = right_.blink_squeeze = 0.0f;
                blink_phase_ = BlinkPhase::kOpen;
                if (double_blink_pending_) {
                    double_blink_pending_ = false;
                    next_blink_ms_ = now_ms + 130U;
                } else {
                    const int min_wait = (expr_ == Expression::kSleepy) ? 1900 : 2500;
                    const int max_wait = (expr_ == Expression::kSleepy) ? 3600 : 5400;
                    const float freq = ProfileBlinkFreqScale();
                    const int wait_ms = static_cast<int>(static_cast<float>(RandRange(min_wait, max_wait)) / freq);
                    next_blink_ms_ = now_ms + static_cast<uint32_t>(ClampInt(wait_ms, 1200, 8000));
                }
            }
            break;
        }
    }
}

void EyeEngine::UpdateGaze(uint32_t now_ms) {
    if (!auto_idle_gaze_) return;
    if (now_ms < gaze_override_until_ms_) return;
    if (expr_ == Expression::kThinking || expr_ == Expression::kCurious ||
        expr_ == Expression::kSurprised || expr_ == Expression::kShy ||
        expr_ == Expression::kLove || expr_ == Expression::kWink ||
        expr_ == Expression::kConfused || expr_ == Expression::kMischievous ||
        expr_ == Expression::kSleeping) {
        return;
    }

    if (now_ms < next_gaze_ms_) return;

    // During LISTENING, keep eyes centered & attentive with only rare tiny micro-saccades
    if (expr_ == Expression::kListening) {
        const bool micro = (RandRange(0, 99) < 35);
        const int pdx = micro ? RandRange(-1, 1) : 0;
        const int pdy = micro ? RandRange(-1, 0) : 0;
        left_.target_x = static_cast<float>(left_.base_x);
        right_.target_x = static_cast<float>(right_.base_x);
        left_.target_y = static_cast<float>(left_.base_y);
        right_.target_y = static_cast<float>(right_.base_y);
        left_.target_pupil_dx = right_.target_pupil_dx = static_cast<float>(pdx);
        left_.target_pupil_dy = right_.target_pupil_dy = static_cast<float>(pdy);
        gaze_is_micro_ = micro;
        next_gaze_ms_ = now_ms + static_cast<uint32_t>(RandRange(1400, 2800));
        return;
    }

    const int roll = RandRange(0, 99);
    const bool return_center = (roll < 38);
    const bool do_micro_saccade = (!return_center && roll < 70);
    int dx = 0;
    int dy = 0;
    if (do_micro_saccade) {
        dx = RandRange(-3, 3);
        dy = RandRange(-2, 2);
        gaze_is_micro_ = true;
    } else if (!return_center) {
        const int max_dx = (expr_ == Expression::kSleepy) ? 3 : 9;
        const int max_dy = (expr_ == Expression::kSleepy) ? 2 : 4;
        dx = RandRange(-max_dx, max_dx);
        dy = RandRange(-max_dy, max_dy);
        gaze_is_micro_ = false;
    } else {
        gaze_is_micro_ = false;
    }

    const int y_bias = (expr_ == Expression::kHappy) ? -1
                     : ((expr_ == Expression::kSleepy) ? 4 : 0);
    left_.target_x = static_cast<float>(left_.base_x) + static_cast<float>(dx) * 0.45f;
    right_.target_x = static_cast<float>(right_.base_x) + static_cast<float>(dx) * 0.45f;
    left_.target_y = static_cast<float>(left_.base_y + y_bias) + static_cast<float>(dy) * 0.40f;
    right_.target_y = static_cast<float>(right_.base_y + y_bias) + static_cast<float>(dy) * 0.40f;
    left_.target_pupil_dx = right_.target_pupil_dx = static_cast<float>(dx) * 0.55f;
    left_.target_pupil_dy = right_.target_pupil_dy = static_cast<float>(dy) * 0.45f;

    const float gfreq = ProfileGazeFreqScale();
    const int base_wait = gaze_is_micro_ ? RandRange(650, 1300) : RandRange(1600, 3600);
    const int scaled_wait = static_cast<int>(static_cast<float>(base_wait) / gfreq);
    next_gaze_ms_ = now_ms + static_cast<uint32_t>(ClampInt(scaled_wait, 500, 6000));
}

void EyeEngine::UpdateMicroExpressions(uint32_t now_ms) {
    if (micro_expr_ != MicroExprType::kNone && now_ms >= micro_expr_until_ms_) {
        micro_expr_ = MicroExprType::kNone;
        ApplyExpressionTargets();
    }

    if (!micro_expressions_enabled_) return;
    if (now_ms < gaze_override_until_ms_ || blink_phase_ != BlinkPhase::kOpen) return;
    if (expr_ == Expression::kSleeping || expr_ == Expression::kLove ||
        expr_ == Expression::kSurprised || expr_ == Expression::kWink) {
        return;
    }

    if (micro_expr_ == MicroExprType::kNone && now_ms >= next_micro_expr_ms_) {
        // Rare during LISTENING so attention stays steady
        if (expr_ == Expression::kListening && RandRange(0, 99) < 65) {
            next_micro_expr_ms_ = now_ms + 3000U;
            return;
        }

        const int r = RandRange(0, 99);
        if (r < 28) {
            micro_expr_ = MicroExprType::kBrowRaise;
            right_.target_brow_offset += 3.0f;
            right_.target_brow_tilt -= 1.5f;
            micro_expr_until_ms_ = now_ms + 520U;
        } else if (r < 54) {
            micro_expr_ = MicroExprType::kSideGlance;
            const float dir = (RandRange(0, 1) == 0) ? -3.5f : 3.5f;
            left_.target_pupil_dx += dir;
            right_.target_pupil_dx += dir;
            micro_expr_until_ms_ = now_ms + 460U;
        } else if (r < 74) {
            micro_expr_ = MicroExprType::kEyeSmile;
            left_.target_lower_lid += 2.5f;
            right_.target_lower_lid += 2.5f;
            left_.target_lower_arch += 3.0f;
            right_.target_lower_arch += 3.0f;
            micro_expr_until_ms_ = now_ms + 580U;
        } else if (r < 90) {
            micro_expr_ = MicroExprType::kPupilPulse;
            left_.target_pupil_radius += 1.0f;
            right_.target_pupil_radius += 1.0f;
            micro_expr_until_ms_ = now_ms + 420U;
        } else {
            const int wink_thresh = (profile_ == VisualProfile::kPlayful) ? 100
                                  : ((profile_ == VisualProfile::kCalm) ? 0 : 50);
            if (RandRange(0, 99) < wink_thresh) {
                micro_expr_ = MicroExprType::kQuickWink;
                right_.target_upper_lid_l += 9.0f;
                right_.target_upper_lid_r += 9.0f;
                micro_expr_until_ms_ = now_ms + 300U;
            }
        }

        const float mfreq = ProfileMicroFreqScale();
        const int next_ms = static_cast<int>(static_cast<float>(RandRange(3600, 7400)) / mfreq);
        next_micro_expr_ms_ = now_ms + static_cast<uint32_t>(ClampInt(next_ms, 1800, 14000));
    }
}

void EyeEngine::UpdateExpressionMotion(uint32_t now_ms) {
    const float t_sec = static_cast<float>(now_ms - expr_start_ms_) * 0.001f;

    switch (expr_) {
        case Expression::kNeutral: {
            const float breath = sinf(t_sec * 1.4f);
            left_.target_height = right_.target_height = 32.0f + 0.8f * breath;
            break;
        }
        case Expression::kHappy: {
            const float bounce = sinf(t_sec * 3.5f) * 1.2f;
            left_.target_y = right_.target_y = static_cast<float>(left_.base_y - 2) + bounce;
            break;
        }
        case Expression::kCurious: {
            const float drift = sinf(t_sec * 1.9f) * 2.0f;
            left_.target_x = static_cast<float>(left_.base_x + 4) + drift;
            right_.target_x = static_cast<float>(right_.base_x + 4) + drift;
            break;
        }
        case Expression::kSleepy: {
            const float drowse = sinf(t_sec * 1.1f) * 1.5f;
            left_.target_upper_lid_l = left_.target_upper_lid_r = 12.0f + drowse;
            right_.target_upper_lid_l = right_.target_upper_lid_r = 12.0f + drowse;
            break;
        }
        case Expression::kListening: {
            const float breath = sinf(t_sec * 3.0f);
            left_.target_height = right_.target_height = 35.5f + 1.2f * breath;
            break;
        }
        case Expression::kThinking: {
            const float scan = 2.5f * sinf(t_sec * 1.7f) + 1.2f * sinf(t_sec * 2.9f);
            left_.target_x = static_cast<float>(left_.base_x + 7) + scan;
            right_.target_x = static_cast<float>(right_.base_x + 7) + scan;
            break;
        }
        case Expression::kSpeaking: {
            // Smooth, non-frantic syllabic envelope
            const float env = ClampFloat(
                0.5f + 0.32f * sinf(t_sec * 6.8f) + 0.18f * sinf(t_sec * 10.7f),
                0.0f, 1.0f);
            left_.target_height = right_.target_height = 27.0f + 6.0f * env;
            left_.target_lower_lid = right_.target_lower_lid = 2.0f + 3.5f * (1.0f - env);
            left_.target_lower_arch = right_.target_lower_arch = 4.0f + 2.5f * (1.0f - env);
            break;
        }
        case Expression::kSurprised: {
            const float pulse = sinf(t_sec * 5.0f);
            left_.target_width = right_.target_width = 34.0f + pulse;
            left_.target_height = right_.target_height = 38.0f + pulse;
            break;
        }
        case Expression::kShy: {
            const float sway = sinf(t_sec * 1.6f) * 1.5f;
            left_.target_x = static_cast<float>(left_.base_x - 3) + sway;
            right_.target_x = static_cast<float>(right_.base_x - 3) + sway;
            break;
        }
        case Expression::kLove: {
            const float beat = fabsf(sinf(t_sec * 3.8f)) * 1.8f;
            left_.target_y = right_.target_y = static_cast<float>(left_.base_y - 1) - beat;
            break;
        }
        case Expression::kWink: {
            left_.target_y = static_cast<float>(left_.base_y - 1) + sinf(t_sec * 2.8f) * 0.8f;
            break;
        }
        case Expression::kConfused: {
            const float tilt = sinf(t_sec * 2.2f) * 1.5f;
            left_.target_x = static_cast<float>(left_.base_x + 2) + tilt;
            right_.target_x = static_cast<float>(right_.base_x + 2) + tilt;
            break;
        }
        case Expression::kMischievous: {
            const float sly = sinf(t_sec * 2.1f) * 2.0f;
            left_.target_x = static_cast<float>(left_.base_x + 5) + sly;
            right_.target_x = static_cast<float>(right_.base_x + 5) + sly;
            break;
        }
        case Expression::kSleeping: {
            const float breathe = sinf(t_sec * 0.9f);
            left_.target_y = right_.target_y = static_cast<float>(left_.base_y + 3) + breathe;
            break;
        }
    }
}

void EyeEngine::InterpolateEye(EyeState& eye, float dt_sec) {
    const float mult = ProfileSpeedScale() * transition_boost_;
    eye.x = SmoothExp(eye.x, eye.target_x, 12.0f * mult, dt_sec);
    eye.y = SmoothExp(eye.y, eye.target_y, 12.0f * mult, dt_sec);
    eye.width = SmoothExp(eye.width, eye.target_width, 10.0f * mult, dt_sec);
    eye.height = SmoothExp(eye.height, eye.target_height, 10.0f * mult, dt_sec);
    eye.corner_radius = SmoothExp(eye.corner_radius, eye.target_corner_radius, 10.0f * mult, dt_sec);
    eye.lower_lid = SmoothExp(eye.lower_lid, eye.target_lower_lid, 12.0f * mult, dt_sec);
    eye.lower_arch = SmoothExp(eye.lower_arch, eye.target_lower_arch, 12.0f * mult, dt_sec);
    eye.upper_lid_l = SmoothExp(eye.upper_lid_l, eye.target_upper_lid_l, 12.0f * mult, dt_sec);
    eye.upper_lid_r = SmoothExp(eye.upper_lid_r, eye.target_upper_lid_r, 12.0f * mult, dt_sec);
    eye.upper_arch = SmoothExp(eye.upper_arch, eye.target_upper_arch, 12.0f * mult, dt_sec);
    eye.pupil_dx = SmoothExp(eye.pupil_dx, eye.target_pupil_dx, 14.0f * mult, dt_sec);
    eye.pupil_dy = SmoothExp(eye.pupil_dy, eye.target_pupil_dy, 14.0f * mult, dt_sec);
    eye.pupil_radius = SmoothExp(eye.pupil_radius, eye.target_pupil_radius, 12.0f * mult, dt_sec);
    eye.brow_offset = SmoothExp(eye.brow_offset, eye.target_brow_offset, 12.0f * mult, dt_sec);
    eye.brow_tilt = SmoothExp(eye.brow_tilt, eye.target_brow_tilt, 12.0f * mult, dt_sec);
    eye.brow_arch = SmoothExp(eye.brow_arch, eye.target_brow_arch, 12.0f * mult, dt_sec);
    eye.shape_power = SmoothExp(eye.shape_power, eye.target_shape_power, 10.0f * mult, dt_sec);
    eye.taper = SmoothExp(eye.taper, eye.target_taper, 10.0f * mult, dt_sec);
}

void EyeEngine::Update(uint32_t now_ms) {
    const uint32_t elapsed = now_ms - last_frame_ms_;
    if (elapsed < frame_interval_ms_) {
        return;
    }
    if (elapsed >= frame_interval_ms_ * 2U && elapsed < 2000U) {
        dropped_frames_ += (elapsed / frame_interval_ms_) - 1U;
    }
    UpdateStep(now_ms);
}

void EyeEngine::UpdateStep(uint32_t now_ms) {
    uint32_t dt_ms = (now_ms >= last_frame_ms_) ? (now_ms - last_frame_ms_) : frame_interval_ms_;
    if (dt_ms < 1U) dt_ms = 1U;
    if (dt_ms > 100U) dt_ms = 100U;
    const float dt_sec = static_cast<float>(dt_ms) * 0.001f;
    const float inst_fps = 1000.0f / static_cast<float>(dt_ms);
    actual_fps_ = actual_fps_ * 0.85f + inst_fps * 0.15f;

    last_frame_ms_ = now_ms;

    UpdateBlinker(now_ms, dt_sec);
    UpdateGaze(now_ms);
    UpdateMicroExpressions(now_ms);
    UpdateExpressionMotion(now_ms);
    InterpolateEye(left_, dt_sec);
    InterpolateEye(right_, dt_sec);
    transition_boost_ = SmoothExp(transition_boost_, 1.0f, 6.0f, dt_sec);
    RenderFrame(now_ms);
}

void EyeEngine::DrawSingleEye(const EyeState& eye) {
    const int w = ClampInt(RoundHalfAway(eye.width), 12, 46);
    const int raw_h = ClampInt(RoundHalfAway(eye.height), 10, 48);

    // Closed-eye soft curved lash line when almost fully blinked
    if (eye.blink_squeeze >= 0.85f) {
        const int cx = ClampInt(RoundHalfAway(eye.x), w / 2 + 4, gfx::kWidth - w / 2 - 4);
        const int cy = ClampInt(RoundHalfAway(eye.y) + 2, 6, gfx::kHeight - 6);
        const int half = w / 2;
        for (int dx = -half; dx <= half; ++dx) {
            const float u = static_cast<float>(dx) / static_cast<float>(half > 1 ? half : 1);
            const int sag = RoundHalfAway(1.5f * (1.0f - u * u));
            fb_.SetPixel(cx + dx, cy + sag, 1);
            fb_.SetPixel(cx + dx, cy + sag + 1, 1);
        }
        return;
    }

    const int h = ClampInt(RoundHalfAway(static_cast<float>(raw_h) * (1.0f - 0.88f * eye.blink_squeeze)), 4, 48);
    const int cx = ClampInt(RoundHalfAway(eye.x), w / 2 + 4, gfx::kWidth - w / 2 - 4);
    const int cy = ClampInt(RoundHalfAway(eye.y), h / 2 + 6, gfx::kHeight - h / 2 - 5);
    const float rx = static_cast<float>(w) * 0.5f;
    const float ry = static_cast<float>(h) * 0.5f;
    const float p = (eye.shape_power > 2.0f) ? eye.shape_power : 2.0f;

    // Organic superellipse + vertical taper
    for (int dy = -h / 2; dy <= h / 2; ++dy) {
        const float v = (ry > 0.0f) ? (static_cast<float>(dy) / ry) : 0.0f;
        const float av = fabsf(v) < 1.0f ? fabsf(v) : 1.0f;
        const float taper_scale = 1.0f - eye.taper * v;
        const float inner = 1.0f - powf(av, p);
        const float span_x = rx * taper_scale * powf(inner > 0.0f ? inner : 0.0f, 1.0f / p);
        const int half_x = static_cast<int>(floorf(span_x));
        const int py = cy + dy;
        if (py >= 4 && py <= gfx::kHeight - 5) {
            for (int dx = -half_x; dx <= half_x; ++dx) {
                const int px = cx + dx;
                if (px >= 4 && px <= gfx::kWidth - 5) {
                    fb_.SetPixel(px, py, 1);
                }
            }
        }
    }

    const int x = cx - w / 2;
    const int y = cy - h / 2;

    // Apply curved/tilted eyelid masks when open enough
    if (eye.blink_squeeze < 0.65f) {
        const float half_w = static_cast<float>(w - 1) * 0.5f;

        if (eye.lower_lid > 0.4f || eye.lower_arch > 0.4f) {
            for (int col = 0; col < w; ++col) {
                const float u = (half_w > 0.0f) ? (static_cast<float>(col) - half_w) / half_w : 0.0f;
                const float curve = 1.0f - u * u;
                const int mask_top = RoundHalfAway(
                    static_cast<float>(y + h) - eye.lower_lid - eye.lower_arch * curve);
                for (int py = mask_top; py <= y + h + 1; ++py) {
                    fb_.SetPixel(x + col, py, 0);
                }
            }
        }

        if (eye.upper_lid_l > 0.4f || eye.upper_lid_r > 0.4f || eye.upper_arch > 0.4f) {
            const float max_ul = (eye.upper_lid_l > eye.upper_lid_r) ? eye.upper_lid_l : eye.upper_lid_r;
            for (int col = 0; col < w; ++col) {
                const float frac = (w > 1) ? static_cast<float>(col) / static_cast<float>(w - 1) : 0.5f;
                const float u = (half_w > 0.0f) ? (static_cast<float>(col) - half_w) / half_w : 0.0f;
                const float curve = 1.0f - u * u;
                const float lid_y = eye.upper_lid_l + (eye.upper_lid_r - eye.upper_lid_l) * frac;
                const int mask_bot = RoundHalfAway(
                    static_cast<float>(y) + lid_y + eye.upper_arch * curve);
                for (int py = y - 2; py <= mask_bot; ++py) {
                    fb_.SetPixel(x + col, py, 0);
                }
                if (max_ul >= 12.0f && mask_bot >= 4 && mask_bot <= gfx::kHeight - 6) {
                    fb_.SetPixel(x + col, mask_bot + 1, 1);
                }
            }
        }
    }

    // Proportional dark pupil + dual futuristic catchlights
    if (eye.blink_squeeze < 0.45f && eye.pupil_radius >= 2.5f) {
        const int max_r_fit = ((w < h) ? w : h) / 2 - 4;
        const int pr = ClampInt(RoundHalfAway(eye.pupil_radius), 3, (max_r_fit > 3) ? max_r_fit : 3);
        const int top_mask = RoundHalfAway(
            ((eye.upper_lid_l > eye.upper_lid_r) ? eye.upper_lid_l : eye.upper_lid_r) + eye.upper_arch * 0.5f);
        const int bot_mask = RoundHalfAway(eye.lower_lid + eye.lower_arch * 0.5f);
        const int min_px = x + pr + 4;
        const int max_px = x + w - 1 - pr - 4;
        const int min_py = y + top_mask + pr + 2;
        const int max_py = y + h - 1 - bot_mask - pr - 2;
        if (min_px <= max_px && min_py <= max_py) {
            const int px = ClampInt(RoundHalfAway(static_cast<float>(cx) + eye.pupil_dx), min_px, max_px);
            const int py = ClampInt(RoundHalfAway(static_cast<float>(cy) + eye.pupil_dy), min_py, max_py);
            fb_.FillCircle(px, py, pr, 0);
            // Primary crisp 2x2 catchlight
            const int gx = px - (pr / 2) + 1;
            const int gy = py - (pr / 2) + 1;
            fb_.SetPixel(gx, gy, 1);
            fb_.SetPixel(gx + 1, gy, 1);
            fb_.SetPixel(gx, gy + 1, 1);
            fb_.SetPixel(gx + 1, gy + 1, 1);
            // Secondary subtle tech glint
            if (pr >= 5) {
                fb_.SetPixel(px + (pr / 2) - 1, py + (pr / 2) - 1, 1);
            }
        }
    }

    // Sculpted tapered eyebrow integrated over the eye dome
    if (eye.brow_offset >= 1.0f && eye.blink_squeeze < 0.70f) {
        const int bw = ClampInt(w - 6, 14, 34);
        const int bx0 = ClampInt(cx - bw / 2, 4, gfx::kWidth - bw - 4);
        const int by_base = ClampInt(y - RoundHalfAway(eye.brow_offset), 4, gfx::kHeight - 8);
        for (int col = 0; col < bw; ++col) {
            const float frac = (bw > 1) ? static_cast<float>(col) / static_cast<float>(bw - 1) : 0.5f;
            const float u = (frac - 0.5f) * 2.0f;
            const float arch = eye.brow_arch * (1.0f - u * u);
            const float tilt = eye.brow_tilt * (frac - 0.5f);
            const int py = ClampInt(RoundHalfAway(static_cast<float>(by_base) + tilt - arch), 4, gfx::kHeight - 6);
            const int thick = (fabsf(u) < 0.55f) ? 3 : 2;
            for (int t = 0; t < thick; ++t) {
                fb_.SetPixel(bx0 + col, py + t, 1);
            }
        }
    }
}

void EyeEngine::DrawHappyCrescent(const EyeState& eye) {
    const int cx = ClampInt(RoundHalfAway(eye.x), 22, gfx::kWidth - 22);
    const int cy = ClampInt(RoundHalfAway(eye.y), 16, gfx::kHeight - 14);
    constexpr int kHalf = 16;
    for (int dx = -kHalf; dx <= kHalf; ++dx) {
        const float u = static_cast<float>(dx) / static_cast<float>(kHalf);
        const int arch = RoundHalfAway(9.0f * (1.0f - u * u));
        const int py = cy + 3 - arch;
        const float au = fabsf(u);
        const int thick = (au < 0.65f) ? 5 : ((au < 0.85f) ? 4 : 3);
        for (int t = 0; t < thick; ++t) {
            fb_.SetPixel(cx + dx, py + t, 1);
        }
    }
    // Sculpted happy brow above
    constexpr int kBw = 26;
    const int bx0 = cx - kBw / 2;
    const int by0 = (cy - 15 > 5) ? (cy - 15) : 5;
    for (int col = 0; col < kBw; ++col) {
        const float u = (static_cast<float>(col) / static_cast<float>(kBw - 1) - 0.5f) * 2.0f;
        const int py_raw = by0 - RoundHalfAway(3.0f * (1.0f - u * u));
        const int py = (py_raw > 4) ? py_raw : 4;
        fb_.SetPixel(bx0 + col, py, 1);
        fb_.SetPixel(bx0 + col, py + 1, 1);
    }
}

void EyeEngine::DrawPlumpHeart(int cx, int cy) {
    const int clamped_cx = ClampInt(cx, 18, gfx::kWidth - 18);
    const int clamped_cy = ClampInt(cy, 18, gfx::kHeight - 18);
    for (int dy = -14; dy < 14; ++dy) {
        for (int dx = -14; dx <= 14; ++dx) {
            const float nx = static_cast<float>(dx) / 11.5f;
            const float ny = -(static_cast<float>(dy) + 1.5f) / 10.5f;
            const float r2 = nx * nx + ny * ny - 1.0f;
            const float val = r2 * r2 * r2 - (nx * nx) * (ny * ny * ny);
            if (val <= 0.0f) {
                fb_.SetPixel(clamped_cx + dx, clamped_cy + dy, 1);
            }
        }
    }
    // Glossy catchlight on left lobe
    fb_.SetPixel(clamped_cx - 6, clamped_cy - 5, 0);
    fb_.SetPixel(clamped_cx - 5, clamped_cy - 5, 0);
    fb_.SetPixel(clamped_cx - 6, clamped_cy - 4, 0);
}

void EyeEngine::DrawGlyph(int ox, int oy, const char* const* pattern, uint8_t rows, int scale) {
    for (uint8_t r = 0; r < rows; ++r) {
        const char* row = pattern[r];
        for (int c = 0; row[c] != '\0'; ++c) {
            if (row[c] == '1') {
                for (int sy = 0; sy < scale; ++sy) {
                    for (int sx = 0; sx < scale; ++sx) {
                        const int px = ClampInt(ox + c * scale + sx, 4, gfx::kWidth - 5);
                        const int py = ClampInt(oy + static_cast<int>(r) * scale + sy, 4, gfx::kHeight - 5);
                        fb_.SetPixel(px, py, 1);
                    }
                }
            }
        }
    }
}

void EyeEngine::DrawSleepingLash(const EyeState& eye) {
    const int cx = ClampInt(RoundHalfAway(eye.x), 22, gfx::kWidth - 22);
    const int cy = ClampInt(RoundHalfAway(eye.y), 16, gfx::kHeight - 16);
    constexpr int kHalf = 15;
    for (int dx = -kHalf; dx <= kHalf; ++dx) {
        const float u = static_cast<float>(dx) / static_cast<float>(kHalf);
        const int sag = RoundHalfAway(5.0f * (1.0f - u * u));
        const int py = cy - 1 + sag;
        const int thick = (fabsf(u) < 0.7f) ? 4 : 3;
        for (int t = 0; t < thick; ++t) {
            fb_.SetPixel(cx + dx, py + t, 1);
        }
    }
}

void EyeEngine::RenderToFramebuffer(uint32_t now_ms) {
    fb_.Clear();

    if (expr_ == Expression::kLove) {
        const int beat = ((now_ms / 260U) % 2U == 0U) ? 1 : 0;
        DrawPlumpHeart(RoundHalfAway(left_.x), RoundHalfAway(left_.y) - beat);
        DrawPlumpHeart(RoundHalfAway(right_.x), RoundHalfAway(right_.y) - beat);
        return;
    }

    if (expr_ == Expression::kHappy) {
        DrawHappyCrescent(left_);
        DrawHappyCrescent(right_);
        const int cxs[2] = {RoundHalfAway(left_.x) - 14, RoundHalfAway(right_.x) + 14};
        for (int cx : cxs) {
            fb_.SetPixel(cx, 48, 1);
            fb_.SetPixel(cx + 1, 47, 1);
            fb_.SetPixel(cx + 2, 48, 1);
        }
        return;
    }

    if (expr_ == Expression::kWink) {
        DrawSingleEye(left_);
        DrawHappyCrescent(right_);
        return;
    }

    if (expr_ == Expression::kSleeping) {
        DrawSleepingLash(left_);
        DrawSleepingLash(right_);
        const int phase = static_cast<int>((now_ms / 450U) % 3U);
        static const char* const kZSmall[4] = {"1111", "..1.", ".1..", "1111"};
        static const char* const kZBig[5] = {"11111", "...1.", "..1..", ".1...", "11111"};
        DrawGlyph(98, 14 - phase, kZSmall, 4, 1);
        DrawGlyph(106, 7 - phase, kZBig, 5, 1);
        return;
    }

    DrawSingleEye(left_);
    DrawSingleEye(right_);

    // Subtle non-intrusive bottom/corner cues
    if (expr_ == Expression::kListening) {
        const uint8_t pulse_r = ((now_ms / 280U) % 2U == 0U) ? 2 : 1;
        fb_.FillCircle(gfx::kWidth / 2, gfx::kHeight - 4, pulse_r, 1);
    } else if (expr_ == Expression::kThinking) {
        const uint8_t active_dot = static_cast<uint8_t>((now_ms / 300U) % 3U);
        for (uint8_t i = 0; i < 3; ++i) {
            const int dx = (gfx::kWidth / 2 - 8) + static_cast<int>(i) * 8;
            if (i == active_dot) {
                fb_.FillCircle(dx, gfx::kHeight - 4, 2, 1);
            } else {
                fb_.DrawCircle(dx, gfx::kHeight - 4, 1, 1);
            }
        }
    } else if (expr_ == Expression::kShy) {
        const int cxs[2] = {RoundHalfAway(left_.x) - 10, RoundHalfAway(right_.x) + 10};
        for (int cx : cxs) {
            for (int off : {-4, 0, 4}) {
                fb_.SetPixel(cx + off, 53, 1);
                fb_.SetPixel(cx + off + 1, 52, 1);
            }
        }
    } else if (expr_ == Expression::kConfused) {
        static const char* const kQMark[7] = {
            ".111.", "1...1", "...1.", "..1..", "..1..", ".....", "..1.."
        };
        DrawGlyph(114, 6, kQMark, 7, 1);
    } else if (expr_ == Expression::kSurprised) {
        static const char* const kBang[6] = {"11", "11", "11", "11", "..", "11"};
        DrawGlyph(gfx::kWidth / 2 - 1, 6, kBang, 6, 1);
    }
}

void EyeEngine::RenderFrame(uint32_t now_ms) {
    const uint32_t t0 = micros();
    RenderToFramebuffer(now_ms);
    last_render_us_ = micros() - t0;
    last_present_us_ = display::PresentFramebuffer(fb_);
}

}  // namespace jarvis::eyes

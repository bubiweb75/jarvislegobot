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
        case Expression::kNeutral:   return "NEUTRAL";
        case Expression::kHappy:     return "HAPPY";
        case Expression::kCurious:   return "CURIOUS";
        case Expression::kSleepy:    return "SLEEPY";
        case Expression::kListening: return "LISTENING";
        case Expression::kThinking:  return "THINKING";
        case Expression::kSpeaking:  return "SPEAKING";
        default:                     return "UNKNOWN";
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
    expr_start_ms_ = now;

    expr_ = Expression::kNeutral;
    ApplyExpressionTargets();
    RenderFrame(now);
}

void EyeEngine::RecalculateBasePositions() {
    const int total_w = kDefaultEyeWidth + spacing_px_ + kDefaultEyeWidth;
    const int start_x = (gfx::kWidth - total_w) / 2;

    left_.base_x = start_x + kDefaultEyeWidth / 2;
    right_.base_x = start_x + kDefaultEyeWidth + spacing_px_ + kDefaultEyeWidth / 2;
    left_.base_y = gfx::kHeight / 2;
    right_.base_y = gfx::kHeight / 2;

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
    ApplyExpressionTargets();
}

void EyeEngine::ApplyExpressionTargets() {
    for (EyeState* eye : {&left_, &right_}) {
        eye->target_width = static_cast<float>(kDefaultEyeWidth);
        eye->target_height = static_cast<float>(kDefaultEyeHeight);
        eye->target_corner_radius = static_cast<float>(kDefaultCornerRadius);
        eye->target_lower_lid = 0.0f;
        eye->target_lower_arch = 0.0f;
        eye->target_upper_lid_l = 0.0f;
        eye->target_upper_lid_r = 0.0f;
        eye->target_upper_arch = 0.0f;
        eye->target_x = static_cast<float>(eye->base_x);
        eye->target_y = static_cast<float>(eye->base_y);
    }

    switch (expr_) {
        case Expression::kNeutral:
            // Relaxed, balanced organic capsule eyes
            break;

        case Expression::kHappy:
            // Soft curved crescent smile from lower cheeks, lifted slightly
            left_.target_width = right_.target_width = 33.0f;
            left_.target_height = right_.target_height = 30.0f;
            left_.target_corner_radius = right_.target_corner_radius = 12.0f;
            left_.target_lower_lid = right_.target_lower_lid = 6.0f;
            left_.target_lower_arch = right_.target_lower_arch = 12.0f;
            left_.target_y = right_.target_y = static_cast<float>(left_.base_y - 2);
            break;

        case Expression::kCurious:
            // Asymmetric inquisitive look + simulated slight head tilt
            left_.target_width = 27.0f;
            left_.target_height = 26.0f;
            left_.target_corner_radius = 9.0f;
            left_.target_upper_lid_l = 1.0f;
            left_.target_upper_lid_r = 6.0f;
            left_.target_x = static_cast<float>(left_.base_x + 4);
            left_.target_y = static_cast<float>(left_.base_y + 2);

            right_.target_width = 34.0f;
            right_.target_height = 36.0f;
            right_.target_corner_radius = 12.0f;
            right_.target_x = static_cast<float>(right_.base_x + 4);
            right_.target_y = static_cast<float>(right_.base_y - 3);
            break;

        case Expression::kSleepy:
            // Droopy curved upper lids, lower relaxed position
            left_.target_width = right_.target_width = 31.0f;
            left_.target_height = right_.target_height = 28.0f;
            left_.target_corner_radius = right_.target_corner_radius = 10.0f;
            left_.target_upper_lid_l = left_.target_upper_lid_r = 12.0f;
            right_.target_upper_lid_l = right_.target_upper_lid_r = 12.0f;
            left_.target_upper_arch = right_.target_upper_arch = 2.5f;
            left_.target_y = right_.target_y = static_cast<float>(left_.base_y + 4);
            break;

        case Expression::kListening:
            // Wide, attentive, centered rounded eyes
            left_.target_width = right_.target_width = 32.0f;
            left_.target_height = right_.target_height = 36.0f;
            left_.target_corner_radius = right_.target_corner_radius = 11.0f;
            break;

        case Expression::kThinking:
            // Up-right focused gaze with subtle concentrated squint
            left_.target_width = right_.target_width = 29.0f;
            left_.target_height = right_.target_height = 29.0f;
            left_.target_corner_radius = right_.target_corner_radius = 10.0f;
            left_.target_x = static_cast<float>(left_.base_x + 7);
            right_.target_x = static_cast<float>(right_.base_x + 7);
            left_.target_y = static_cast<float>(left_.base_y - 5);
            right_.target_y = static_cast<float>(right_.base_y - 5);
            left_.target_upper_lid_l = 4.0f;
            left_.target_upper_lid_r = 2.0f;
            right_.target_lower_lid = 3.0f;
            right_.target_lower_arch = 3.0f;
            break;

        case Expression::kSpeaking:
            // Warm, gently animated companion eyes
            left_.target_width = right_.target_width = 31.0f;
            left_.target_height = right_.target_height = 31.0f;
            left_.target_corner_radius = right_.target_corner_radius = 10.0f;
            left_.target_lower_lid = right_.target_lower_lid = 3.0f;
            left_.target_lower_arch = right_.target_lower_arch = 5.0f;
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
    left_.target_x = static_cast<float>(left_.base_x + clamped_dx);
    right_.target_x = static_cast<float>(right_.base_x + clamped_dx);
    left_.target_y = static_cast<float>(left_.base_y + clamped_dy);
    right_.target_y = static_cast<float>(right_.base_y + clamped_dy);
    gaze_override_until_ms_ = now_ms + hold_ms;
}

void EyeEngine::UpdateBlinker(uint32_t now_ms, float dt_sec) {
    const float close_rate = (expr_ == Expression::kSleepy) ? 6.5f : 18.0f;
    const float open_rate = (expr_ == Expression::kSleepy) ? 4.5f : 14.0f;

    switch (blink_phase_) {
        case BlinkPhase::kOpen:
            if (now_ms >= next_blink_ms_) {
                blink_phase_ = BlinkPhase::kClosing;
                if (expr_ == Expression::kNeutral && !double_blink_pending_) {
                    double_blink_pending_ = (RandRange(0, 99) < 20);
                }
            }
            break;

        case BlinkPhase::kClosing:
            left_.blink_squeeze += close_rate * dt_sec;
            right_.blink_squeeze += close_rate * dt_sec;
            if (left_.blink_squeeze >= 1.0f) {
                left_.blink_squeeze = right_.blink_squeeze = 1.0f;
                blink_phase_ = BlinkPhase::kHoldClosed;
                blink_hold_until_ms_ = now_ms + ((expr_ == Expression::kSleepy) ? 140U : 45U);
            }
            break;

        case BlinkPhase::kHoldClosed:
            if (now_ms >= blink_hold_until_ms_) {
                blink_phase_ = BlinkPhase::kOpening;
            }
            break;

        case BlinkPhase::kOpening:
            left_.blink_squeeze -= open_rate * dt_sec;
            right_.blink_squeeze -= open_rate * dt_sec;
            if (left_.blink_squeeze <= 0.0f) {
                left_.blink_squeeze = right_.blink_squeeze = 0.0f;
                blink_phase_ = BlinkPhase::kOpen;
                if (double_blink_pending_) {
                    double_blink_pending_ = false;
                    next_blink_ms_ = now_ms + 130U;
                } else {
                    const int min_wait = (expr_ == Expression::kSleepy) ? 1900 : 2600;
                    const int max_wait = (expr_ == Expression::kSleepy) ? 3600 : 5400;
                    next_blink_ms_ = now_ms + static_cast<uint32_t>(RandRange(min_wait, max_wait));
                }
            }
            break;
    }
}

void EyeEngine::UpdateGaze(uint32_t now_ms) {
    if (!auto_idle_gaze_) return;
    if (now_ms < gaze_override_until_ms_) return;
    if (expr_ == Expression::kThinking || expr_ == Expression::kListening ||
        expr_ == Expression::kCurious) {
        return;
    }

    if (now_ms >= next_gaze_ms_) {
        const bool return_center = (RandRange(0, 99) < 35);
        int dx = 0;
        int dy = 0;
        if (!return_center) {
            const int max_dx = (expr_ == Expression::kSleepy) ? 3 : 9;
            const int max_dy = (expr_ == Expression::kSleepy) ? 2 : 4;
            dx = RandRange(-max_dx, max_dx);
            dy = RandRange(-max_dy, max_dy);
        }

        const int y_bias = (expr_ == Expression::kHappy) ? -2
                         : ((expr_ == Expression::kSleepy) ? 4 : 0);
        left_.target_x = static_cast<float>(left_.base_x + dx);
        right_.target_x = static_cast<float>(right_.base_x + dx);
        left_.target_y = static_cast<float>(left_.base_y + dy + y_bias);
        right_.target_y = static_cast<float>(right_.base_y + dy + y_bias);

        next_gaze_ms_ = now_ms + static_cast<uint32_t>(RandRange(1700, 3900));
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
    }
}

void EyeEngine::InterpolateEye(EyeState& eye, float dt_sec) {
    eye.x = SmoothExp(eye.x, eye.target_x, 12.0f, dt_sec);
    eye.y = SmoothExp(eye.y, eye.target_y, 12.0f, dt_sec);
    eye.width = SmoothExp(eye.width, eye.target_width, 10.0f, dt_sec);
    eye.height = SmoothExp(eye.height, eye.target_height, 10.0f, dt_sec);
    eye.corner_radius = SmoothExp(eye.corner_radius, eye.target_corner_radius, 10.0f, dt_sec);
    eye.lower_lid = SmoothExp(eye.lower_lid, eye.target_lower_lid, 12.0f, dt_sec);
    eye.lower_arch = SmoothExp(eye.lower_arch, eye.target_lower_arch, 12.0f, dt_sec);
    eye.upper_lid_l = SmoothExp(eye.upper_lid_l, eye.target_upper_lid_l, 12.0f, dt_sec);
    eye.upper_lid_r = SmoothExp(eye.upper_lid_r, eye.target_upper_lid_r, 12.0f, dt_sec);
    eye.upper_arch = SmoothExp(eye.upper_arch, eye.target_upper_arch, 12.0f, dt_sec);
}

void EyeEngine::Update(uint32_t now_ms) {
    if (now_ms - last_frame_ms_ < frame_interval_ms_) {
        return;
    }
    UpdateStep(now_ms);
}

void EyeEngine::UpdateStep(uint32_t now_ms) {
    uint32_t dt_ms = (now_ms >= last_frame_ms_) ? (now_ms - last_frame_ms_) : frame_interval_ms_;
    if (dt_ms < 1U) dt_ms = 1U;
    if (dt_ms > 100U) dt_ms = 100U;
    const float dt_sec = static_cast<float>(dt_ms) * 0.001f;

    last_frame_ms_ = now_ms;

    UpdateBlinker(now_ms, dt_sec);
    UpdateGaze(now_ms);
    UpdateExpressionMotion(now_ms);
    InterpolateEye(left_, dt_sec);
    InterpolateEye(right_, dt_sec);
    RenderFrame(now_ms);
}

void EyeEngine::DrawSingleEye(const EyeState& eye) {
    const int w = ClampInt(RoundHalfAway(eye.width), 8, 44);
    const int raw_h = ClampInt(RoundHalfAway(eye.height), 8, 44);

    // Closed-eye soft horizontal line when almost fully blinked
    if (eye.blink_squeeze >= 0.85f) {
        const int cx = ClampInt(RoundHalfAway(eye.x), w / 2 + 4, gfx::kWidth - w / 2 - 4);
        const int cy = ClampInt(RoundHalfAway(eye.y) + 2, 4, gfx::kHeight - 5);
        fb_.FillRoundRect(cx - w / 2, cy - 1, w, 2, 1, 1);
        return;
    }

    const int h = ClampInt(RoundHalfAway(static_cast<float>(raw_h) * (1.0f - 0.88f * eye.blink_squeeze)), 3, 44);
    const int x = ClampInt(RoundHalfAway(eye.x) - w / 2, 4, gfx::kWidth - w - 4);
    const int y = ClampInt(RoundHalfAway(eye.y) - h / 2, 4, gfx::kHeight - h - 4);
    const int max_r = (w < h ? w : h) / 2;
    const int r = ClampInt(RoundHalfAway(eye.corner_radius), 1, max_r);

    fb_.FillRoundRect(x, y, w, h, r, 1);

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
            for (int col = 0; col < w; ++col) {
                const float frac = (w > 1) ? static_cast<float>(col) / static_cast<float>(w - 1) : 0.5f;
                const float u = (half_w > 0.0f) ? (static_cast<float>(col) - half_w) / half_w : 0.0f;
                const float curve = 1.0f - u * u;
                const float lid_y = eye.upper_lid_l + (eye.upper_lid_r - eye.upper_lid_l) * frac;
                const int mask_bot = RoundHalfAway(
                    static_cast<float>(y) + lid_y + eye.upper_arch * curve);
                for (int py = y - 1; py <= mask_bot; ++py) {
                    fb_.SetPixel(x + col, py, 0);
                }
            }
        }
    }
}

void EyeEngine::RenderFrame(uint32_t now_ms) {
    fb_.Clear();

    DrawSingleEye(left_);
    DrawSingleEye(right_);

    // Subtle non-intrusive bottom-edge cues for Listening / Thinking
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
    }

    display::PresentFramebuffer(fb_);
}

}  // namespace jarvis::eyes

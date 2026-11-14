// =============================================================================
// JARVIS AI Desk Buddy — Animated Eye Rendering Engine (v2 Organic Companion)
//
// Attribution:
//   Non-blocking blinker, eyelid masking concept, and idle gaze architecture
//   originally inspired by Carmoruda/Jarvis (MIT License, Copyright (c) 2026
//   Carmoruda). Redesigned for JARVIS AI Desk Buddy with original organic
//   super-capsule geometry, curved eyelids, FPS-independent exponential
//   interpolation, deterministic PRNG, and 7 companion expressions.
// =============================================================================
#pragma once

#include <stdint.h>
#include "monochrome_fb.h"

namespace jarvis::eyes {

enum class Expression : uint8_t {
    kNeutral = 0,
    kHappy,
    kCurious,
    kSleepy,
    kListening,
    kThinking,
    kSpeaking
};

const char* ExpressionToString(Expression expr);

class EyeEngine {
public:
    void Begin(uint16_t fps = 50, int spacing_px = 16);

    /// Non-blocking tick; call every loop() iteration.
    void Update(uint32_t now_ms);

    /// Forces one render step at now_ms (useful for deterministic simulation).
    void UpdateStep(uint32_t now_ms);

    void SetExpression(Expression expr);
    void SetExpressionAt(Expression expr, uint32_t now_ms);
    Expression GetExpression() const { return expr_; }

    /// Forces an immediate natural blink cycle.
    void TriggerBlink(uint32_t now_ms);

    /// Sets a temporary gaze offset in pixels (-11..+11 X, -6..+6 Y).
    void SetGazeOffset(int8_t dx, int8_t dy, uint32_t hold_ms, uint32_t now_ms);

    /// Enables or disables automatic idle gaze saccades.
    void SetAutoIdleGaze(bool enabled) { auto_idle_gaze_ = enabled; }

    /// Seeds the deterministic internal PRNG (xorshift32).
    void SeedRng(uint32_t seed);

    /// Direct read-only access to the 128x64 monochrome framebuffer.
    const gfx::MonochromeFramebuffer& Framebuffer() const { return fb_; }

private:
    enum class BlinkPhase : uint8_t {
        kOpen = 0,
        kClosing,
        kHoldClosed,
        kOpening
    };

    struct EyeState {
        int base_x = 0;
        int base_y = 0;

        float x = 0.0f;
        float y = 0.0f;
        float target_x = 0.0f;
        float target_y = 0.0f;

        float width = 30.0f;
        float height = 32.0f;
        float target_width = 30.0f;
        float target_height = 32.0f;

        float corner_radius = 10.0f;
        float target_corner_radius = 10.0f;

        float lower_lid = 0.0f;
        float target_lower_lid = 0.0f;
        float lower_arch = 0.0f;
        float target_lower_arch = 0.0f;

        float upper_lid_l = 0.0f;
        float upper_lid_r = 0.0f;
        float target_upper_lid_l = 0.0f;
        float target_upper_lid_r = 0.0f;
        float upper_arch = 0.0f;
        float target_upper_arch = 0.0f;

        float blink_squeeze = 0.0f;  // 0.0 = open, 1.0 = closed
    };

    static constexpr int kDefaultEyeWidth = 30;
    static constexpr int kDefaultEyeHeight = 32;
    static constexpr int kDefaultCornerRadius = 10;

    EyeState left_;
    EyeState right_;

    Expression expr_ = Expression::kNeutral;
    int spacing_px_ = 16;

    uint32_t frame_interval_ms_ = 20;
    uint32_t last_frame_ms_ = 0;

    // Blinker state
    BlinkPhase blink_phase_ = BlinkPhase::kOpen;
    uint32_t next_blink_ms_ = 0;
    uint32_t blink_hold_until_ms_ = 0;
    bool double_blink_pending_ = false;

    // Idle gaze state
    bool auto_idle_gaze_ = true;
    uint32_t next_gaze_ms_ = 0;
    uint32_t gaze_override_until_ms_ = 0;

    // Expression-specific animation phase
    uint32_t expr_start_ms_ = 0;

    // Deterministic PRNG state (xorshift32)
    uint32_t rng_state_ = 0xA511E9B3U;

    uint32_t NextRand();
    int RandRange(int lo, int hi);

    void RecalculateBasePositions();
    void ApplyExpressionTargets();
    void UpdateBlinker(uint32_t now_ms, float dt_sec);
    void UpdateGaze(uint32_t now_ms);
    void UpdateExpressionMotion(uint32_t now_ms);
    void InterpolateEye(EyeState& eye, float dt_sec);
    void RenderFrame(uint32_t now_ms);
    void DrawSingleEye(const EyeState& eye);

    gfx::MonochromeFramebuffer fb_;
};

}  // namespace jarvis::eyes

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
    kSpeaking,
    kSurprised,
    kShy,
    kLove,
    kWink,
    kConfused,
    kMischievous,
    kSleeping
};

const char* ExpressionToString(Expression expr);

/// Visual-only personality profiles for JARVIS Eyes 3.0.
/// Does not affect Voice AI, LLM, or conversational personality.
enum class VisualProfile : uint8_t {
    kCalm = 0,
    kLively,
    kPlayful
};

const char* VisualProfileToString(VisualProfile profile);

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

    /// Sets visual-only animation personality profile (CALM, LIVELY, PLAYFUL).
    void SetVisualProfile(VisualProfile profile) { profile_ = profile; }
    VisualProfile GetVisualProfile() const { return profile_; }

    /// Enables or disables spontaneous contextual micro-expressions.
    void SetMicroExpressionsEnabled(bool enabled) { micro_expressions_enabled_ = enabled; }

    /// Seeds the deterministic internal PRNG (xorshift32).
    void SeedRng(uint32_t seed);

    /// Direct read-only access to the 128x64 monochrome framebuffer.
    const gfx::MonochromeFramebuffer& Framebuffer() const { return fb_; }

    /// Real measured duration of the last framebuffer render (in microseconds).
    uint32_t LastFrameRenderUs() const { return last_render_us_; }

    /// Real measured duration of the last physical OLED I2C transfer (in microseconds).
    uint32_t LastI2cTransferUs() const { return last_present_us_; }

    /// Smoothed effective frame rate (FPS) and dropped frame counter.
    float ActualFps() const { return actual_fps_; }
    uint32_t DroppedFrames() const { return dropped_frames_; }

private:
    enum class BlinkPhase : uint8_t {
        kOpen = 0,
        kClosing,
        kHoldClosed,
        kOpening
    };

    enum class MicroExprType : uint8_t {
        kNone = 0,
        kBrowRaise,
        kSideGlance,
        kQuickWink,
        kEyeSmile,
        kPupilPulse
    };

    struct EyeState {
        int base_x = 0;
        int base_y = 0;

        float x = 0.0f;
        float y = 0.0f;
        float target_x = 0.0f;
        float target_y = 0.0f;

        float width = 38.0f;
        float height = 38.0f;
        float target_width = 38.0f;
        float target_height = 38.0f;

        float shape_power = 2.6f;
        float target_shape_power = 2.6f;
        float taper = 0.10f;
        float target_taper = 0.10f;

        float corner_radius = 11.0f;
        float target_corner_radius = 11.0f;

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

        float pupil_dx = 0.0f;
        float target_pupil_dx = 0.0f;
        float pupil_dy = 0.0f;
        float target_pupil_dy = 0.0f;
        float pupil_radius = 7.0f;
        float target_pupil_radius = 7.0f;

        float brow_offset = 4.0f;
        float target_brow_offset = 4.0f;
        float brow_tilt = 0.0f;
        float target_brow_tilt = 0.0f;
        float brow_arch = 2.2f;
        float target_brow_arch = 2.2f;

        float blink_squeeze = 0.0f;  // 0.0 = open, 1.0 = closed
    };

    static constexpr int kDefaultEyeWidth = 38;
    static constexpr int kDefaultEyeHeight = 38;
    static constexpr int kDefaultCornerRadius = 11;

    EyeState left_;
    EyeState right_;

    Expression expr_ = Expression::kNeutral;
    int spacing_px_ = 16;

    uint32_t frame_interval_ms_ = 33;
    uint32_t last_frame_ms_ = 0;
    uint32_t last_render_us_ = 0;
    uint32_t last_present_us_ = 0;
    float actual_fps_ = 30.0f;
    uint32_t dropped_frames_ = 0;

    // Visual personality profile (LIVELY default = "Amichetto Vivace")
    VisualProfile profile_ = VisualProfile::kLively;

    // Blinker state
    BlinkPhase blink_phase_ = BlinkPhase::kOpen;
    uint32_t next_blink_ms_ = 0;
    uint32_t blink_hold_until_ms_ = 0;
    bool double_blink_pending_ = false;

    // Idle gaze & micro-saccade state
    bool auto_idle_gaze_ = true;
    uint32_t next_gaze_ms_ = 0;
    uint32_t gaze_override_until_ms_ = 0;
    bool gaze_is_micro_ = false;

    // Micro-expression state (contextual, never mutates expr_)
    bool micro_expressions_enabled_ = true;
    MicroExprType micro_expr_ = MicroExprType::kNone;
    uint32_t micro_expr_until_ms_ = 0;
    uint32_t next_micro_expr_ms_ = 0;

    // Transition speed multiplier (boosted briefly on SURPRISED or profile changes)
    float transition_boost_ = 1.0f;

    // Expression-specific animation phase
    uint32_t expr_start_ms_ = 0;

    // Deterministic PRNG state (xorshift32)
    uint32_t rng_state_ = 0xA511E9B3U;

    uint32_t NextRand();
    int RandRange(int lo, int hi);
    float ProfileSpeedScale() const;
    float ProfileGazeFreqScale() const;
    float ProfileMicroFreqScale() const;
    float ProfileBlinkFreqScale() const;

    void RecalculateBasePositions();
    void ApplyExpressionTargets();
    void UpdateBlinker(uint32_t now_ms, float dt_sec);
    void UpdateGaze(uint32_t now_ms);
    void UpdateMicroExpressions(uint32_t now_ms);
    void UpdateExpressionMotion(uint32_t now_ms);
    void InterpolateEye(EyeState& eye, float dt_sec);
    void RenderToFramebuffer(uint32_t now_ms);
    void RenderFrame(uint32_t now_ms);
    void DrawSingleEye(const EyeState& eye);
    void DrawHappyCrescent(const EyeState& eye);
    void DrawPlumpHeart(int cx, int cy);
    void DrawSleepingLash(const EyeState& eye);
    void DrawHeart(int cx, int cy, int scale);
    void DrawGlyph(int ox, int oy, const char* const* pattern, uint8_t rows, int scale);
    void DrawWinkEye(const EyeState& eye);
    void DrawSleepingEye(const EyeState& eye);

    gfx::MonochromeFramebuffer fb_;
};

}  // namespace jarvis::eyes

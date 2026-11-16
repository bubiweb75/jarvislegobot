// =============================================================================
// JARVIS AI Desk Buddy — Non-Blocking Companion State Machine & Host Link
//
// Designed for standalone demo cycling, physical button interaction (GPIO 47),
// and future Raspberry Pi UART/USB-CDC host state orchestration.
// =============================================================================
#pragma once

#include <stdint.h>
#include "eye_engine.h"
#ifdef JARVIS_ENABLE_TOUCH
#include "touch_manager.h"
#endif

namespace jarvis::state {

class StateMachine {
public:
    void Begin(eyes::EyeEngine& eyes_ref, bool start_auto_demo = true);

    /// Non-blocking update for button debounce, serial commands, and auto-demo.
    void Update(uint32_t now_ms);

    void SetExpression(eyes::Expression expr, bool disable_auto_demo = true);
    bool IsAutoDemoEnabled() const { return auto_demo_enabled_; }
    void SetOledDetectedAddr(uint8_t addr) { oled_addr_ = addr; }

private:
    eyes::EyeEngine* eyes_ = nullptr;
    uint8_t oled_addr_ = 0;

    // Auto-demo cycling state
    bool auto_demo_enabled_ = true;
    uint8_t demo_index_ = 0;
    uint32_t last_demo_switch_ms_ = 0;
    static constexpr uint32_t kDemoIntervalMs = 5000;

    // Debounced button state (GPIO 47, active LOW)
    bool btn_last_raw_ = true;
    bool btn_stable_ = true;
    uint32_t btn_last_change_ms_ = 0;
    uint32_t btn_press_start_ms_ = 0;
    bool btn_long_fired_ = false;
    static constexpr uint32_t kDebounceMs = 35;
    static constexpr uint32_t kLongPressMs = 1500;

    // Non-blocking Serial command line buffer (Raspberry Pi host ready)
    static constexpr uint8_t kRxBufSize = 64;
    char rx_buf_[kRxBufSize] = {};
    uint8_t rx_len_ = 0;

    void PollButton(uint32_t now_ms);
    void PollSerial(uint32_t now_ms);
    void HandleCommand(const char* cmd, uint32_t now_ms);
    void CycleNextExpression();
    void PrintStatus() const;
    void PrintDiagnostics(uint32_t now_ms) const;

#ifdef JARVIS_ENABLE_TOUCH
    touch::TouchManager touch_{};
    bool touch_reaction_active_ = false;
    bool touch_long_holding_ = false;
    uint32_t touch_reaction_until_ms_ = 0;
    eyes::Expression saved_expr_ = eyes::Expression::kNeutral;
    bool saved_auto_demo_ = true;

    void PollTouch(uint32_t now_ms);
    void HandleTouchEvent(touch::TouchEvent ev, uint32_t now_ms);
    void HandleTouchRelease(uint32_t now_ms);
    void CancelTouchReaction();
#endif
};

}  // namespace jarvis::state

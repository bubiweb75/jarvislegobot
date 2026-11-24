// =============================================================================
// JARVIS AI Desk Buddy — Capacitive Touch Manager (FASE 11.1)
//
// Non-blocking software debounce and gesture classifier for TTP223 / TTP223B
// digital touch sensor (or Wokwi virtual active-HIGH touch button on GPIO1).
//
// Events emitted:
//   - kSingle : confirmed only after double_tap_window_ms expires without 2nd tap
//   - kDouble : 2nd short tap released within double_tap_window_ms
//   - kLong   : continuous press >= long_press_ms (fires once per press)
//   - released flag : true on any valid release transition (TOUCH_RELEASE)
// =============================================================================
#pragma once

#include <stdint.h>

namespace jarvis::touch {

enum class TouchEvent : uint8_t {
    kNone = 0,
    kSingle,
    kDouble,
    kLong,
};

struct TouchConfig {
    bool active_high = true;              // TTP223 default: HIGH when touched
    uint32_t debounce_ms = 40;            // Software debounce window
    uint32_t double_tap_window_ms = 350;  // Max gap after 1st release for 2nd tap
    uint32_t long_press_ms = 1200;        // Hold threshold for TOUCH_LONG
};

struct TouchUpdateResult {
    TouchEvent event = TouchEvent::kNone;
    bool released = false;
    bool is_pressed = false;
};

class TouchManager {
public:
    void Begin(bool initial_raw_level = false, const TouchConfig& config = TouchConfig{});
    void SetEnabled(bool enabled) { enabled_ = enabled; }
    bool IsEnabled() const { return enabled_; }
    const TouchConfig& Config() const { return config_; }

    /// Non-blocking update; call every loop tick with digitalRead(pin).
    TouchUpdateResult Update(bool raw_level, uint32_t now_ms);

    /// Reset pending gesture timers without changing configuration.
    void Reset(bool current_raw_level = false, uint32_t now_ms = 0);

private:
    TouchConfig config_{};
    bool enabled_ = true;

    bool last_raw_active_ = false;
    bool stable_active_ = false;
    uint32_t last_change_ms_ = 0;
    uint32_t press_start_ms_ = 0;
    uint32_t first_release_ms_ = 0;
    bool long_fired_ = false;
    bool waiting_second_tap_ = false;
};

}  // namespace jarvis::touch

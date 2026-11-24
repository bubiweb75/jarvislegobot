// =============================================================================
// JARVIS AI Desk Buddy — Capacitive Touch Manager Implementation (FASE 11.1)
// =============================================================================
#include "touch_manager.h"

namespace jarvis::touch {

void TouchManager::Begin(bool initial_raw_level, const TouchConfig& config) {
    config_ = config;
    const bool active = config_.active_high ? initial_raw_level : !initial_raw_level;
    last_raw_active_ = active;
    stable_active_ = active;
    last_change_ms_ = 0;
    press_start_ms_ = 0;
    first_release_ms_ = 0;
    long_fired_ = false;
    waiting_second_tap_ = false;
}

void TouchManager::Reset(bool current_raw_level, uint32_t now_ms) {
    const bool active = config_.active_high ? current_raw_level : !current_raw_level;
    last_raw_active_ = active;
    stable_active_ = active;
    last_change_ms_ = now_ms;
    press_start_ms_ = now_ms;
    first_release_ms_ = 0;
    long_fired_ = false;
    waiting_second_tap_ = false;
}

TouchUpdateResult TouchManager::Update(bool raw_level, uint32_t now_ms) {
    TouchUpdateResult out{};
    if (!enabled_) {
        return out;
    }

    const bool raw_active = config_.active_high ? raw_level : !raw_level;
    if (raw_active != last_raw_active_) {
        last_raw_active_ = raw_active;
        last_change_ms_ = now_ms;
    }

    if ((now_ms - last_change_ms_) >= config_.debounce_ms && raw_active != stable_active_) {
        stable_active_ = raw_active;
        if (stable_active_) {
            press_start_ms_ = now_ms;
            long_fired_ = false;
        } else {
            out.released = true;
            if (!long_fired_) {
                if (waiting_second_tap_ &&
                    (now_ms - first_release_ms_) <= config_.double_tap_window_ms) {
                    waiting_second_tap_ = false;
                    out.event = TouchEvent::kDouble;
                } else {
                    waiting_second_tap_ = true;
                    first_release_ms_ = now_ms;
                }
            } else {
                waiting_second_tap_ = false;
            }
        }
    }

    if (stable_active_ && !long_fired_ &&
        (now_ms - press_start_ms_) >= config_.long_press_ms) {
        long_fired_ = true;
        waiting_second_tap_ = false;
        out.event = TouchEvent::kLong;
    }

    if (!stable_active_ && waiting_second_tap_ &&
        (now_ms - first_release_ms_) > config_.double_tap_window_ms) {
        waiting_second_tap_ = false;
        out.event = TouchEvent::kSingle;
    }

    out.is_pressed = stable_active_;
    return out;
}

}  // namespace jarvis::touch

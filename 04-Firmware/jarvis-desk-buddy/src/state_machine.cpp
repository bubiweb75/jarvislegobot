// =============================================================================
// JARVIS AI Desk Buddy — Non-Blocking Companion State Machine Implementation
// =============================================================================
#include "state_machine.h"

#include <Arduino.h>
#include <ctype.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "display_driver.h"
#include "pinout_config.h"
#include "sensor_stub.h"

namespace jarvis::state {

namespace {

constexpr eyes::Expression kCycleOrder[] = {
    eyes::Expression::kNeutral,
    eyes::Expression::kHappy,
    eyes::Expression::kCurious,
    eyes::Expression::kListening,
    eyes::Expression::kThinking,
    eyes::Expression::kSpeaking,
    eyes::Expression::kSleepy,
};
constexpr uint8_t kCycleCount = sizeof(kCycleOrder) / sizeof(kCycleOrder[0]);

void TrimAndUpper(char* s) {
    // Strip trailing whitespace/CR/LF
    size_t len = strlen(s);
    while (len > 0 && (s[len - 1] == '\r' || s[len - 1] == '\n' ||
                       s[len - 1] == ' ' || s[len - 1] == '\t')) {
        s[--len] = '\0';
    }
    for (size_t i = 0; i < len; ++i) {
        s[i] = static_cast<char>(toupper(static_cast<unsigned char>(s[i])));
    }
}

}  // namespace

void StateMachine::Begin(eyes::EyeEngine& eyes_ref, bool start_auto_demo) {
    eyes_ = &eyes_ref;
    auto_demo_enabled_ = start_auto_demo;
    demo_index_ = 0;
    last_demo_switch_ms_ = millis();

    pinMode(pins::kButtonActivate, INPUT_PULLUP);
    btn_last_raw_ = (digitalRead(pins::kButtonActivate) == HIGH);
    btn_stable_ = btn_last_raw_;
    btn_last_change_ms_ = last_demo_switch_ms_;

    eyes_->SetExpression(kCycleOrder[demo_index_]);
}

void StateMachine::SetExpression(eyes::Expression expr, bool disable_auto_demo) {
    if (disable_auto_demo) {
        auto_demo_enabled_ = false;
    }
    if (eyes_ != nullptr) {
        eyes_->SetExpression(expr);
    }
    Serial.print(F("EVENT:STATE="));
    Serial.println(eyes::ExpressionToString(expr));
}

void StateMachine::CycleNextExpression() {
    demo_index_ = static_cast<uint8_t>((demo_index_ + 1U) % kCycleCount);
    if (eyes_ != nullptr) {
        eyes_->SetExpression(kCycleOrder[demo_index_]);
    }
    Serial.print(F("EVENT:STATE="));
    Serial.println(eyes::ExpressionToString(kCycleOrder[demo_index_]));
}

void StateMachine::PollButton(uint32_t now_ms) {
    const bool raw = (digitalRead(pins::kButtonActivate) == HIGH);
    if (raw != btn_last_raw_) {
        btn_last_raw_ = raw;
        btn_last_change_ms_ = now_ms;
    }

    if ((now_ms - btn_last_change_ms_) >= kDebounceMs && raw != btn_stable_) {
        btn_stable_ = raw;
        if (!btn_stable_) {
            // Button pressed (active LOW)
            btn_press_start_ms_ = now_ms;
            btn_long_fired_ = false;
        } else {
            // Button released
            if (!btn_long_fired_) {
                auto_demo_enabled_ = false;
                CycleNextExpression();
            }
        }
    }

    if (!btn_stable_ && !btn_long_fired_ &&
        (now_ms - btn_press_start_ms_) >= kLongPressMs) {
        btn_long_fired_ = true;
        auto_demo_enabled_ = !auto_demo_enabled_;
        last_demo_switch_ms_ = now_ms;
        Serial.print(F("EVENT:AUTO_DEMO="));
        Serial.println(auto_demo_enabled_ ? F("ON") : F("OFF"));
    }
}

void StateMachine::PollSerial(uint32_t now_ms) {
    while (Serial.available() > 0) {
        const char ch = static_cast<char>(Serial.read());
        if (ch == '\n' || ch == '\r') {
            if (rx_len_ > 0) {
                rx_buf_[rx_len_] = '\0';
                HandleCommand(rx_buf_, now_ms);
                rx_len_ = 0;
            }
        } else if (rx_len_ < (kRxBufSize - 1)) {
            rx_buf_[rx_len_++] = ch;
        } else {
            // Line too long; reset cleanly without blocking
            rx_len_ = 0;
        }
    }
}

void StateMachine::HandleCommand(const char* raw_cmd, uint32_t now_ms) {
    char cmd[kRxBufSize];
    strncpy(cmd, raw_cmd, kRxBufSize - 1);
    cmd[kRxBufSize - 1] = '\0';
    TrimAndUpper(cmd);
    if (cmd[0] == '\0') return;

    const char* arg = cmd;
    if (strncmp(cmd, "STATE:", 6) == 0) {
        arg = cmd + 6;
    } else if (strncmp(cmd, "CMD:", 4) == 0) {
        arg = cmd + 4;
    }

    if (strcmp(arg, "NEUTRAL") == 0 || strcmp(arg, "IDLE") == 0) {
        SetExpression(eyes::Expression::kNeutral, true);
    } else if (strcmp(arg, "HAPPY") == 0) {
        SetExpression(eyes::Expression::kHappy, true);
    } else if (strcmp(arg, "CURIOUS") == 0) {
        SetExpression(eyes::Expression::kCurious, true);
    } else if (strcmp(arg, "SLEEPY") == 0) {
        SetExpression(eyes::Expression::kSleepy, true);
    } else if (strcmp(arg, "LISTENING") == 0) {
        SetExpression(eyes::Expression::kListening, true);
    } else if (strcmp(arg, "THINKING") == 0) {
        SetExpression(eyes::Expression::kThinking, true);
    } else if (strcmp(arg, "SPEAKING") == 0) {
        SetExpression(eyes::Expression::kSpeaking, true);
    } else if (strcmp(arg, "SURPRISED") == 0) {
        SetExpression(eyes::Expression::kSurprised, true);
    } else if (strcmp(arg, "SHY") == 0) {
        SetExpression(eyes::Expression::kShy, true);
    } else if (strcmp(arg, "LOVE") == 0) {
        SetExpression(eyes::Expression::kLove, true);
    } else if (strcmp(arg, "WINK") == 0) {
        SetExpression(eyes::Expression::kWink, true);
    } else if (strcmp(arg, "CONFUSED") == 0) {
        SetExpression(eyes::Expression::kConfused, true);
    } else if (strcmp(arg, "MISCHIEVOUS") == 0) {
        SetExpression(eyes::Expression::kMischievous, true);
    } else if (strcmp(arg, "SLEEPING") == 0) {
        SetExpression(eyes::Expression::kSleeping, true);
    } else if (strcmp(arg, "BLINK") == 0) {
        if (eyes_ != nullptr) eyes_->TriggerBlink(now_ms);
        Serial.println(F("OK:BLINK"));
    } else if (strncmp(arg, "LOOK:", 5) == 0) {
        int dx = 0;
        int dy = 0;
        if (sscanf(arg + 5, "%d,%d", &dx, &dy) == 2 && eyes_ != nullptr) {
            if (dx < -11 || dx > 11 || dy < -6 || dy > 6) {
                Serial.println(F("ERR:LOOK_RANGE (dx:-11..11,dy:-6..6)"));
            } else {
                eyes_->SetGazeOffset(static_cast<int8_t>(dx), static_cast<int8_t>(dy), 2000U, now_ms);
                Serial.println(F("OK:LOOK"));
            }
        } else {
            Serial.println(F("ERR:LOOK_SYNTAX (expected LOOK:dx,dy)"));
        }
    } else if (strcmp(arg, "AUTO:ON") == 0) {
        auto_demo_enabled_ = true;
        last_demo_switch_ms_ = now_ms;
        Serial.println(F("OK:AUTO=ON"));
    } else if (strcmp(arg, "AUTO:OFF") == 0) {
        auto_demo_enabled_ = false;
        Serial.println(F("OK:AUTO=OFF"));
    } else if (strcmp(arg, "PING") == 0) {
        Serial.println(F("PONG"));
    } else if (strcmp(arg, "STATUS") == 0) {
        PrintStatus();
    } else if (strcmp(arg, "DIAG") == 0) {
        PrintDiagnostics(now_ms);
    } else if (strcmp(arg, "HELP") == 0) {
        Serial.println(F("COMMANDS: IDLE|NEUTRAL|HAPPY|CURIOUS|SLEEPY|LISTENING|THINKING|SPEAKING|SURPRISED|SHY|LOVE|WINK|CONFUSED|MISCHIEVOUS|SLEEPING|BLINK|LOOK:dx,dy|AUTO:ON|AUTO:OFF|STATUS|DIAG|PING"));
    } else {
        Serial.print(F("ERR:UNKNOWN_CMD="));
        Serial.println(cmd);
    }
}

void StateMachine::PrintStatus() const {
    Serial.print(F("OK:STATE="));
    Serial.print(eyes_ ? eyes::ExpressionToString(eyes_->GetExpression()) : "NONE");
    Serial.print(F(";AUTO="));
    Serial.print(auto_demo_enabled_ ? F("ON") : F("OFF"));
    Serial.print(F(";DRIVER="));
    Serial.println(kOledDriverName);
}

void StateMachine::PrintDiagnostics(uint32_t now_ms) const {
    Serial.printf("OK:DIAG;STATE=%s;UPTIME_MS=%lu;FREE_HEAP=%lu;FREE_PSRAM=%lu;OLED_ADDR=0x%02X;DRIVER=%s;SENSORS=%s\n",
                  eyes_ ? eyes::ExpressionToString(eyes_->GetExpression()) : "NONE",
                  static_cast<unsigned long>(now_ms),
                  static_cast<unsigned long>(ESP.getFreeHeap()),
                  static_cast<unsigned long>(ESP.getFreePsram()),
                  oled_addr_,
                  kOledDriverName,
                  sensors::SensorBridgeStub::StatusLabel());
}

void StateMachine::Update(uint32_t now_ms) {
    PollButton(now_ms);
    PollSerial(now_ms);

    if (auto_demo_enabled_ && (now_ms - last_demo_switch_ms_) >= kDemoIntervalMs) {
        last_demo_switch_ms_ = now_ms;
        CycleNextExpression();
    }
}

}  // namespace jarvis::state

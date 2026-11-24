#pragma once

#include <Arduino.h>

// Set to 1 to enable verbose diagnostic Serial logs; keep 0 to save Flash in production builds.
#ifndef JARVIS_DEBUG_VERBOSE
#define JARVIS_DEBUG_VERBOSE 0
#endif

#if JARVIS_DEBUG_VERBOSE
#define JLOG_V(...) Serial.printf(__VA_ARGS__)
#define JLOG_VLN(x) Serial.println(F(x))
#else
#define JLOG_V(...) do {} while (0)
#define JLOG_VLN(x) do {} while (0)
#endif

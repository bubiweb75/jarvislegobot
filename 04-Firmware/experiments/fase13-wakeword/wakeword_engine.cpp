#include "wakeword_engine.h"
#include "hey_jarvis_model.h"

#include <Arduino.h>
#include <Chirale_TensorFlowLite.h>
#include <esp_heap_caps.h>
#include <math.h>
#include <string.h>

#include "tensorflow/lite/experimental/microfrontend/lib/frontend.h"
#include "tensorflow/lite/experimental/microfrontend/lib/frontend_util.h"
#include "tensorflow/lite/micro/micro_allocator.h"
#include "tensorflow/lite/micro/micro_interpreter.h"
#include "tensorflow/lite/micro/micro_mutable_op_resolver.h"
#include "tensorflow/lite/micro/micro_resource_variable.h"
#include "tensorflow/lite/schema/schema_generated.h"

namespace jarvis::wakeword {

namespace {
tflite::MicroMutableOpResolver<13> g_op_resolver;
bool g_ops_registered = false;

bool EnsureOpsRegistered() {
  if (g_ops_registered) return true;
  if (g_op_resolver.AddAssignVariable() != kTfLiteOk) return false;
  if (g_op_resolver.AddCallOnce() != kTfLiteOk) return false;
  if (g_op_resolver.AddConcatenation() != kTfLiteOk) return false;
  if (g_op_resolver.AddConv2D() != kTfLiteOk) return false;
  if (g_op_resolver.AddDepthwiseConv2D() != kTfLiteOk) return false;
  if (g_op_resolver.AddFullyConnected() != kTfLiteOk) return false;
  if (g_op_resolver.AddLogistic() != kTfLiteOk) return false;
  if (g_op_resolver.AddQuantize() != kTfLiteOk) return false;
  if (g_op_resolver.AddReadVariable() != kTfLiteOk) return false;
  if (g_op_resolver.AddReshape() != kTfLiteOk) return false;
  if (g_op_resolver.AddStridedSlice() != kTfLiteOk) return false;
  if (g_op_resolver.AddVarHandle() != kTfLiteOk) return false;
  g_ops_registered = true;
  return true;
}

uint16_t ComputeRms16(const int16_t* pcm16, size_t n) {
  if (!pcm16 || n == 0) return 0;
  uint64_t sum_sq = 0;
  for (size_t i = 0; i < n; ++i) {
    const int32_t v = pcm16[i];
    sum_sq += static_cast<uint64_t>(v * v);
  }
  return static_cast<uint16_t>(sqrt(static_cast<double>(sum_sq) / static_cast<double>(n)));
}
}  // namespace

const char* WakeStateName(WakeState s) {
  switch (s) {
    case WakeState::kBoot:
      return "BOOT";
    case WakeState::kIdle:
      return "IDLE";
    case WakeState::kWakeDetected:
      return "WAKE_DETECTED";
    case WakeState::kCommandListening:
      return "COMMAND_LISTENING";
    case WakeState::kProcessing:
      return "PROCESSING";
    case WakeState::kSpeaking:
      return "SPEAKING";
    case WakeState::kError:
      return "ERROR";
    case WakeState::kRecovery:
      return "RECOVERY";
    default:
      return "UNKNOWN";
  }
}

MicroWakeWordDetector::~MicroWakeWordDetector() {
  if (frontend_ready_ && frontend_state_) {
    FrontendFreeStateContents(frontend_state_);
    frontend_ready_ = false;
  }
  delete frontend_state_;
  frontend_state_ = nullptr;
  delete interpreter_;
  interpreter_ = nullptr;
  if (tensor_arena_) {
    heap_caps_free(tensor_arena_);
    tensor_arena_ = nullptr;
  }
}

bool MicroWakeWordDetector::Begin() {
  if (!EnsureOpsRegistered()) {
    Serial.println(F("[WAKE_ERROR] Failed to register TFLite Micro ops"));
    return false;
  }

  const tflite::Model* model = tflite::GetModel(g_hey_jarvis_tflite);
  if (!model || model->version() != TFLITE_SCHEMA_VERSION) {
    Serial.println(F("[WAKE_ERROR] Invalid TFLite model schema"));
    return false;
  }
  Serial.printf("[WAKE_MODEL_LOADED] name=%s bytes=%u\n",
                ModelName(), static_cast<unsigned>(g_hey_jarvis_tflite_len));

  tensor_arena_ = static_cast<uint8_t*>(
      heap_caps_aligned_alloc(16, kTensorArenaBytes, MALLOC_CAP_INTERNAL | MALLOC_CAP_8BIT));
  if (!tensor_arena_ && psramFound()) {
    tensor_arena_ = static_cast<uint8_t*>(
        heap_caps_aligned_alloc(16, kTensorArenaBytes, MALLOC_CAP_SPIRAM | MALLOC_CAP_8BIT));
  }
  if (!tensor_arena_) {
    Serial.println(F("[WAKE_ERROR] Tensor arena allocation failed"));
    return false;
  }

  allocator_ = tflite::MicroAllocator::Create(tensor_arena_, kTensorArenaBytes);
  if (!allocator_) {
    Serial.println(F("[WAKE_ERROR] MicroAllocator creation failed"));
    return false;
  }
  resource_vars_ = tflite::MicroResourceVariables::Create(allocator_, 8);
  interpreter_ = new tflite::MicroInterpreter(model, g_op_resolver, allocator_, resource_vars_);
  if (!interpreter_ || interpreter_->AllocateTensors() != kTfLiteOk) {
    Serial.println(F("[WAKE_ERROR] AllocateTensors failed"));
    return false;
  }
  arena_used_bytes_ = interpreter_->arena_used_bytes();
  Serial.printf("[WAKE_ARENA_BYTES] used=%u alloc=%u\n",
                static_cast<unsigned>(arena_used_bytes_),
                static_cast<unsigned>(kTensorArenaBytes));

  frontend_state_ = new FrontendState();
  FrontendConfig cfg{};
  FrontendFillConfigWithDefaults(&cfg);
  cfg.window.size_ms = 30;
  cfg.window.step_size_ms = 10;
  cfg.filterbank.num_channels = kFeatureBins;
  cfg.filterbank.lower_band_limit = 125.0f;
  cfg.filterbank.upper_band_limit = 7500.0f;
  cfg.noise_reduction.smoothing_bits = 10;
  cfg.noise_reduction.even_smoothing = 0.025f;
  cfg.noise_reduction.odd_smoothing = 0.06f;
  cfg.noise_reduction.min_signal_remaining = 0.05f;
  cfg.pcan_gain_control.enable_pcan = 1;
  cfg.pcan_gain_control.strength = 0.95f;
  cfg.pcan_gain_control.offset = 80.0f;
  cfg.pcan_gain_control.gain_bits = 21;
  cfg.log_scale.enable_log = 1;
  cfg.log_scale.scale_shift = 6;

  if (!FrontendPopulateState(&cfg, frontend_state_, 16000)) {
    Serial.println(F("[WAKE_ERROR] FrontendPopulateState failed"));
    return false;
  }
  frontend_ready_ = true;
  Reset();
  Serial.println(F("[WAKE_INIT_OK] microWakeWord hey_jarvis ready"));
  return true;
}

void MicroWakeWordDetector::Reset() {
  feature_frame_idx_ = 0;
  prob_idx_ = 0;
  prob_count_ = 0;
  memset(feature_buf_, -128, sizeof(feature_buf_));
  memset(prob_history_, 0, sizeof(prob_history_));
  if (frontend_ready_ && frontend_state_) {
    FrontendReset(frontend_state_);
  }
}

WakeDetectionResult MicroWakeWordDetector::ProcessFrame10ms(const int16_t* pcm16, size_t n_samples) {
  WakeDetectionResult res{};
  if (!pcm16 || n_samples == 0 || !interpreter_ || !frontend_ready_) return res;
  res.frame_rms = ComputeRms16(pcm16, n_samples);

  size_t num_samples_read = 0;
  FrontendOutput out = FrontendProcessSamples(frontend_state_, pcm16, n_samples, &num_samples_read);
  if (out.size != kFeatureBins || !out.values) {
    return res;
  }

  // Quantize 16-bit microfrontend log-mel values (~0..666) to INT8 [-128, 127]
  int8_t* dst = &feature_buf_[feature_frame_idx_ * kFeatureBins];
  for (size_t i = 0; i < kFeatureBins; ++i) {
    int32_t q = static_cast<int32_t>(roundf(static_cast<float>(out.values[i]) * (255.0f / 666.0f))) - 128;
    if (q < -128) q = -128;
    if (q > 127) q = 127;
    dst[i] = static_cast<int8_t>(q);
  }
  feature_frame_idx_++;

  if (feature_frame_idx_ < kFramesPerInvoke) {
    return res;
  }
  feature_frame_idx_ = 0;

  TfLiteTensor* input = interpreter_->input(0);
  TfLiteTensor* output = interpreter_->output(0);
  if (!input || !output || input->bytes < sizeof(feature_buf_)) {
    return res;
  }
  memcpy(input->data.int8, feature_buf_, sizeof(feature_buf_));

  const uint32_t t0 = micros();
  if (interpreter_->Invoke() != kTfLiteOk) {
    Serial.println(F("[WAKE_ERROR] Invoke failed"));
    return res;
  }
  res.inference_us = micros() - t0;
  res.ran_inference = true;

  // Output tensor is UINT8 [1, 1] with scale = 1/256, zp = 0
  res.confidence = static_cast<float>(output->data.uint8[0]) / 256.0f;

  prob_history_[prob_idx_] = res.confidence;
  prob_idx_ = (prob_idx_ + 1U) % kSlidingWindowSize;
  if (prob_count_ < kSlidingWindowSize) prob_count_++;

  float sum = 0.0f;
  for (size_t i = 0; i < prob_count_; ++i) sum += prob_history_[i];
  res.smoothed_confidence = (prob_count_ > 0) ? (sum / static_cast<float>(prob_count_)) : 0.0f;
  res.detected = (prob_count_ == kSlidingWindowSize) && (res.smoothed_confidence >= kProbabilityCutoff);
  return res;
}

bool PreRollRingBuffer::AllocatePsram() {
  if (buf_) return true;
  if (psramFound()) {
    buf_ = static_cast<int16_t*>(ps_malloc(kCapacitySamples * sizeof(int16_t)));
  } else {
    buf_ = static_cast<int16_t*>(malloc(kCapacitySamples * sizeof(int16_t)));
  }
  Clear();
  return buf_ != nullptr;
}

void PreRollRingBuffer::Clear() {
  head_ = 0;
  count_ = 0;
}

void PreRollRingBuffer::Push(const int16_t* samples, size_t count) {
  if (!buf_ || !samples || count == 0) return;
  for (size_t i = 0; i < count; ++i) {
    buf_[head_] = samples[i];
    head_ = (head_ + 1U) % kCapacitySamples;
    if (count_ < kCapacitySamples) {
      count_++;
    }
  }
}

size_t PreRollRingBuffer::DrainTo(int16_t* dst, size_t max_samples) {
  if (!buf_ || !dst || count_ == 0 || max_samples == 0) return 0;
  const size_t n = (count_ < max_samples) ? count_ : max_samples;
  const size_t start = (head_ + kCapacitySamples - count_) % kCapacitySamples;
  for (size_t i = 0; i < n; ++i) {
    dst[i] = buf_[(start + i) % kCapacitySamples];
  }
  Clear();
  return n;
}

}  // namespace jarvis::wakeword

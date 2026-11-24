import unittest


class VoiceActivityDetectorModel:
    """Mirror of vad_controller.h for deterministic host unit testing."""

    MIN_NOISE_RMS = 80
    MAX_NOISE_RMS = 1500
    MIN_SPEECH_RMS = 360
    MIN_SILENCE_RMS = 220
    SPEECH_SNR = 2.4
    SILENCE_SNR = 1.5
    SPEECH_START_CHUNKS = 4
    POST_WAKE_HOLDOFF_MS = 300
    END_OF_SPEECH_SILENCE_MS = 1100
    NO_SPEECH_TIMEOUT_MS = 2500

    def __init__(self, initial_rms=180):
        self.noise_floor_rms = self._clamp(initial_rms)
        self.session_start_ms = 0
        self.last_speech_ms = 0
        self.consecutive_speech = 0
        self.speech_started = False

    def _clamp(self, v):
        return max(self.MIN_NOISE_RMS, min(self.MAX_NOISE_RMS, int(v)))

    def update_ambient_rms(self, chunk_rms):
        if chunk_rms > self.noise_floor_rms * 3 and chunk_rms > 600:
            return
        self.noise_floor_rms = self._clamp(0.95 * self.noise_floor_rms + 0.05 * chunk_rms)

    def speech_threshold(self):
        return max(self.MIN_SPEECH_RMS, int(self.noise_floor_rms * self.SPEECH_SNR))

    def silence_threshold(self):
        return max(self.MIN_SILENCE_RMS, int(self.noise_floor_rms * self.SILENCE_SNR))

    def start_session(self, start_ms):
        self.session_start_ms = start_ms
        self.last_speech_ms = start_ms
        self.consecutive_speech = 0
        self.speech_started = False

    def process_chunk(self, chunk_rms, now_ms):
        if not self.speech_started:
            if (now_ms - self.session_start_ms) < self.POST_WAKE_HOLDOFF_MS:
                self.consecutive_speech = 0
                return "CONTINUE"
            if chunk_rms >= self.speech_threshold():
                self.consecutive_speech += 1
                if self.consecutive_speech >= self.SPEECH_START_CHUNKS:
                    self.speech_started = True
                    self.last_speech_ms = now_ms
            else:
                self.consecutive_speech = 0
                if (now_ms - self.session_start_ms) >= self.NO_SPEECH_TIMEOUT_MS:
                    return "STOP_NO_SPEECH"
            return "CONTINUE"
        if chunk_rms >= self.silence_threshold():
            self.last_speech_ms = now_ms
        elif (now_ms - self.last_speech_ms) >= self.END_OF_SPEECH_SILENCE_MS:
            return "STOP_END_OF_SPEECH"
        return "CONTINUE"


class PreRollRingModel:
    CAPACITY = 8000

    def __init__(self):
        self.buf = [0] * self.CAPACITY
        self.head = 0
        self.count = 0

    def push(self, samples):
        for s in samples:
            self.buf[self.head] = s
            self.head = (self.head + 1) % self.CAPACITY
            if self.count < self.CAPACITY:
                self.count += 1

    def drain_chunk(self, max_samples):
        n = min(self.count, max_samples)
        if n == 0:
            return []
        start = (self.head + self.CAPACITY - self.count) % self.CAPACITY
        out = [self.buf[(start + i) % self.CAPACITY] for i in range(n)]
        self.count -= n
        return out


class RobotStateMachineModel:
    GUARD_MS = 1500
    DMA_DISCARD_FRAMES = 20
    MAX_RECORD_MS = 8000

    def __init__(self):
        self.state = "IDLE"
        self.guard_until_ms = 0
        self.dma_discard_frames = 0
        self.idle_wake_active = True
        self.recording_from_wake = False

    def transition(self, next_state, now_ms, from_net_boot=False):
        if self.state == next_state:
            return
        self.state = next_state
        if next_state == "IDLE":
            self.recording_from_wake = False
            self.idle_wake_active = True
            self.dma_discard_frames = 0 if from_net_boot else self.DMA_DISCARD_FRAMES
            self.guard_until_ms = now_ms if from_net_boot else (now_ms + self.GUARD_MS)
        else:
            self.idle_wake_active = False

    def process_idle_frame(self, now_ms, smoothed_conf, detected):
        if not (self.state == "IDLE" and self.idle_wake_active):
            return False
        if self.dma_discard_frames > 0:
            self.dma_discard_frames -= 1
            return False
        if now_ms < self.guard_until_ms:
            if smoothed_conf >= 0.30 and (self.guard_until_ms - now_ms) < 150:
                self.guard_until_ms = now_ms + 150
            return False
        if detected:
            self.recording_from_wake = True
            self.transition("LISTENING", now_ms)
            return True
        return False

    def on_wake_detected(self, now_ms):
        return self.process_idle_frame(now_ms, 0.0, True)


class WriteZeroFlushModel:
    """Mirror of AudioPlayback::WriteZeroFlush() chunking and bounds checks."""

    CHUNK_FRAMES = 256
    BYTES_PER_FRAME = 4  # 2 channels * sizeof(int16_t)
    BUF_BYTES = CHUNK_FRAMES * BYTES_PER_FRAME  # 1024 B
    MAX_ZERO_RETRIES = 3

    def __init__(self, write_fn):
        self.write_fn = write_fn
        self.bytes_written = 0
        self.partial_writes = 0
        self.i2s_errors = 0
        self.last_err = 0
        self.max_chunk_bytes_requested = 0

    def write_zero_flush(self, frames):
        if frames == 0:
            return
        zero_retries = 0
        remaining = frames
        while remaining > 0:
            chunk_frames = min(remaining, self.CHUNK_FRAMES)
            bytes_to_write = chunk_frames * self.BYTES_PER_FRAME
            assert bytes_to_write <= self.BUF_BYTES, "Buffer overflow prevented"
            if bytes_to_write > self.max_chunk_bytes_requested:
                self.max_chunk_bytes_requested = bytes_to_write
            written, err = self.write_fn(bytes_to_write)
            self.bytes_written += written
            if written != bytes_to_write:
                self.partial_writes += 1
            if err != 0:
                self.i2s_errors += 1
                self.last_err = err
                break
            if written == 0:
                zero_retries += 1
                if zero_retries >= self.MAX_ZERO_RETRIES:
                    break
                continue
            zero_retries = 0
            frames_written = written // self.BYTES_PER_FRAME
            if frames_written == 0:
                break
            remaining = max(0, remaining - frames_written)


class TestFase134Logic(unittest.TestCase):
    def test_state_transitions_and_antiretrigger_guard(self):
        sm = RobotStateMachineModel()
        self.assertTrue(sm.on_wake_detected(5000))
        self.assertEqual(sm.state, "LISTENING")
        self.assertFalse(sm.idle_wake_active)

        sm.transition("THINKING", 6500)
        self.assertFalse(sm.on_wake_detected(6600))  # suspended in THINKING
        sm.transition("SPEAKING", 7200)
        self.assertFalse(sm.on_wake_detected(7500))  # suspended in SPEAKING

        sm.transition("IDLE", 9000)
        self.assertEqual(sm.state, "IDLE")
        # First 20 DMA frames (200 ms) discarded even if time jumps
        for _ in range(20):
            self.assertFalse(sm.process_idle_frame(11000, 0.99, True))
        # Guard active until 10500 ms (1500 ms); elevated score extends guard
        self.assertFalse(sm.process_idle_frame(10400, 0.45, True))
        self.assertEqual(sm.guard_until_ms, 10550)
        self.assertFalse(sm.process_idle_frame(10500, 0.10, True))
        self.assertTrue(sm.process_idle_frame(10550, 0.99, True))  # allowed after extended guard

    def test_vad_end_of_speech_and_no_speech_timeout(self):
        vad = VoiceActivityDetectorModel(initial_rms=150)
        for _ in range(20):
            vad.update_ambient_rms(200)
        self.assertGreaterEqual(vad.speech_threshold(), 360)

        # Case 1: wake-word tail/echo in first 300 ms does NOT arm speech_started_
        vad.start_session(1000)
        for t in (1016, 1032, 1048, 1200, 1280):
            self.assertEqual(vad.process_chunk(1200, t), "CONTINUE")
        self.assertFalse(vad.speech_started)
        self.assertEqual(vad.process_chunk(180, 3499), "CONTINUE")
        self.assertEqual(vad.process_chunk(180, 3500), "STOP_NO_SPEECH")
        self.assertFalse(vad.speech_started)

        # Case 2: user speaks right after 300 ms holdoff -> arms in 4 chunks (64 ms), stops after 1100 ms silence
        vad.start_session(5000)
        for t in (5316, 5332, 5348, 5364):
            self.assertEqual(vad.process_chunk(900, t), "CONTINUE")
        self.assertTrue(vad.speech_started)
        self.assertEqual(vad.process_chunk(150, 6460), "CONTINUE")
        self.assertEqual(vad.process_chunk(150, 6464), "STOP_END_OF_SPEECH")

    def test_gpio47_and_error_recovery(self):
        sm = RobotStateMachineModel()
        # Manual GPIO47 press in IDLE
        sm.transition("LISTENING", 1000)
        self.assertFalse(sm.recording_from_wake)
        # Error -> recovery to IDLE with 20 DMA discards + 1500 ms guard
        sm.transition("ERROR", 2000)
        sm.transition("IDLE", 4000)
        self.assertEqual(sm.state, "IDLE")
        for _ in range(20):
            self.assertFalse(sm.on_wake_detected(6000))
        self.assertFalse(sm.on_wake_detected(5400))
        self.assertTrue(sm.on_wake_detected(5500))

    def test_preroll_chunked_drain_preserves_order(self):
        ring = PreRollRingModel()
        data = list(range(1, 10001))  # > 8000 capacity
        ring.push(data)
        self.assertEqual(ring.count, 8000)
        drained = []
        while True:
            c = ring.drain_chunk(256)
            if not c:
                break
            drained.extend(c)
        self.assertEqual(drained, list(range(2001, 10001)))
        self.assertEqual(ring.count, 0)

    def test_write_zero_flush_sizes_and_bounds(self):
        for frames in (0, 1, 256, 257, 960, 1024):
            calls = []

            def fake_write(n_bytes):
                calls.append(n_bytes)
                return n_bytes, 0

            m = WriteZeroFlushModel(fake_write)
            m.write_zero_flush(frames)
            self.assertEqual(m.bytes_written, frames * 4)
            self.assertLessEqual(m.max_chunk_bytes_requested, 1024)
            self.assertEqual(m.i2s_errors, 0)
            self.assertEqual(m.partial_writes, 0)
            for c in calls:
                self.assertLessEqual(c, 1024)

    def test_write_zero_flush_partial_timeout_and_error(self):
        # Partial write: 512 B then remaining 512 B for 256 frames
        seq = [(512, 0), (512, 0)]
        m_partial = WriteZeroFlushModel(lambda _: seq.pop(0))
        m_partial.write_zero_flush(256)
        self.assertEqual(m_partial.bytes_written, 1024)
        self.assertEqual(m_partial.partial_writes, 1)
        self.assertEqual(m_partial.i2s_errors, 0)

        # Timeout (0 bytes): stops cleanly after MAX_ZERO_RETRIES=3 without infinite loop
        calls = [0]

        def fake_timeout(_):
            calls[0] += 1
            return 0, 0

        m_to = WriteZeroFlushModel(fake_timeout)
        m_to.write_zero_flush(960)
        self.assertEqual(calls[0], 3)
        self.assertEqual(m_to.partial_writes, 3)

        # Error: stops immediately
        m_err = WriteZeroFlushModel(lambda _: (0, -1))
        m_err.write_zero_flush(960)
        self.assertEqual(m_err.i2s_errors, 1)
        self.assertEqual(m_err.last_err, -1)


if __name__ == "__main__":
    unittest.main(verbosity=2)

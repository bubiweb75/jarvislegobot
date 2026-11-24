(() => {
  "use strict";

  const MAX_REC_MS = 5000;
  const TARGET_SR = 16000;

  let uiState = "IDLE";
  let authenticated = false;
  let csrfToken = "";
  let mediaStream = null;
  let audioCtx = null;
  let scriptNode = null;
  let analyser = null;
  let recordedChunks = [];
  let recStartMs = 0;
  let recTimerId = null;
  let meterRafId = null;
  let activeAbortCtrl = null;
  let currentAudioUrl = null;
  let currentOriginalAudioUrl = null;
  let lastResampled16k = null;
  let gainCompareUrls = [];
  let gainCompareInFlight = false;

  const $ = (id) => document.getElementById(id);
  const el = {
    orb: $("orb-indicator"),
    backendBadge: $("backend-badge"),
    providerBadge: $("provider-badge"),
    stateBadge: $("state-badge"),
    tokenInput: $("token-input"),
    btnLogin: $("btn-login"),
    btnLogout: $("btn-logout"),
    authStatus: $("auth-status"),
    recPill: $("rec-pill"),
    btnStart: $("btn-start"),
    btnStop: $("btn-stop"),
    btnCancel: $("btn-cancel"),
    recTimer: $("rec-timer"),
    levelPct: $("level-pct"),
    levelBar: $("level-bar"),
    micHint: $("mic-hint"),
    optEcho: $("opt-echo"),
    optNoise: $("opt-noise"),
    optAgc: $("opt-agc"),
    gainSelect: $("gain-select"),
    originalAudioPlayer: $("original-audio-player"),
    transcriptBox: $("transcript-box"),
    replyBox: $("reply-box"),
    ttsStatusBadge: $("tts-status-badge"),
    audioPlayer: $("audio-player"),
    btnReplay: $("btn-replay"),
    btnStopAudio: $("btn-stop-audio"),
    diagReqId: $("diag-req-id"),
    diagProvider: $("diag-provider"),
    diagDur: $("diag-dur"),
    diagFmtIn: $("diag-fmt-in"),
    diagRmsPeak: $("diag-rms-peak"),
    diagClipping: $("diag-clipping"),
    diagGain: $("diag-gain"),
    diagWavSize: $("diag-wav-size"),
    diagFmtOut: $("diag-fmt-out"),
    diagSttMs: $("diag-stt-ms"),
    diagAiMs: $("diag-ai-ms"),
    diagTtsMs: $("diag-tts-ms"),
    diagTotalMs: $("diag-total-ms"),
    diagTz: $("diag-tz"),
    diagError: $("diag-error"),
    btnCompareStt: $("btn-compare-stt"),
    btnCompareGain: $("btn-compare-gain"),
    btnCompareModels: $("btn-compare-models"),
    sttRefInput: $("stt-ref-input"),
    sttCompareBox: $("stt-compare-box"),
    gainCompareBox: $("gain-compare-box"),
    modelCompareBox: $("model-compare-box"),
  };

  function setState(next) {
    uiState = next;
    el.stateBadge.textContent = next;
    el.orb.className = "orb";
    if (next === "RECORDING") el.orb.classList.add("recording");
    else if (next === "UPLOADING" || next === "PROCESSING") el.orb.classList.add("processing");
    else if (next === "PLAYING") el.orb.classList.add("playing");

    const busy = next === "RECORDING" || next === "UPLOADING" || next === "PROCESSING";
    el.btnStart.disabled = !authenticated || busy;
    el.btnStop.disabled = next !== "RECORDING";
    el.btnCancel.disabled = !(next === "UPLOADING" || next === "PROCESSING");
    el.recPill.hidden = next !== "RECORDING";
  }

  function releaseMediaResources() {
    if (recTimerId) {
      clearInterval(recTimerId);
      recTimerId = null;
    }
    if (meterRafId) {
      cancelAnimationFrame(meterRafId);
      meterRafId = null;
    }
    if (scriptNode) {
      try { scriptNode.disconnect(); } catch (_) {}
      scriptNode.onaudioprocess = null;
      scriptNode = null;
    }
    if (analyser) {
      try { analyser.disconnect(); } catch (_) {}
      analyser = null;
    }
    if (mediaStream) {
      mediaStream.getTracks().forEach((t) => t.stop());
      mediaStream = null;
    }
    if (audioCtx) {
      audioCtx.close().catch(() => {});
      audioCtx = null;
    }
    el.levelBar.style.width = "0%";
    el.levelPct.textContent = "0%";
  }

  async function resampleAntiAliased(floatSamples, srcRate, dstRate) {
    if (srcRate === dstRate || floatSamples.length < 2) {
      return floatSamples;
    }
    const targetLen = Math.max(1, Math.round(floatSamples.length * (dstRate / srcRate)));
    const OfflineCtx = window.OfflineAudioContext || window.webkitOfflineAudioContext;
    if (OfflineCtx) {
      const offline = new OfflineCtx(1, targetLen, dstRate);
      const buffer = offline.createBuffer(1, floatSamples.length, srcRate);
      buffer.copyToChannel(floatSamples, 0);
      const src = offline.createBufferSource();
      src.buffer = buffer;
      src.connect(offline.destination);
      src.start(0);
      const rendered = await offline.startRendering();
      return rendered.getChannelData(0);
    }
    // Fallback if OfflineAudioContext is unavailable in a legacy browser
    const ratio = srcRate / dstRate;
    const out = new Float32Array(targetLen);
    const maxIdx = floatSamples.length - 1;
    for (let i = 0; i < targetLen; i++) {
      const pos = i * ratio;
      const idx = Math.floor(pos);
      if (idx >= maxIdx) {
        out[i] = floatSamples[maxIdx];
      } else {
        const frac = pos - idx;
        out[i] = floatSamples[idx] * (1 - frac) + floatSamples[idx + 1] * frac;
      }
    }
    return out;
  }

  function clearGainCompare() {
    for (const u of gainCompareUrls) {
      URL.revokeObjectURL(u);
    }
    gainCompareUrls = [];
    if (el.gainCompareBox) {
      el.gainCompareBox.innerHTML = "";
      el.gainCompareBox.style.display = "none";
    }
  }

  function applySafeGain(floatSamples, requestedGain, safetyHeadroom = 0.95) {
    let peakIn = 0;
    for (let i = 0; i < floatSamples.length; i++) {
      const a = Math.abs(floatSamples[i]);
      if (a > peakIn) peakIn = a;
    }
    const effectiveGain = peakIn > 0 ? Math.min(requestedGain, safetyHeadroom / peakIn) : requestedGain;
    const out = new Float32Array(floatSamples.length);
    let sumSq = 0;
    let peak16 = 0;
    let clippedCount = 0;
    for (let i = 0; i < floatSamples.length; i++) {
      const s = floatSamples[i] * effectiveGain;
      out[i] = s;
      const clamped = Math.max(-1, Math.min(1, s));
      const i16 = clamped < 0 ? Math.round(clamped * 0x8000) : Math.round(clamped * 0x7fff);
      const abs16 = Math.abs(i16);
      if (abs16 > peak16) peak16 = abs16;
      if (abs16 >= 32767) clippedCount += 1;
      sumSq += i16 * i16;
    }
    const rms16 = floatSamples.length > 0 ? Math.round(Math.sqrt(sumSq / floatSamples.length)) : 0;
    return { samples: out, requestedGain, effectiveGain, rms16, peak16, clippedCount };
  }

  function encodeWavPcm16Mono(samples, sampleRate) {
    const numSamples = samples.length;
    const dataBytes = numSamples * 2;
    const buf = new ArrayBuffer(44 + dataBytes);
    const view = new DataView(buf);
    const writeStr = (offset, str) => {
      for (let i = 0; i < str.length; i++) view.setUint8(offset + i, str.charCodeAt(i));
    };

    writeStr(0, "RIFF");
    view.setUint32(4, 36 + dataBytes, true);
    writeStr(8, "WAVE");
    writeStr(12, "fmt ");
    view.setUint32(16, 16, true);
    view.setUint16(20, 1, true);
    view.setUint16(22, 1, true);
    view.setUint32(24, sampleRate, true);
    view.setUint32(28, sampleRate * 2, true);
    view.setUint16(32, 2, true);
    view.setUint16(34, 16, true);
    writeStr(36, "data");
    view.setUint32(40, dataBytes, true);

    let off = 44;
    for (let i = 0; i < numSamples; i++) {
      const clamped = Math.max(-1, Math.min(1, samples[i]));
      view.setInt16(off, clamped < 0 ? clamped * 0x8000 : clamped * 0x7fff, true);
      off += 2;
    }
    return new Blob([buf], { type: "audio/wav" });
  }

  async function refreshHealthAndReady() {
    try {
      const r = await fetch("/health");
      if (!r.ok) throw new Error("HTTP " + r.status);
      el.backendBadge.textContent = "Backend: connesso";
      el.backendBadge.className = "badge badge-ok";
    } catch (_) {
      el.backendBadge.textContent = "Backend: offline";
      el.backendBadge.className = "badge badge-err";
    }

    if (!authenticated) return;
    try {
      const r = await fetch("/ready", { credentials: "same-origin" });
      if (r.ok) {
        const d = await r.json();
        const p = d.providers || {};
        const aiText = (p.ollama && p.ollama.available) ? "Ollama" : ((p.cloud && p.cloud.available) ? "Cloud" : "Offline");
        el.providerBadge.textContent = `AI: ${aiText} | STT: ${p.stt && p.stt.available ? "OK" : "NO"} | TTS: ${p.tts && p.tts.available ? "OK" : "NO"}`;
      }
    } catch (_) {}
  }

  async function checkExistingSession() {
    try {
      const r = await fetch("/api/v1/auth/session", { credentials: "same-origin" });
      if (r.ok) {
        const d = await r.json();
        if (d.authenticated && !d.require_auth) {
          authenticated = true;
          el.authStatus.textContent = "Auth disabilitata in config";
          el.btnLogout.hidden = true;
          setState("IDLE");
          await refreshHealthAndReady();
        }
      }
    } catch (_) {}
  }

  el.btnLogin.addEventListener("click", async () => {
    const tok = el.tokenInput.value.trim();
    el.diagError.textContent = "Nessuno";
    try {
      const r = await fetch("/api/v1/auth/session", {
        method: "POST",
        credentials: "same-origin",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token: tok }),
      });
      if (!r.ok) {
        el.authStatus.textContent = "Token rifiutato (" + r.status + ")";
        authenticated = false;
        setState("ERROR");
        return;
      }
      const d = await r.json();
      csrfToken = d.csrf_token || "";
      authenticated = true;
      el.tokenInput.value = "";
      el.authStatus.textContent = "Sessione attiva (cookie HttpOnly)";
      el.btnLogout.hidden = false;
      el.micHint.textContent = "Pronto. Premi \"Avvia registrazione\" per registrare fino a 5 secondi.";
      setState("IDLE");
      await refreshHealthAndReady();
    } catch (err) {
      el.authStatus.textContent = "Errore rete";
      el.diagError.textContent = String(err);
    }
  });

  el.btnLogout.addEventListener("click", async () => {
    try {
      await fetch("/api/v1/auth/logout", {
        method: "POST",
        credentials: "same-origin",
        headers: { "X-CSRF-Token": csrfToken },
      });
    } catch (_) {}
    csrfToken = "";
    authenticated = false;
    if (currentOriginalAudioUrl) {
      URL.revokeObjectURL(currentOriginalAudioUrl);
      currentOriginalAudioUrl = null;
    }
    if (el.originalAudioPlayer) {
      el.originalAudioPlayer.removeAttribute("src");
      el.originalAudioPlayer.load();
    }
    lastResampled16k = null;
    clearGainCompare();
    if (el.btnCompareGain) el.btnCompareGain.disabled = true;
    if (el.btnCompareModels) el.btnCompareModels.disabled = true;
    if (el.modelCompareBox) {
      el.modelCompareBox.innerHTML = "";
      el.modelCompareBox.style.display = "none";
    }
    el.authStatus.textContent = "Sessione chiusa";
    el.btnLogout.hidden = true;
    setState("IDLE");
  });

  async function startRecording() {
    if (!authenticated || uiState === "RECORDING") return;
    el.diagError.textContent = "Nessuno";
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      el.diagError.textContent = "API microfono non disponibile nel browser.";
      setState("ERROR");
      return;
    }

    try {
      mediaStream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,
          echoCancellation: el.optEcho ? el.optEcho.checked : true,
          noiseSuppression: el.optNoise ? el.optNoise.checked : true,
          autoGainControl: el.optAgc ? el.optAgc.checked : true,
        },
      });
      const Ctx = window.AudioContext || window.webkitAudioContext;
      audioCtx = new Ctx();
      const source = audioCtx.createMediaStreamSource(mediaStream);
      analyser = audioCtx.createAnalyser();
      analyser.fftSize = 256;
      scriptNode = audioCtx.createScriptProcessor(2048, 1, 1);

      recordedChunks = [];
      scriptNode.onaudioprocess = (ev) => {
        if (uiState !== "RECORDING") return;
        const ch0 = ev.inputBuffer.getChannelData(0);
        recordedChunks.push(new Float32Array(ch0));
      };

      source.connect(analyser);
      analyser.connect(scriptNode);
      scriptNode.connect(audioCtx.destination);

      recStartMs = performance.now();
      setState("RECORDING");
      el.micHint.textContent = "Registrazione in corso... parla ora.";

      const freqData = new Uint8Array(analyser.frequencyBinCount);
      const tickMeter = () => {
        if (uiState !== "RECORDING" || !analyser) return;
        analyser.getByteTimeDomainData(freqData);
        let peak = 0;
        for (let i = 0; i < freqData.length; i++) {
          const v = Math.abs(freqData[i] - 128) / 128;
          if (v > peak) peak = v;
        }
        const pct = Math.min(100, Math.round(peak * 180));
        el.levelBar.style.width = pct + "%";
        el.levelPct.textContent = pct + "%";
        meterRafId = requestAnimationFrame(tickMeter);
      };
      meterRafId = requestAnimationFrame(tickMeter);

      recTimerId = setInterval(() => {
        const elapsed = performance.now() - recStartMs;
        el.recTimer.textContent = (Math.min(MAX_REC_MS, elapsed) / 1000).toFixed(1) + " s";
        if (elapsed >= MAX_REC_MS) {
          stopAndUpload();
        }
      }, 100);
    } catch (err) {
      releaseMediaResources();
      el.diagError.textContent = "Permesso microfono negato o dispositivo assente: " + err.message;
      setState("ERROR");
    }
  }

  async function stopAndUpload() {
    if (uiState !== "RECORDING") return;
    const elapsedMs = Math.max(0, performance.now() - recStartMs);
    const srcSr = audioCtx ? audioCtx.sampleRate : 48000;
    releaseMediaResources();

    const totalLen = recordedChunks.reduce((acc, c) => acc + c.length, 0);
    if (totalLen === 0) {
      el.diagError.textContent = "Nessun campione audio acquisito.";
      setState("ERROR");
      return;
    }

    const merged = new Float32Array(totalLen);
    let offset = 0;
    for (const c of recordedChunks) {
      merged.set(c, offset);
      offset += c.length;
    }
    recordedChunks = [];

    const resampled = await resampleAntiAliased(merged, srcSr, TARGET_SR);
    lastResampled16k = resampled;
    clearGainCompare();
    const requestedGain = parseFloat(el.gainSelect ? el.gainSelect.value : "1") || 1;
    const gained = applySafeGain(resampled, requestedGain, 0.95);
    const wavBlob = encodeWavPcm16Mono(gained.samples, TARGET_SR);

    if (currentOriginalAudioUrl) {
      URL.revokeObjectURL(currentOriginalAudioUrl);
      currentOriginalAudioUrl = null;
    }
    currentOriginalAudioUrl = URL.createObjectURL(wavBlob);
    if (el.originalAudioPlayer) {
      el.originalAudioPlayer.src = currentOriginalAudioUrl;
    }

    el.diagDur.textContent = (elapsedMs / 1000).toFixed(2) + " s";
    el.diagFmtIn.textContent = `${TARGET_SR} Hz (da ${srcSr} Hz)`;
    el.diagRmsPeak.textContent = `RMS ${gained.rms16} / Picco ${gained.peak16}`;
    el.diagClipping.textContent = `${gained.clippedCount} campioni`;
    if (el.diagGain) {
      el.diagGain.textContent = `${gained.requestedGain.toFixed(1)}× / ${gained.effectiveGain.toFixed(2)}×`;
    }
    el.diagWavSize.textContent = `${wavBlob.size} B`;
    el.btnCompareStt.disabled = true;
    if (el.btnCompareGain) el.btnCompareGain.disabled = false;
    if (el.btnCompareModels) el.btnCompareModels.disabled = false;
    el.sttCompareBox.style.display = "none";
    if (el.modelCompareBox) {
      el.modelCompareBox.innerHTML = "";
      el.modelCompareBox.style.display = "none";
    }

    const form = new FormData();
    form.append("file", wavBlob, "voice_lab.wav");

    activeAbortCtrl = new AbortController();
    setState("UPLOADING");
    el.ttsStatusBadge.textContent = "TTS: elaborazione...";
    el.micHint.textContent = "Invio WAV ed elaborazione STT → AI → TTS in corso...";

    try {
      setState("PROCESSING");
      const resp = await fetch("/api/v1/voice/process?include_base64=true", {
        method: "POST",
        credentials: "same-origin",
        headers: { "X-CSRF-Token": csrfToken },
        body: form,
        signal: activeAbortCtrl.signal,
      });

      const data = await resp.json();
      if (!resp.ok) {
        const errCode = (data.error && data.error.code) || ("HTTP_" + resp.status);
        const errMsg = (data.error && data.error.message) || "Errore pipeline";
        el.diagError.textContent = `${errCode}: ${errMsg}`;
        if (errCode === "SILENT_AUDIO" || errCode === "EMPTY_TRANSCRIPT") {
          el.transcriptBox.textContent = `[Nessun parlato rilevato: ${errCode}]`;
        }
        el.ttsStatusBadge.textContent = "TTS: errore";
        setState("ERROR");
        return;
      }

      el.transcriptBox.textContent = data.transcript || "—";
      el.replyBox.textContent = data.reply_text || "—";
      el.providerBadge.textContent = `Provider: ${data.provider_used}`;
      el.diagReqId.textContent = data.request_id || "—";
      el.diagProvider.textContent = data.provider_used || "—";
      if (typeof data.input_duration_s === "number" && data.input_duration_s > 0) {
        el.diagDur.textContent = `${data.input_duration_s.toFixed(2)} s`;
      }
      if (typeof data.input_sample_rate === "number" && data.input_sample_rate > 0) {
        el.diagFmtIn.textContent = `${data.input_sample_rate} Hz PCM16 mono`;
      }
      if (typeof data.input_rms_16 === "number") {
        el.diagRmsPeak.textContent = `RMS ${data.input_rms_16} / Picco ${data.input_peak_16 ?? 0}`;
      }
      if (typeof data.input_clipped_count === "number") {
        el.diagClipping.textContent = `${data.input_clipped_count} campioni`;
      }
      if (typeof data.input_wav_bytes_len === "number" && data.input_wav_bytes_len > 0) {
        el.diagWavSize.textContent = `${data.input_wav_bytes_len} B`;
      }
      el.diagTz.textContent = data.timezone_note || "—";
      el.btnCompareStt.disabled = false;
      el.diagFmtOut.textContent = `${data.audio_sample_rate} Hz · ${data.audio_channels}ch · ${data.audio_bits}bit (${data.audio_bytes_len} B)`;
      el.diagSttMs.textContent = `${data.timings.stt_ms} ms`;
      el.diagAiMs.textContent = `${data.timings.ai_ms} ms`;
      el.diagTtsMs.textContent = `${data.timings.tts_ms} ms`;
      el.diagTotalMs.textContent = `${data.timings.total_ms} ms`;
      el.ttsStatusBadge.textContent = "TTS: pronto";

      if (data.audio_wav_base64) {
        const bin = atob(data.audio_wav_base64);
        const bytes = new Uint8Array(bin.length);
        for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
        const outBlob = new Blob([bytes], { type: "audio/wav" });
        if (currentAudioUrl) URL.revokeObjectURL(currentAudioUrl);
        currentAudioUrl = URL.createObjectURL(outBlob);
        el.audioPlayer.src = currentAudioUrl;
        el.btnReplay.disabled = false;
        el.btnStopAudio.disabled = false;
        setState("READY");
        el.audioPlayer.play().catch(() => {});
      } else {
        setState("READY");
      }
      el.micHint.textContent = "Completato. Puoi registrare un'altra domanda o riascoltare.";
    } catch (err) {
      if (err.name === "AbortError") {
        el.diagError.textContent = "Richiesta annullata dal browser (AbortController).";
        el.ttsStatusBadge.textContent = "TTS: annullato";
        setState("IDLE");
      } else {
        el.diagError.textContent = "Errore rete/elaborazione: " + err.message;
        el.ttsStatusBadge.textContent = "TTS: errore";
        setState("ERROR");
      }
    } finally {
      activeAbortCtrl = null;
    }
  }

  el.btnStart.addEventListener("click", startRecording);
  el.btnStop.addEventListener("click", stopAndUpload);
  el.btnCancel.addEventListener("click", () => {
    if (activeAbortCtrl) activeAbortCtrl.abort();
  });
  el.btnCompareStt.addEventListener("click", async () => {
    el.btnCompareStt.disabled = true;
    el.sttCompareBox.style.display = "block";
    el.sttCompareBox.textContent = "Esecuzione confronto STT (A–E) in corso...";
    try {
      const resp = await fetch("/api/v1/stt/compare", {
        method: "POST",
        credentials: "same-origin",
        headers: { "X-CSRF-Token": csrfToken },
      });
      const data = await resp.json();
      if (!resp.ok) {
        const errMsg = (data.error && data.error.message) || ("HTTP " + resp.status);
        el.sttCompareBox.textContent = "Confronto non disponibile: " + errMsg;
        return;
      }
      const lines = (data.comparisons || []).map((c) => {
        const res = c.error ? `[ERRORE: ${c.error}]` : `"${c.transcript}"`;
        return `${c.id} (${c.latency_ms} ms) — ${c.label}: ${res}`;
      });
      el.sttCompareBox.textContent = lines.join("\n") || "Nessun risultato.";
    } catch (err) {
      el.sttCompareBox.textContent = "Errore confronto STT: " + err.message;
    } finally {
      el.btnCompareStt.disabled = false;
    }
  });
  el.btnCompareGain.addEventListener("click", async () => {
    if (gainCompareInFlight || !lastResampled16k) return;
    gainCompareInFlight = true;
    el.btnCompareGain.disabled = true;
    el.btnStart.disabled = true;
    clearGainCompare();
    el.gainCompareBox.style.display = "block";
    const statusLine = document.createElement("p");
    statusLine.textContent = "Confronto guadagni (1× / 2× / 3×) in corso in sequenza...";
    el.gainCompareBox.appendChild(statusLine);

    try {
      for (const reqGain of [1, 2, 3]) {
        const gained = applySafeGain(lastResampled16k, reqGain, 0.95);
        const wavBlob = encodeWavPcm16Mono(gained.samples, TARGET_SR);
        const objUrl = URL.createObjectURL(wavBlob);
        gainCompareUrls.push(objUrl);

        const row = document.createElement("div");
        row.style.border = "1px solid rgba(255,255,255,0.12)";
        row.style.borderRadius = "8px";
        row.style.padding = "8px";
        row.style.marginTop = "8px";

        const meta = document.createElement("div");
        meta.textContent =
          `Guadagno ${gained.requestedGain.toFixed(0)}× (effettivo ${gained.effectiveGain.toFixed(2)}×) · ` +
          `RMS ${gained.rms16} · Picco ${gained.peak16} · Clipping ${gained.clippedCount}`;
        row.appendChild(meta);

        const player = document.createElement("audio");
        player.controls = true;
        player.preload = "auto";
        player.src = objUrl;
        player.style.width = "100%";
        player.style.marginTop = "4px";
        row.appendChild(player);

        const sttLine = document.createElement("div");
        sttLine.style.marginTop = "4px";
        sttLine.textContent = "Trascrizione Whisper: in elaborazione...";
        row.appendChild(sttLine);
        el.gainCompareBox.appendChild(row);

        const form = new FormData();
        form.append("file", wavBlob, `voice_lab_${reqGain}x.wav`);
        try {
          const resp = await fetch("/api/v1/stt", {
            method: "POST",
            credentials: "same-origin",
            headers: { "X-CSRF-Token": csrfToken },
            body: form,
          });
          const data = await resp.json();
          if (!resp.ok) {
            const errCode = (data.error && data.error.code) || ("HTTP_" + resp.status);
            const errMsg = (data.error && data.error.message) || "Errore STT";
            sttLine.textContent = `Trascrizione Whisper: [${errCode}] ${errMsg}`;
          } else {
            sttLine.textContent = `Trascrizione Whisper (${data.stt_ms} ms): "${data.transcript}"`;
          }
        } catch (err) {
          sttLine.textContent = `Errore richiesta STT: ${err.message}`;
        }
      }
      statusLine.textContent = "Confronto guadagni completato (nota: il guadagno amplifica anche il rumore di fondo).";
    } finally {
      gainCompareInFlight = false;
      el.btnCompareGain.disabled = !lastResampled16k;
      el.btnStart.disabled = !authenticated;
    }
  });
  el.btnCompareModels.addEventListener("click", async () => {
    if (!lastResampled16k) return;
    el.btnCompareModels.disabled = true;
    el.btnStart.disabled = true;
    el.modelCompareBox.innerHTML = "";
    el.modelCompareBox.style.display = "block";
    const statusP = document.createElement("p");
    statusP.textContent = "Confronto sequenziale Whisper Base vs Small in corso sullo stesso WAV originale...";
    el.modelCompareBox.appendChild(statusP);

    try {
      const origBlob = encodeWavPcm16Mono(lastResampled16k, TARGET_SR);
      const form = new FormData();
      form.append("file", origBlob, "voice_lab_orig.wav");
      form.append("models", "base,small");
      form.append("reference_text", el.sttRefInput ? el.sttRefInput.value : "");

      const resp = await fetch("/api/v1/stt/compare-models", {
        method: "POST",
        credentials: "same-origin",
        headers: { "X-CSRF-Token": csrfToken },
        body: form,
      });
      const data = await resp.json();
      if (!resp.ok) {
        const errCode = (data.error && data.error.code) || ("HTTP_" + resp.status);
        const errMsg = (data.error && data.error.message) || "Errore confronto modelli";
        statusP.textContent = `Confronto non riuscito [${errCode}]: ${errMsg}`;
        return;
      }

      const dur = data.audio_metrics ? data.audio_metrics.input_duration_s : "—";
      statusP.textContent = `Confronto completato (modello predefinito pipeline: ${data.default_model}, durata WAV: ${dur} s):`;
      for (const c of data.comparisons || []) {
        const card = document.createElement("div");
        card.style.border = "1px solid rgba(255,255,255,0.12)";
        card.style.borderRadius = "8px";
        card.style.padding = "8px";
        card.style.marginTop = "8px";

        const title = document.createElement("div");
        const werText = typeof c.wer === "number" ? ` · WER ${(c.wer * 100).toFixed(1)}%` : "";
        const rssText = typeof c.rss_mb === "number" ? ` · RAM ${c.rss_mb} MB (Δ ${c.rss_delta_mb ?? 0} MB)` : "";
        title.textContent = `Modello: ${c.model} · Caricamento ${c.load_ms} ms · Inferenza ${c.inference_ms} ms${werText}${rssText}`;
        card.appendChild(title);

        const tr = document.createElement("div");
        tr.style.marginTop = "4px";
        tr.textContent = c.error ? `Errore: ${c.error}` : `Trascrizione: "${c.transcript}"`;
        card.appendChild(tr);

        const p = document.createElement("div");
        p.style.marginTop = "2px";
        p.style.opacity = "0.8";
        const o = c.options || {};
        p.textContent = `Parametri: lang=${o.language || "it"}, beam=${o.beam_size}, vad=${o.vad_filter}, pad=${o.speech_pad_ms}ms, prompt="${o.initial_prompt || ""}"`;
        card.appendChild(p);

        el.modelCompareBox.appendChild(card);
      }
    } catch (err) {
      statusP.textContent = `Errore richiesta confronto modelli: ${err.message}`;
    } finally {
      el.btnCompareModels.disabled = !lastResampled16k;
      el.btnStart.disabled = !authenticated;
    }
  });
  el.btnReplay.addEventListener("click", () => {
    if (el.audioPlayer.src) {
      el.audioPlayer.currentTime = 0;
      el.audioPlayer.play().catch(() => {});
    }
  });
  el.btnStopAudio.addEventListener("click", () => {
    el.audioPlayer.pause();
    el.audioPlayer.currentTime = 0;
    setState("READY");
  });
  el.audioPlayer.addEventListener("play", () => setState("PLAYING"));
  el.audioPlayer.addEventListener("ended", () => setState("READY"));

  setState("IDLE");
  refreshHealthAndReady();
  checkExistingSession();
})();

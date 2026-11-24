# Specifica del Protocollo WebSocket Duplex v1.0

> **JARVIS Robotics Platform** — Contratto di Protocollo Real-Time Client/Server  
> **Fase:** RP-02  
> **Stato:** Approvato per Progettazione  

---

## 1. Stato dell'Implementazione Esistente vs Estensioni

L'analisi del backend `05-Voice-AI/voice_bridge/esp_protocol.py` e del firmware client `04-Firmware/arduino-hw-test/jarvis_wifi_voice_client/` evidenzia la suddivisione rigorosa tra ciò che è già funzionante e ciò che viene formalizzato per la piattaforma:

### 1.1 Messaggi Già Implementati e Collaudati a Banco
- `auth` e `auth_ok`: Autenticazione client con token dispositivo e configurazione sessione.
- `ping` e `pong`: Heartbeat ciclico per verifica connettività.
- `audio_start` e `ack`: Apertura canale di cattura microfonica I2S.
- Frame binari upstream: Chunk PCM16 16 kHz mono da 2048 byte inviati dal client.
- `audio_end`: Notifica fine parlato che scatena la pipeline STT/LLM/TTS.
- `tts_start`, frame binari downstream e `tts_end`: Notifica e streaming della sintesi vocale Piper verso I2S1.
- `cancel` e `cancelled`: Interruzione rapida via pulsante PTT GPIO47.
- `error`: Notifiche di errore con codici standard.

### 1.2 Messaggi Formalizzati per la Piattaforma Multi-Robot (Estensione RP-02)
- Negoziazione Capability nell'handshake `auth` (`client_capabilities` e `server_capabilities`).
- `config_update` e `config_ack`: Invio e conferma di parametri NVS (es. etichetta robot, volume nominale).
- `skin_apply` e `skin_applied`: Distribuzione a caldo di profili grafici oculari con applicazione differita allo stato sicuro `IDLE`.
- `telemetry_report`: Frame periodico con telemetria estesa (heap, RSSI, tensione batteria, FPS effettivi).

---

## 2. Definizione dei Frame di Controllo JSON

Ogni frame JSON adotta una struttura unificata:
```json
{
  "type": "STRING_EVENT_NAME",
  "request_id": "req-1732470000-001",
  "correlation_id": "corr-session-987",
  "timestamp": "2026-11-24T18:00:00Z",
  "payload": {}
}
```

### 2.1 Handshake e Autenticazione
```json
// Client -> Server: auth
{
  "type": "auth",
  "request_id": "req-auth-001",
  "payload": {
    "device_id": "rob-esp32s3-288485870588",
    "token": "HMAC_TOKEN_SECRET",
    "firmware_version": "1.0.0",
    "hardware_profile": "profile-desktop-v1",
    "client_capabilities": ["DISPLAY_MONO_128X64", "AUDIO_INPUT_I2S", "AUDIO_OUTPUT_I2S", "PTT", "LOCAL_WAKEWORD"]
  }
}

// Server -> Client: auth_ok
{
  "type": "auth_ok",
  "correlation_id": "req-auth-001",
  "payload": {
    "session_id": "sess-84920491",
    "chunk_bytes": 2048,
    "max_audio_bytes": 256000,
    "max_tts_bytes": 640000,
    "active_identity_id": "identity-jarvis-original-v3",
    "server_capabilities": ["FASTER_WHISPER", "PIPER_TTS", "LOCAL_INTENTS"]
  }
}
```

### 2.2 Streaming Audio Turno Vocale
```json
// Client -> Server: audio_start
{
  "type": "audio_start",
  "request_id": "req-turn-102",
  "payload": {
    "sample_rate": 16000,
    "channels": 1,
    "bit_depth": 16,
    "trigger_source": "WAKEWORD_LOCAL"
  }
}

// Client -> Server: frame binari (ripetuti, 2048 byte PCM16)

// Client -> Server: audio_end
{
  "type": "audio_end",
  "request_id": "req-turn-102",
  "payload": {
    "total_samples": 48000,
    "duration_ms": 3000
  }
}

// Server -> Client: tts_start
{
  "type": "tts_start",
  "request_id": "req-turn-102",
  "payload": {
    "sample_rate": 16000,
    "channels": 1,
    "total_bytes": 64000,
    "provider": "piper",
    "voice_id": "it_IT-riccardo-x_low",
    "transcript": "Buongiorno! Come posso esserti utile?"
  }
}

// Server -> Client: frame binari (ripetuti, 2048 byte PCM16)

// Server -> Client: tts_end
{
  "type": "tts_end",
  "request_id": "req-turn-102",
  "payload": {
    "total_bytes_sent": 64000,
    "timings": {
      "stt_ms": 220,
      "ai_ms": 610,
      "tts_ms": 175,
      "total_e2e_ms": 1005
    }
  }
}
```

### 2.3 Applicazione a Caldo della Skin e Transazione Sicura
```json
// Server -> Client: skin_apply
{
  "type": "skin_apply",
  "request_id": "req-skin-404",
  "payload": {
    "skin_id": "skin-eva-elegant-v1",
    "config_revision": 4,
    "safe_apply_deferred": true,
    "parameters": {
      "width": 36.0,
      "height": 36.0,
      "shape_power": 2.2,
      "taper": 0.08,
      "corner_radius": 14.0,
      "spacing_px": 16
    }
  }
}

// Client -> Server: skin_applied
{
  "type": "skin_applied",
  "correlation_id": "req-skin-404",
  "payload": {
    "skin_id": "skin-eva-elegant-v1",
    "applied_revision": 4,
    "status": "APPLIED_IMMEDIATELY",
    "render_us": 2420
  }
}
```

---

## 3. Garanzie di Resilienza e Idempotenza

1. **Idempotenza delle Richieste:**  
   Ogni richiesta di cambio configurazione include un `request_id` univoco e un numero sequenziale di revisione (`config_revision`). Se il client riceve un messaggio duplicato con revisione uguale o inferiore a quella attiva, risponde immediatamente con `skin_applied` senza rieseguire il caricamento o causare sfarfallii.
2. **Heartbeat e Timeout di Connessione:**  
   Se il client non riceve risposta a 3 messaggi di `ping` consecutivi (intervallo 15 s, timeout 45 s), chiude il socket TCP e avvia la procedura di riconnessione esponenziale, continuando a visualizzare le animazioni locali in sicurezza.

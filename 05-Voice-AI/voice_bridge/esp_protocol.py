"""ESP32-S3 WebSocket Protocol Adapter v1.0 for JARVIS Voice Bridge."""

from __future__ import annotations

import array
import asyncio
from dataclasses import asdict
import hmac
import io
import json
import logging
import secrets
from typing import Any, Dict, Optional
import wave

from fastapi import WebSocket, WebSocketDisconnect

from .audio import encode_wav_mono_16bit
from .pipeline import CancellationToken, VoiceBridgeService
from .schemas import BridgeError

PROTOCOL_VERSION = "1.0"
MAX_BINARY_FRAME_BYTES = 8192


def _extract_pcm16_frames(wav_bytes: bytes) -> tuple[int, int, int, bytes]:
    with wave.open(io.BytesIO(wav_bytes), "rb") as wf:
        sr = wf.getframerate()
        ch = wf.getnchannels()
        bits = wf.getsampwidth() * 8
        frames = wf.readframes(wf.getnframes())
    return sr, ch, bits, frames


class Esp32WebSocketAdapter:
    """Handles one authenticated ESP32-S3 WebSocket session reusing VoiceBridgeService."""

    def __init__(self, service: VoiceBridgeService) -> None:
        self.service = service
        self.cfg = service.config

    def _verify_device_token(self, token: str) -> bool:
        if not self.cfg.require_auth:
            return True
        expected = self.cfg.esp_device_token
        if not expected or not token:
            return False
        return hmac.compare_digest(token.encode("utf-8"), expected.encode("utf-8"))

    @staticmethod
    async def _send_json(ws: WebSocket, payload: Dict[str, Any]) -> None:
        msg = {"v": PROTOCOL_VERSION, **payload}
        await ws.send_text(json.dumps(msg, ensure_ascii=False))

    async def _send_error(
        self,
        ws: WebSocket,
        code: str,
        message: str,
        request_id: str = "",
    ) -> None:
        payload: Dict[str, Any] = {"type": "error", "code": code, "message": message}
        if request_id:
            payload["request_id"] = request_id
        await self._send_json(ws, payload)

    async def handle(self, ws: WebSocket) -> None:
        await ws.accept()
        session_id = f"esp_{secrets.token_hex(6)}"
        authenticated = False

        # Check optional Bearer header on handshake
        auth_header = ws.headers.get("authorization", "")
        if auth_header.lower().startswith("bearer "):
            hdr_token = auth_header[7:].strip()
            if self._verify_device_token(hdr_token):
                authenticated = True
                await self._send_json(
                    ws,
                    {
                        "type": "auth_ok",
                        "session_id": session_id,
                        "max_audio_bytes": self.cfg.esp_max_input_bytes,
                        "max_tts_bytes": self.cfg.esp_max_tts_bytes,
                        "chunk_bytes": self.cfg.esp_ws_chunk_bytes,
                    },
                )
            else:
                await self._send_error(ws, "UNAUTHORIZED", "Token dispositivo non valido")
                await ws.close(code=4001)
                return
        elif not self.cfg.require_auth:
            authenticated = True
            await self._send_json(
                ws,
                {
                    "type": "auth_ok",
                    "session_id": session_id,
                    "max_audio_bytes": self.cfg.esp_max_input_bytes,
                    "max_tts_bytes": self.cfg.esp_max_tts_bytes,
                    "chunk_bytes": self.cfg.esp_ws_chunk_bytes,
                },
            )

        active_req_id: Optional[str] = None
        upload_buf = bytearray()
        cancel_token: Optional[CancellationToken] = None
        seen_req_ids: set[str] = set()

        try:
            while True:
                try:
                    raw = await asyncio.wait_for(ws.receive(), timeout=self.cfg.esp_ws_idle_timeout_s)
                except asyncio.TimeoutError:
                    await self._send_error(ws, "SESSION_TIMEOUT", "Timeout inattivita sessione WebSocket")
                    await ws.close(code=4008)
                    return

                if raw.get("type") == "websocket.disconnect":
                    break

                if "bytes" in raw and raw["bytes"] is not None:
                    chunk = raw["bytes"]
                    if not authenticated:
                        await self._send_error(ws, "UNAUTHORIZED", "Autenticazione richiesta prima dei dati binari")
                        await ws.close(code=4001)
                        return
                    if active_req_id is None:
                        await self._send_error(ws, "UNEXPECTED_BINARY", "Frame binario ricevuto senza audio_start attivo")
                        continue
                    if len(chunk) > MAX_BINARY_FRAME_BYTES:
                        req = active_req_id
                        active_req_id = None
                        upload_buf.clear()
                        await self._send_error(ws, "FRAME_TOO_LARGE", "Frame binario troppo grande", request_id=req)
                        continue
                    if len(upload_buf) + len(chunk) > self.cfg.esp_max_input_bytes:
                        req = active_req_id
                        active_req_id = None
                        upload_buf.clear()
                        await self._send_error(
                            ws,
                            "PAYLOAD_TOO_LARGE",
                            f"Audio superiore al limite ({self.cfg.esp_max_input_bytes} B)",
                            request_id=req,
                        )
                        continue
                    upload_buf.extend(chunk)
                    continue

                text_data = raw.get("text")
                if text_data is None:
                    continue

                try:
                    msg = json.loads(text_data)
                    if not isinstance(msg, dict):
                        raise ValueError("JSON root must be an object")
                except Exception:
                    await self._send_error(ws, "MALFORMED_JSON", "Messaggio JSON non valido")
                    continue

                msg_type = str(msg.get("type", "")).strip()
                req_id = str(msg.get("request_id", "")).strip()

                if not authenticated:
                    if msg_type != "auth":
                        await self._send_error(ws, "UNAUTHORIZED", "Atteso messaggio auth iniziale")
                        await ws.close(code=4001)
                        return
                    tok = str(msg.get("token", "")).strip()
                    if not self._verify_device_token(tok):
                        self.service.diagnostics.log_event(logging.WARNING, session_id, "ESP32 auth failed")
                        await self._send_error(ws, "UNAUTHORIZED", "Autenticazione dispositivo fallita")
                        await ws.close(code=4001)
                        return
                    authenticated = True
                    await self._send_json(
                        ws,
                        {
                            "type": "auth_ok",
                            "session_id": session_id,
                            "max_audio_bytes": self.cfg.esp_max_input_bytes,
                            "max_tts_bytes": self.cfg.esp_max_tts_bytes,
                            "chunk_bytes": self.cfg.esp_ws_chunk_bytes,
                        },
                    )
                    continue

                if msg_type == "ping":
                    await self._send_json(ws, {"type": "pong", "ts": msg.get("ts", 0)})
                    continue

                if msg_type == "cancel":
                    if cancel_token is not None:
                        cancel_token.cancel()
                    cancelled_id = req_id or active_req_id or ""
                    active_req_id = None
                    upload_buf.clear()
                    await self._send_json(ws, {"type": "cancelled", "request_id": cancelled_id})
                    continue

                if msg_type == "audio_start":
                    if not req_id:
                        await self._send_error(ws, "MISSING_REQUEST_ID", "request_id obbligatorio")
                        continue
                    if active_req_id is not None or req_id in seen_req_ids:
                        await self._send_error(
                            ws,
                            "DUPLICATE_REQUEST",
                            "Richiesta gia attiva o request_id duplicato",
                            request_id=req_id,
                        )
                        continue
                    sr = int(msg.get("sr", 0) or 0)
                    ch = int(msg.get("ch", 0) or 0)
                    bits = int(msg.get("bits", 0) or 0)
                    if sr != 16000 or ch != 1 or bits != 16:
                        await self._send_error(
                            ws,
                            "UNSUPPORTED_AUDIO_FORMAT",
                            "Richiesto PCM16 mono 16000 Hz",
                            request_id=req_id,
                        )
                        continue
                    seen_req_ids.add(req_id)
                    active_req_id = req_id
                    upload_buf.clear()
                    cancel_token = CancellationToken()
                    await self._send_json(ws, {"type": "ack", "request_id": req_id, "stage": "audio_start"})
                    continue

                if msg_type == "audio_end":
                    if active_req_id is None or req_id != active_req_id:
                        await self._send_error(
                            ws,
                            "NO_ACTIVE_UPLOAD",
                            "audio_end non corrisponde ad alcuna registrazione attiva",
                            request_id=req_id,
                        )
                        continue
                    pcm_bytes = bytes(upload_buf)
                    active_req_id = None
                    upload_buf.clear()
                    if len(pcm_bytes) < 2 or len(pcm_bytes) % 2 != 0:
                        await self._send_error(
                            ws,
                            "INVALID_AUDIO_PAYLOAD",
                            "Payload PCM16 incompleto o vuoto",
                            request_id=req_id,
                        )
                        continue

                    samples = array.array("h")
                    samples.frombytes(pcm_bytes)
                    self.service.diagnostics.log_event(
                        logging.INFO,
                        req_id,
                        f"ESP_AUDIO_RX pcm_bytes={len(pcm_bytes)} dur_s={len(pcm_bytes) / 32000.0:.2f} "
                        f"max_bytes={self.cfg.esp_max_input_bytes} "
                        f"limit_reached={len(pcm_bytes) >= self.cfg.esp_max_input_bytes}",
                    )
                    wav_in = encode_wav_mono_16bit(list(samples), 16000)

                    try:
                        res = await asyncio.to_thread(
                            self.service.process_voice,
                            wav_in,
                            False,
                            cancel_token,
                        )
                        out_wav = self.service.temp_store.get(res.audio_id, consume=True)
                        out_sr, out_ch, out_bits, out_pcm = _extract_pcm16_frames(out_wav)
                        if len(out_pcm) > self.cfg.esp_max_tts_bytes:
                            self.service.diagnostics.log_event(
                                logging.WARNING,
                                req_id,
                                f"WSS TTS_TOO_LONG pcm_bytes={len(out_pcm)} max_bytes={self.cfg.esp_max_tts_bytes}",
                            )
                            await self._send_error(
                                ws,
                                "TTS_TOO_LONG",
                                f"Risposta TTS eccede il limite dispositivo ({len(out_pcm)} B > {self.cfg.esp_max_tts_bytes} B)",
                                request_id=req_id,
                            )
                            continue

                        await self._send_json(
                            ws,
                            {
                                "type": "tts_start",
                                "request_id": req_id,
                                "sr": out_sr,
                                "ch": out_ch,
                                "bits": out_bits,
                                "total_bytes": len(out_pcm),
                                "provider_used": res.provider_used,
                                "transcript": res.transcript,
                            },
                        )
                        step = self.cfg.esp_ws_chunk_bytes
                        for off in range(0, len(out_pcm), step):
                            await ws.send_bytes(out_pcm[off : off + step])
                        await self._send_json(
                            ws,
                            {
                                "type": "tts_end",
                                "request_id": req_id,
                                "total_bytes": len(out_pcm),
                                "timings": asdict(res.timings),
                            },
                        )
                        self.service.diagnostics.log_event(
                            logging.INFO,
                            req_id,
                            f"WSS TTS_SENT pcm_bytes={len(out_pcm)} (invio completato, riproduzione lato dispositivo)",
                        )
                    except BridgeError as exc:
                        await self._send_error(ws, exc.code, exc.message, request_id=req_id)
                    continue

                await self._send_error(ws, "UNKNOWN_MESSAGE_TYPE", f"Tipo messaggio non supportato: '{msg_type}'")
        except WebSocketDisconnect:
            if cancel_token is not None:
                cancel_token.cancel()
            upload_buf.clear()
        finally:
            upload_buf.clear()

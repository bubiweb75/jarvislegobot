"""FastAPI HTTP Layer for JARVIS Voice Bridge + JARVIS Voice Lab UI."""

from __future__ import annotations

import hmac
import logging
from pathlib import Path
from typing import Optional

from fastapi import Cookie, Depends, FastAPI, File, Form, Header, Query, Request, Response, UploadFile, WebSocket
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .esp_protocol import Esp32WebSocketAdapter
from .pipeline import VoiceBridgeService
from .schemas import BridgeError
from .security import BrowserSessionStore, verify_bearer_token

_STATIC_DIR = Path(__file__).resolve().parent / "static"


class TTSRequest(BaseModel):
    text: str


class SessionLoginRequest(BaseModel):
    token: str = ""


def create_app(service: Optional[VoiceBridgeService] = None) -> FastAPI:
    svc = service or VoiceBridgeService()
    sessions = BrowserSessionStore(ttl_s=3600.0)

    app = FastAPI(
        title="JARVIS Voice Bridge",
        version="0.1.0",
        description="Bridge vocale LAN per JARVIS LEGO BOT (FastAPI + STT + AI Router + Piper TTS + Voice Lab).",
    )
    app.state.service = svc
    app.state.sessions = sessions

    if _STATIC_DIR.exists():
        app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")

    def require_auth(
        request: Request,
        authorization: Optional[str] = Header(default=None),
        jarvis_session: Optional[str] = Cookie(default=None),
        x_csrf_token: Optional[str] = Header(default=None),
    ) -> None:
        if not svc.config.require_auth:
            return
        if authorization:
            verify_bearer_token(authorization, svc.config.device_token, svc.config.require_auth)
            return
        is_mutating = request.method.upper() in {"POST", "PUT", "PATCH", "DELETE"}
        if sessions.verify(jarvis_session, x_csrf_token, require_csrf=is_mutating):
            return
        raise BridgeError("UNAUTHORIZED", "Autenticazione richiesta", http_status=401, recoverable=False)

    @app.exception_handler(BridgeError)
    async def bridge_error_handler(_request: Request, exc: BridgeError) -> JSONResponse:
        return JSONResponse(status_code=exc.http_status, content=exc.to_dict())

    @app.get("/", include_in_schema=False)
    async def index() -> FileResponse:
        index_path = _STATIC_DIR / "index.html"
        if not index_path.exists():
            raise BridgeError("UI_NOT_FOUND", "Interfaccia Voice Lab non trovata", http_status=404, recoverable=False)
        return FileResponse(str(index_path), media_type="text/html")

    @app.post("/api/v1/auth/session")
    async def create_session(payload: SessionLoginRequest, response: Response) -> dict:
        if svc.config.require_auth:
            if not svc.config.device_token:
                raise BridgeError("AUTH_MISCONFIGURED", "Token bridge non configurato", http_status=503, recoverable=False)
            if not payload.token or not hmac.compare_digest(payload.token.strip(), svc.config.device_token):
                raise BridgeError("UNAUTHORIZED", "Token non valido", http_status=401, recoverable=False)
        sid, csrf = sessions.create()
        response.set_cookie(
            key="jarvis_session",
            value=sid,
            httponly=True,
            samesite="strict",
            path="/",
            max_age=3600,
        )
        return {"authenticated": True, "csrf_token": csrf, "require_auth": svc.config.require_auth}

    @app.get("/api/v1/auth/session")
    async def check_session(jarvis_session: Optional[str] = Cookie(default=None)) -> dict:
        if not svc.config.require_auth:
            return {"authenticated": True, "require_auth": False}
        ok = sessions.verify(jarvis_session, None, require_csrf=False)
        return {"authenticated": ok, "require_auth": True}

    @app.post("/api/v1/auth/logout", dependencies=[Depends(require_auth)])
    async def logout_session(
        response: Response,
        jarvis_session: Optional[str] = Cookie(default=None),
    ) -> dict:
        sessions.revoke(jarvis_session)
        response.delete_cookie(key="jarvis_session", path="/")
        return {"authenticated": False}

    @app.get("/health")
    async def health() -> dict:
        return svc.health().to_dict()

    @app.get("/ready", dependencies=[Depends(require_auth)])
    async def ready() -> dict:
        res = svc.ready()
        return res.to_dict()

    @app.post("/api/v1/voice/process", dependencies=[Depends(require_auth)])
    async def process_voice(
        file: UploadFile = File(...),
        include_base64: bool = Query(default=True),
    ) -> dict:
        wav_bytes = await file.read()
        resp = svc.process_voice(wav_bytes, include_base64_audio=include_base64)
        return resp.to_dict()

    @app.get("/api/v1/voice/audio/{audio_id}", dependencies=[Depends(require_auth)])
    async def get_audio(audio_id: str, consume: bool = Query(default=False)) -> Response:
        wav_bytes = svc.temp_store.get(audio_id, consume=consume)
        return Response(content=wav_bytes, media_type="audio/wav")

    @app.post("/api/v1/stt", dependencies=[Depends(require_auth)])
    async def stt_diag(file: UploadFile = File(...)) -> dict:
        wav_bytes = await file.read()
        return svc.transcribe_only(wav_bytes)

    @app.post("/api/v1/stt/compare", dependencies=[Depends(require_auth)])
    async def stt_compare_diag(file: Optional[UploadFile] = File(None)) -> dict:
        wav_bytes = await file.read() if file is not None else None
        return svc.compare_stt(wav_bytes)

    @app.post("/api/v1/stt/compare-models", dependencies=[Depends(require_auth)])
    async def stt_compare_models_diag(
        file: Optional[UploadFile] = File(None),
        models: str = Form("base,small"),
        reference_text: str = Form(""),
    ) -> dict:
        wav_bytes = await file.read() if file is not None else None
        model_list = [m.strip() for m in models.split(",") if m.strip()]
        return svc.compare_stt_models(wav_bytes=wav_bytes, models=model_list, reference_text=reference_text)

    @app.post("/api/v1/tts", dependencies=[Depends(require_auth)])
    async def tts_diag(payload: TTSRequest) -> Response:
        wav_bytes = svc.synthesize_only(payload.text)
        return Response(content=wav_bytes, media_type="audio/wav")

    @app.post("/api/v1/conversation/reset", dependencies=[Depends(require_auth)])
    async def reset_conversation() -> dict:
        return svc.reset_conversation()

    @app.websocket("/ws/v1/esp32")
    async def esp32_ws_endpoint(ws: WebSocket) -> None:
        adapter = Esp32WebSocketAdapter(svc)
        await adapter.handle(ws)

    @app.on_event("startup")
    async def _startup_event() -> None:
        tts_ok, tts_msg = svc.tts.is_available()
        logging.getLogger("jarvis.voice_bridge").info("TTS startup config | ok=%s | %s", tts_ok, tts_msg)
        svc.start_prewarm()

    @app.on_event("shutdown")
    async def _shutdown_event() -> None:
        svc.close()

    return app


app = create_app()

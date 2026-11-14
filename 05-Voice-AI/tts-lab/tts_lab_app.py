"""JARVIS Voice Personality Lab (Isolated FASE 5.1 Testbed).

Supports:
  - Piper TTS (it_IT-paola-medium, it_IT-riccardo-x_low) via native piper.exe
  - Kokoro-82M (if_sara, im_nicola) via isolated .venv-kokoro (Python 3.12)
  - Microsoft Elsa Desktop (Windows SAPI5 baseline)
  - 3 Personality Profiles + custom Pitch/Speed/Expressiveness/Robot Mix
  - Non-blocking playback, instant Stop, and real latency/RAM/CPU telemetry
"""

import argparse
import json
import os
from pathlib import Path
import queue
import subprocess
import tempfile
import threading
import time
import tkinter as tk
from tkinter import ttk
from typing import Dict, Optional
import winsound

import psutil

from audio_dsp import PROFILES, process_voice_audio

LAB_DIR = Path(__file__).resolve().parent

VOICES = {
    "Piper: Paola (it_IT-paola-medium)": ("piper", "it_IT-paola-medium"),
    "Piper: Riccardo (it_IT-riccardo-x_low)": ("piper", "it_IT-riccardo-x_low"),
    "Kokoro-82M: Sara (if_sara)": ("kokoro", "if_sara"),
    "Kokoro-82M: Nicola (im_nicola)": ("kokoro", "im_nicola"),
    "Riferimento: Microsoft Elsa (SAPI)": ("sapi", "Microsoft Elsa Desktop"),
}

TEST_PHRASES: Dict[str, str] = {
    "1. Saluto": "Ciaooo! Sono JARVIS! Che bello vederti! Cosa facciamo oggi?",
    "2. Curiosità": "Oh! Questa cosa è interessante! Me la racconti meglio?",
    "3. Entusiasmo": "Wow! Ce l'abbiamo fatta! Siamo proprio una bella squadra!",
    "4. Risposta normale": "Certo! Posso aiutarti. Vediamo insieme come risolvere il problema.",
    "5. Piccola sorpresa": "Ops! Questa proprio non me l'aspettavo!",
    "6. Risposta più lunga": "Ho trovato alcune idee per il nostro progetto. Possiamo iniziare dalla soluzione più semplice e poi aggiungere nuove funzionalità, una alla volta.",
}


class KokoroClient:
    """Manages persistent .venv-kokoro worker subprocess for fast reuse & metrics."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._proc: Optional[subprocess.Popen] = None
        self.last_load_ms = 0.0

    def ensure_started(self) -> float:
        with self._lock:
            if self._proc is not None and self._proc.poll() is None:
                return 0.0
            py = LAB_DIR / ".venv-kokoro" / "Scripts" / "python.exe"
            worker = LAB_DIR / "kokoro_worker.py"
            if not py.exists():
                raise RuntimeError(".venv-kokoro non trovato")
            self._proc = subprocess.Popen(
                [str(py), str(worker)],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            ready_line = self._proc.stdout.readline().strip()
            if not ready_line:
                err = self._proc.stderr.read()
                raise RuntimeError(f"Kokoro worker avvio fallito: {err}")
            info = json.loads(ready_line)
            self.last_load_ms = float(info.get("load_ms", 0.0))
            return self.last_load_ms

    def synthesize(self, text: str, voice: str, speed: float, out_wav: Path) -> Dict[str, float]:
        load_ms = self.ensure_started()
        with self._lock:
            assert self._proc is not None and self._proc.stdin and self._proc.stdout
            req = json.dumps({"text": text, "voice": voice, "speed": speed, "out_wav": str(out_wav)})
            self._proc.stdin.write(req + "\n")
            self._proc.stdin.flush()
            resp_line = self._proc.stdout.readline().strip()
            if not resp_line:
                raise RuntimeError("Nessuna risposta dal worker Kokoro")
            resp = json.loads(resp_line)
            if not resp.get("ok"):
                raise RuntimeError(resp.get("error", "Errore Kokoro"))
            return {
                "load_ms": load_ms if load_ms > 0 else float(resp.get("load_ms", 0.0)),
                "gen_ms": float(resp.get("gen_ms", 0.0)),
                "ram_mb": float(resp.get("ram_mb", 0.0)),
                "cpu_pct": float(resp.get("cpu_pct", 0.0)),
            }

    def close(self) -> None:
        with self._lock:
            if self._proc is not None and self._proc.poll() is None:
                try:
                    self._proc.stdin.write(json.dumps({"cmd": "quit"}) + "\n")
                    self._proc.stdin.flush()
                    self._proc.wait(timeout=1.5)
                except Exception:
                    self._proc.terminate()
            self._proc = None


class TTSLabApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("JARVIS Voice Personality Lab — FASE 5.1 (Isolato)")
        self.root.configure(bg="#0B101B")
        self.root.geometry("940x680")

        self.kokoro = KokoroClient()
        self._ui_queue: "queue.Queue[dict]" = queue.Queue()
        self._sapi_proc: Optional[subprocess.Popen] = None
        self._cancel_gen = 0
        self._play_wav_path: Optional[Path] = None

        self._build_ui()
        self._poll_ui()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self) -> None:
        header = tk.Frame(self.root, bg="#0B101B", padx=14, pady=10)
        header.pack(fill="x")
        tk.Label(
            header,
            text="JARVIS Voice Lab — Ricerca Voce 'Piccolo Amichetto Robotico'",
            fg="#F8FAFC",
            bg="#0B101B",
            font=("Segoe UI", 14, "bold"),
        ).pack(side="left")

        self.status_var = tk.StringVar(value="Pronto (Laboratorio isolato)")
        tk.Label(
            header,
            textvariable=self.status_var,
            fg="#38BDF8",
            bg="#0B101B",
            font=("Consolas", 10, "bold"),
        ).pack(side="right")

        body = tk.Frame(self.root, bg="#0B101B", padx=14)
        body.pack(fill="both", expand=True)

        left = tk.Frame(body, bg="#0F172A", padx=12, pady=12)
        left.pack(side="left", fill="both", expand=True, padx=(0, 8))

        right = tk.Frame(body, bg="#0F172A", width=340, padx=12, pady=12)
        right.pack(side="right", fill="both")

        # --- LEFT: VOICE, PROFILES, PHRASES, PARAMS ---
        tk.Label(left, text="1. Seleziona Voce:", fg="#CBD5E1", bg="#0F172A", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        self.voice_var = tk.StringVar(value=list(VOICES.keys())[0])
        voice_cb = ttk.Combobox(left, textvariable=self.voice_var, values=list(VOICES.keys()), state="readonly")
        voice_cb.pack(fill="x", pady=(2, 10))

        tk.Label(left, text="2. Profilo Personalità:", fg="#CBD5E1", bg="#0F172A", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        prof_row = tk.Frame(left, bg="#0F172A")
        prof_row.pack(fill="x", pady=(2, 10))
        self.profile_var = tk.StringVar(value="1. Amichetto Dolce")
        for prof_name in PROFILES:
            tk.Radiobutton(
                prof_row,
                text=prof_name,
                variable=self.profile_var,
                value=prof_name,
                command=self._on_profile_selected,
                fg="#F8FAFC",
                bg="#1E293B",
                selectcolor="#0284C7",
                activebackground="#1E293B",
                activeforeground="#FFFFFF",
                indicatoron=False,
                padx=8,
                pady=4,
                font=("Segoe UI", 8, "bold"),
            ).pack(side="left", padx=2)

        tk.Label(left, text="3. Frasi di collaudo (FASE E):", fg="#CBD5E1", bg="#0F172A", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        phrase_row = tk.Frame(left, bg="#0F172A")
        phrase_row.pack(fill="x", pady=(2, 6))
        for label, txt in TEST_PHRASES.items():
            tk.Button(
                phrase_row,
                text=label,
                bg="#334155",
                fg="#F8FAFC",
                relief="flat",
                font=("Segoe UI", 8),
                padx=6,
                pady=3,
                command=lambda t=txt: self._set_text(t),
            ).pack(side="left", padx=2, pady=2)

        self.text_box = tk.Text(left, height=4, bg="#1E293B", fg="#F8FAFC", font=("Segoe UI", 10), wrap="word", padx=8, pady=6)
        self.text_box.pack(fill="x", pady=(2, 10))
        self.text_box.insert("1.0", TEST_PHRASES["1. Saluto"])

        # Sliders
        params = tk.LabelFrame(left, text=" 4. Parametri Vocali & DSP ", fg="#94A3B8", bg="#0F172A", padx=8, pady=6)
        params.pack(fill="x", pady=(0, 10))

        self.pitch_var = tk.DoubleVar(value=1.2)
        self.speed_var = tk.DoubleVar(value=0.98)
        self.expr_var = tk.DoubleVar(value=0.65)
        self.robot_var = tk.DoubleVar(value=0.0)

        self._add_slider(params, "Pitch (semitoni):", self.pitch_var, -4.0, 6.0, 0.2)
        self._add_slider(params, "Velocità:", self.speed_var, 0.75, 1.35, 0.02)
        self._add_slider(params, "Espressività (Piper noise):", self.expr_var, 0.20, 1.20, 0.05)
        self._add_slider(params, "Carattere Robotico (mix):", self.robot_var, 0.0, 0.25, 0.02)

        actions = tk.Frame(left, bg="#0F172A")
        actions.pack(fill="x")
        tk.Button(
            actions,
            text="▶ Genera e Riproduci",
            bg="#0284C7",
            fg="#FFFFFF",
            relief="flat",
            font=("Segoe UI", 10, "bold"),
            padx=14,
            pady=8,
            command=self._on_play,
        ).pack(side="left", padx=(0, 8))

        tk.Button(
            actions,
            text="⏹ Interrompi",
            bg="#DC2626",
            fg="#FFFFFF",
            relief="flat",
            font=("Segoe UI", 10, "bold"),
            padx=14,
            pady=8,
            command=self._on_stop,
        ).pack(side="left")

        # --- RIGHT: METRICS & BENCHMARK LOG ---
        tk.Label(right, text="Metriche Prestazioni (FASE F)", fg="#CBD5E1", bg="#0F172A", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        self.metrics_var = tk.StringVar(value="Nessun campione generato ancora.")
        tk.Label(
            right,
            textvariable=self.metrics_var,
            fg="#A7F3D0",
            bg="#1E293B",
            font=("Consolas", 9),
            justify="left",
            anchor="nw",
            padx=8,
            pady=8,
            width=40,
            height=8,
        ).pack(fill="x", pady=(4, 10))

        tk.Label(right, text="Cronologia Confronti:", fg="#CBD5E1", bg="#0F172A", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        self.log_box = tk.Text(right, bg="#1E293B", fg="#E2E8F0", font=("Consolas", 8), wrap="word", padx=6, pady=6)
        self.log_box.pack(fill="both", expand=True, pady=(4, 0))

    def _add_slider(self, parent, label: str, var: tk.DoubleVar, lo: float, hi: float, res: float) -> None:
        row = tk.Frame(parent, bg="#0F172A")
        row.pack(fill="x", pady=1)
        tk.Label(row, text=label, width=24, anchor="w", fg="#CBD5E1", bg="#0F172A", font=("Segoe UI", 8)).pack(side="left")
        tk.Scale(
            row,
            variable=var,
            from_=lo,
            to=hi,
            resolution=res,
            orient="horizontal",
            bg="#0F172A",
            fg="#F8FAFC",
            highlightthickness=0,
        ).pack(side="left", fill="x", expand=True)

    def _on_profile_selected(self) -> None:
        p = PROFILES[self.profile_var.get()]
        self.pitch_var.set(p.pitch_semitones)
        self.speed_var.set(p.speed)
        self.expr_var.set(p.expressiveness)
        self.robot_var.set(p.robot_mix)

    def _set_text(self, txt: str) -> None:
        self.text_box.delete("1.0", "end")
        self.text_box.insert("1.0", txt)

    def _on_stop(self) -> None:
        self._cancel_gen += 1
        winsound.PlaySound(None, winsound.SND_PURGE)
        if self._play_wav_path is not None and self._play_wav_path.exists():
            try:
                self._play_wav_path.unlink()
            except OSError:
                pass
            self._play_wav_path = None
        if self._sapi_proc is not None and self._sapi_proc.poll() is None:
            try:
                self._sapi_proc.terminate()
            except Exception:
                pass
        self.status_var.set("Riproduzione interrotta")

    def _on_play(self) -> None:
        self._on_stop()
        gen = self._cancel_gen
        voice_label = self.voice_var.get()
        engine, voice_id = VOICES[voice_label]
        text = self.text_box.get("1.0", "end").strip()
        if not text:
            return
        pitch = float(self.pitch_var.get())
        speed = float(self.speed_var.get())
        expr = float(self.expr_var.get())
        robot_mix = float(self.robot_var.get())
        profile_name = self.profile_var.get()

        self.status_var.set(f"Generazione in corso ({voice_label})...")
        threading.Thread(
            target=self._synth_worker,
            args=(gen, voice_label, engine, voice_id, profile_name, text, pitch, speed, expr, robot_mix),
            daemon=True,
        ).start()

    def _synth_worker(
        self,
        gen: int,
        voice_label: str,
        engine: str,
        voice_id: str,
        profile_name: str,
        text: str,
        pitch: float,
        speed: float,
        expr: float,
        robot_mix: float,
    ) -> None:
        t_total0 = time.perf_counter()
        tmp_wav: Optional[Path] = None
        try:
            fd, tmp_name = tempfile.mkstemp(prefix="jarvis_lab_", suffix=".wav")
            os.close(fd)
            tmp_wav = Path(tmp_name)

            load_ms = 0.0
            gen_ms = 0.0
            ram_mb = 0.0
            cpu_pct = 0.0

            if engine == "piper":
                piper_exe = LAB_DIR / "bin" / "piper" / "piper.exe"
                model_onnx = LAB_DIR / "models" / "piper" / f"{voice_id}.onnx"
                length_scale = 1.0 / max(0.5, speed)
                t0 = time.perf_counter()
                proc = subprocess.Popen(
                    [
                        str(piper_exe),
                        "--model", str(model_onnx),
                        "--length_scale", f"{length_scale:.3f}",
                        "--noise_scale", f"{expr:.3f}",
                        "--output_file", str(tmp_wav),
                    ],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.PIPE,
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                )
                p_info = psutil.Process(proc.pid)
                _, stderr_data = proc.communicate(input=text.encode("utf-8"))
                gen_ms = (time.perf_counter() - t0) * 1000.0
                if proc.returncode != 0:
                    raise RuntimeError(stderr_data.decode("utf-8", errors="replace"))
                ram_mb = psutil.Process().memory_info().rss / (1024.0 * 1024.0)

            elif engine == "kokoro":
                m = self.kokoro.synthesize(text, voice=voice_id, speed=speed, out_wav=tmp_wav)
                load_ms = m["load_ms"]
                gen_ms = m["gen_ms"]
                ram_mb = m["ram_mb"]
                cpu_pct = m["cpu_pct"]

            elif engine == "sapi":
                rate_sapi = max(-6, min(6, int(round((speed - 1.0) * 10.0))))
                ps = (
                    f"[Console]::InputEncoding = [System.Text.Encoding]::UTF8; "
                    f"Add-Type -AssemblyName System.Speech; "
                    f"$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
                    f"$s.Rate = {rate_sapi}; "
                    f"try {{ $s.SelectVoice('{voice_id}') }} catch {{ }}; "
                    f"$s.SetOutputToWaveFile('{str(tmp_wav)}'); "
                    f"$t = [Console]::In.ReadToEnd(); $s.Speak($t); $s.Dispose()"
                )
                t0 = time.perf_counter()
                proc = subprocess.Popen(
                    ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.PIPE,
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                )
                self._sapi_proc = proc
                proc.communicate(input=text.encode("utf-8"))
                gen_ms = (time.perf_counter() - t0) * 1000.0
                ram_mb = psutil.Process().memory_info().rss / (1024.0 * 1024.0)

            if gen != self._cancel_gen:
                return

            raw_wav = tmp_wav.read_bytes()
            t_dsp0 = time.perf_counter()
            final_wav, duration_s = process_voice_audio(raw_wav, pitch_semitones=pitch, robot_mix=robot_mix)
            dsp_ms = (time.perf_counter() - t_dsp0) * 1000.0
            total_latency_ms = (time.perf_counter() - t_total0) * 1000.0

            if gen != self._cancel_gen:
                return

            fd_out, play_name = tempfile.mkstemp(prefix="jarvis_play_", suffix=".wav")
            os.close(fd_out)
            play_path = Path(play_name)
            play_path.write_bytes(final_wav)
            self._play_wav_path = play_path
            winsound.PlaySound(str(play_path), winsound.SND_FILENAME | winsound.SND_ASYNC)

            self._ui_queue.put(
                {
                    "ok": True,
                    "voice": voice_label,
                    "profile": profile_name,
                    "load_ms": load_ms,
                    "gen_ms": gen_ms,
                    "dsp_ms": dsp_ms,
                    "latency_ms": total_latency_ms,
                    "duration_s": duration_s,
                    "ram_mb": ram_mb,
                    "cpu_pct": cpu_pct,
                }
            )
        except Exception as exc:
            self._ui_queue.put({"ok": False, "error": str(exc)})
        finally:
            if tmp_wav is not None and tmp_wav.exists():
                try:
                    tmp_wav.unlink()
                except OSError:
                    pass

    def _poll_ui(self) -> None:
        while True:
            try:
                ev = self._ui_queue.get_nowait()
            except queue.Empty:
                break
            if ev.get("ok"):
                self.status_var.set(f"In riproduzione: {ev['voice']}")
                metrics_txt = (
                    f"Voce:        {ev['voice']}\n"
                    f"Profilo:     {ev['profile']}\n"
                    f"Caricamento: {ev['load_ms']:.1f} ms\n"
                    f"Generazione: {ev['gen_ms']:.1f} ms\n"
                    f"DSP Audio:   {ev['dsp_ms']:.1f} ms\n"
                    f"Latenza tot: {ev['latency_ms']:.1f} ms\n"
                    f"Durata WAV:  {ev['duration_s']:.2f} s\n"
                    f"RAM proc:    {ev['ram_mb']:.1f} MB"
                )
                self.metrics_var.set(metrics_txt)
                self.log_box.insert(
                    "end",
                    f"[{ev['voice']}] {ev['profile']} | gen={ev['gen_ms']:.0f}ms dsp={ev['dsp_ms']:.0f}ms lat={ev['latency_ms']:.0f}ms dur={ev['duration_s']:.2f}s RAM={ev['ram_mb']:.0f}MB\n",
                )
                self.log_box.see("end")
            else:
                self.status_var.set(f"Errore: {ev.get('error')}")
        self.root.after(40, self._poll_ui)

    def _on_close(self) -> None:
        self._on_stop()
        self.kokoro.close()
        self.root.destroy()


def main() -> None:
    parser = argparse.ArgumentParser(description="JARVIS Voice Personality Lab")
    parser.add_argument("--smoke-ms", type=int, default=0)
    args = parser.parse_args()
    root = tk.Tk()
    app = TTSLabApp(root)
    if args.smoke_ms > 0:
        root.after(args.smoke_ms, app._on_close)
    root.mainloop()


if __name__ == "__main__":
    main()

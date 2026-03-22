# voice/voice_engine.py  ──  Nandhi AI Voice Module
# Supports: Whisper (STT) + pyttsx3/Coqui TTS (TTS)
# Falls back gracefully if optional deps are missing.

import os
import logging
import tempfile
import threading
from pathlib import Path

log = logging.getLogger("nandhi.voice")

# ── STT: OpenAI Whisper ─────────────────────────────────
try:
    import whisper
    _whisper_model = None  # lazy-loaded

    def get_whisper():
        global _whisper_model
        if _whisper_model is None:
            log.info("Loading Whisper model (base)…")
            _whisper_model = whisper.load_model("base")
        return _whisper_model

    HAS_WHISPER = True
except ImportError:
    HAS_WHISPER = False
    log.warning("whisper not installed. Run: pip install openai-whisper")

# ── TTS: pyttsx3 (offline, fast) ────────────────────────
try:
    import pyttsx3
    _tts_engine = None

    def get_tts():
        global _tts_engine
        if _tts_engine is None:
            _tts_engine = pyttsx3.init()
            _tts_engine.setProperty("rate", 175)
            _tts_engine.setProperty("volume", 0.95)
        return _tts_engine

    HAS_PYTTSX3 = True
except ImportError:
    HAS_PYTTSX3 = False
    log.warning("pyttsx3 not installed. Run: pip install pyttsx3")

# ── Audio recording: sounddevice ─────────────────────────
try:
    import sounddevice as sd
    import numpy as np
    import scipy.io.wavfile as wav
    HAS_AUDIO = True
except ImportError:
    HAS_AUDIO = False
    log.warning("sounddevice/scipy not installed. Run: pip install sounddevice scipy numpy")


class VoiceEngine:
    """Handles microphone recording, STT via Whisper, and TTS output."""

    def __init__(self, sample_rate: int = 16000, silence_threshold: float = 0.01, silence_duration: float = 1.5):
        self.sample_rate     = sample_rate
        self.silence_thresh  = silence_threshold
        self.silence_dur     = silence_duration
        self._speaking       = False
        self._lock           = threading.Lock()

    # ──────────────────────────────────────────────────────
    #  STT
    # ──────────────────────────────────────────────────────
    def transcribe_file(self, audio_path: str) -> str:
        """Transcribe an audio file using Whisper."""
        if not HAS_WHISPER:
            return "[Whisper not installed]"
        try:
            model  = get_whisper()
            result = model.transcribe(audio_path, fp16=False, language="en")
            return result["text"].strip()
        except Exception as e:
            log.error(f"Whisper transcription error: {e}")
            return f"[STT Error: {e}]"

    def transcribe_bytes(self, audio_bytes: bytes, fmt: str = "wav") -> str:
        """Transcribe raw audio bytes (e.g. from WebSocket upload)."""
        with tempfile.NamedTemporaryFile(suffix=f".{fmt}", delete=False) as f:
            f.write(audio_bytes)
            tmp_path = f.name
        try:
            return self.transcribe_file(tmp_path)
        finally:
            os.unlink(tmp_path)

    def record_and_transcribe(self, max_seconds: int = 10) -> str:
        """Record from mic until silence, then transcribe."""
        if not HAS_AUDIO:
            return "[sounddevice not installed]"
        if not HAS_WHISPER:
            return "[Whisper not installed]"

        log.info("Recording from microphone…")
        frames = []
        silent_chunks = 0
        chunk_size = int(self.sample_rate * 0.1)  # 100ms chunks
        max_chunks  = int(max_seconds / 0.1)

        with sd.InputStream(samplerate=self.sample_rate, channels=1, dtype="float32") as stream:
            for _ in range(max_chunks):
                chunk, _ = stream.read(chunk_size)
                frames.append(chunk)
                rms = float(np.sqrt(np.mean(chunk ** 2)))
                if rms < self.silence_thresh:
                    silent_chunks += 1
                else:
                    silent_chunks = 0
                if silent_chunks >= int(self.silence_dur / 0.1):
                    break

        if not frames:
            return ""

        audio = np.concatenate(frames, axis=0).flatten()
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            wav.write(f.name, self.sample_rate, (audio * 32767).astype("int16"))
            tmp_path = f.name

        try:
            return self.transcribe_file(tmp_path)
        finally:
            os.unlink(tmp_path)

    # ──────────────────────────────────────────────────────
    #  TTS
    # ──────────────────────────────────────────────────────
    def speak(self, text: str, blocking: bool = False):
        """Speak text using pyttsx3 (offline TTS)."""
        if not HAS_PYTTSX3 or not text.strip():
            return
        text_clean = text.replace("**", "").replace("*", "").replace("#", "").strip()
        text_clean = text_clean[:600]  # cap length

        def _speak():
            with self._lock:
                self._speaking = True
                try:
                    engine = get_tts()
                    engine.say(text_clean)
                    engine.runAndWait()
                except Exception as e:
                    log.error(f"TTS error: {e}")
                finally:
                    self._speaking = False

        if blocking:
            _speak()
        else:
            threading.Thread(target=_speak, daemon=True).start()

    def stop_speaking(self):
        """Interrupt any ongoing TTS."""
        if HAS_PYTTSX3 and self._speaking:
            try:
                get_tts().stop()
            except Exception:
                pass
        self._speaking = False

    @property
    def is_speaking(self) -> bool:
        return self._speaking

    # ──────────────────────────────────────────────────────
    #  Status
    # ──────────────────────────────────────────────────────
    def status(self) -> dict:
        return {
            "stt_available": HAS_WHISPER,
            "tts_available": HAS_PYTTSX3,
            "audio_input":   HAS_AUDIO,
            "is_speaking":   self._speaking,
        }


# Singleton
voice_engine = VoiceEngine()

"""Procedural ambient music playback.

Best-effort audio: if optional dependencies (numpy, sounddevice) are missing,
this module quietly disables itself and gameplay continues normally.
"""

from __future__ import annotations

import math
import random
import threading
import time

try:
    import numpy as np
    import sounddevice as sd
except Exception:  # pragma: no cover - optional dependency path
    np = None
    sd = None


class AmbientMusic:
    """Lightweight procedural ambient drone generator.

    Generates a soft layered sine texture that slowly shifts harmonic roots.
    """

    def __init__(
        self,
        sample_rate: int = 44100,
        block_size: int = 1024,
        amplitude: float = 0.08,
        enabled: bool = True,
    ) -> None:
        self.enabled = enabled and np is not None and sd is not None
        self.sample_rate = sample_rate
        self.block_size = block_size
        self.amplitude = amplitude

        self._running = False
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()

        self._root_hz = 110.0
        self._phase = [0.0, 0.0, 0.0]
        self._detune = [0.0, -0.003, 0.004]
        self._weights = [0.55, 0.3, 0.15]
        self._change_interval = 8.0
        self._next_change = 0.0

        # Minor-ish ambient scale roots.
        self._root_candidates = [82.41, 92.50, 98.00, 110.00, 123.47, 130.81]

    def start(self) -> None:
        """Start background ambient playback."""
        if not self.enabled or self._running:
            return
        self._running = True
        self._next_change = time.monotonic() + self._change_interval
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop playback and join background thread."""
        if not self._running:
            return
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=1.0)
            self._thread = None

    def _pick_next_root(self) -> None:
        with self._lock:
            current = self._root_hz
            candidates = [f for f in self._root_candidates if abs(f - current) > 0.01]
            self._root_hz = random.choice(candidates) if candidates else current

    def _run(self) -> None:
        assert np is not None and sd is not None

        def callback(outdata, frames, _time, _status) -> None:
            with self._lock:
                root = self._root_hz

            t = np.arange(frames, dtype=np.float64)
            signal = np.zeros(frames, dtype=np.float64)

            # Root + fifth + octave texture.
            freqs = [
                root * (1.0 + self._detune[0]),
                root * 1.5 * (1.0 + self._detune[1]),
                root * 2.0 * (1.0 + self._detune[2]),
            ]

            for i, freq in enumerate(freqs):
                phase_step = (2.0 * math.pi * freq) / self.sample_rate
                phase = self._phase[i] + phase_step * t
                signal += self._weights[i] * np.sin(phase)
                self._phase[i] = float((phase[-1] + phase_step) % (2.0 * math.pi))

            # Slow amplitude motion to avoid a static tone.
            lfo = 0.75 + 0.25 * np.sin(2.0 * math.pi * 0.08 * (t / self.sample_rate))
            signal = (signal * lfo * self.amplitude).astype(np.float32)

            # Stereo copy.
            outdata[:, 0] = signal
            outdata[:, 1] = signal

        try:
            with sd.OutputStream(
                samplerate=self.sample_rate,
                channels=2,
                dtype="float32",
                blocksize=self.block_size,
                callback=callback,
            ):
                while self._running:
                    now = time.monotonic()
                    if now >= self._next_change:
                        self._pick_next_root()
                        self._next_change = now + self._change_interval
                    time.sleep(0.2)
        except Exception:
            # Audio device/dependency errors must never crash the game.
            self.enabled = False
            self._running = False

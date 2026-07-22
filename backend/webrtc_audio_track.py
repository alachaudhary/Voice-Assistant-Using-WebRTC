import asyncio
import fractions
import time

import av
import numpy as np
from aiortc import AudioStreamTrack


class OutgoingAudioTrack(AudioStreamTrack):
    """
    Streams ElevenLabs PCM audio over WebRTC.
    Expects 16-bit mono PCM @ 24000 Hz.
    """

    def __init__(self):
        super().__init__()

        self.sample_rate = 24000
        self.channels = 1

        # 20 ms per frame
        self.samples_per_frame = 480
        self.frame_duration = self.samples_per_frame / self.sample_rate  # 0.02s

        # Buffer holding pending PCM samples
        self.buffer = np.empty((0,), dtype=np.int16)

        # Queue of newly synthesized PCM chunks
        self.queue = asyncio.Queue()

        # FastAPI event loop (set from main.py)
        self.loop = None

        # RTP timestamp
        self.samples_sent = 0

        # Signals when all queued/buffered audio has been played out
        self._playback_done = asyncio.Event()
        self._playback_done.set()

        # Real-time pacing clock (incremental, resynced after idle gaps)
        self._next_frame_time = None

    def set_event_loop(self, loop):
        self.loop = loop

    def enqueue(self, pcm_bytes: bytes):
        """
        Called from a worker thread after ElevenLabs synthesis.
        """
        print("enqueue bytes:", len(pcm_bytes))

        if self.loop is None:
            return

        self.loop.call_soon_threadsafe(self._playback_done.clear)
        self.loop.call_soon_threadsafe(
            self.queue.put_nowait,
            pcm_bytes,
        )

    async def recv(self):
        """
        Called repeatedly by aiortc.
        Returns exactly 20 ms of audio each call, paced to real time.
        """
        while len(self.buffer) < self.samples_per_frame:
            pcm_bytes = await self.queue.get()
            samples = np.frombuffer(pcm_bytes, dtype=np.int16)

            if self.buffer.size == 0:
                self.buffer = samples.copy()
            else:
                self.buffer = np.concatenate((self.buffer, samples))

        frame_samples = self.buffer[: self.samples_per_frame]
        self.buffer = self.buffer[self.samples_per_frame :]

        frame = av.AudioFrame.from_ndarray(
            frame_samples.reshape(1, -1),
            format="s16",
            layout="mono",
        )
        frame.sample_rate = self.sample_rate
        frame.pts = self.samples_sent
        frame.time_base = fractions.Fraction(1, self.sample_rate)

        # --- Real-time pacing (resyncs after idle gaps between turns) ---
        now = time.monotonic()

        if self._next_frame_time is None:
            self._next_frame_time = now

        # If we're behind by more than one frame, we just came off an idle
        # gap (waiting for the next LLM/TTS turn) — resync to now instead
        # of bursting frames to "catch up".
        if now - self._next_frame_time > self.frame_duration:
            self._next_frame_time = now

        if self._next_frame_time > now:
            await asyncio.sleep(self._next_frame_time - now)

        self._next_frame_time += self.frame_duration
        # -------------------------------------------------------------

        self.samples_sent += self.samples_per_frame

        if self.buffer.size == 0 and self.queue.empty():
            self._playback_done.set()

        return frame
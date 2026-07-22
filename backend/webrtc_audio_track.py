import asyncio
import fractions

import av
import numpy as np
from aiortc import MediaStreamTrack


class OutgoingAudioTrack(MediaStreamTrack):
    """
    Streams ElevenLabs PCM audio over WebRTC.
    Expects 16-bit mono PCM @ 24000 Hz.
    """

    kind = "audio"

    def __init__(self):
        super().__init__()

        self.sample_rate = 24000
        self.channels = 1

        # 20 ms per frame
        self.samples_per_frame = 480

        # Buffer holding pending PCM samples
        self.buffer = np.empty((0,), dtype=np.int16)

        # Queue of newly synthesized PCM chunks
        self.queue = asyncio.Queue()

        # FastAPI event loop (set from main.py)
        self.loop = None

        # RTP timestamp
        self.samples_sent = 0

    def set_event_loop(self, loop):
        self.loop = loop

    def enqueue(self, pcm_bytes: bytes):
        """
        Called from a worker thread after ElevenLabs synthesis.
        """

        if self.loop is None:
            return

        self.loop.call_soon_threadsafe(
            self.queue.put_nowait,
            pcm_bytes,
        )

    async def recv(self):
        """
        Called repeatedly by aiortc.
        Returns exactly 20 ms of audio each call.
        """

        # If we don't have enough samples, fetch another chunk.
        while len(self.buffer) < self.samples_per_frame:
            try:
                pcm_bytes = await asyncio.wait_for(
                    self.queue.get(),
                    timeout=0.02,
                )

                samples = np.frombuffer(
                    pcm_bytes,
                    dtype=np.int16,
                )

                if self.buffer.size == 0:
                    self.buffer = samples.copy()
                else:
                    self.buffer = np.concatenate((self.buffer, samples))

            except asyncio.TimeoutError:
                silence = np.zeros(
                    self.samples_per_frame,
                    dtype=np.int16,
                )

                if self.buffer.size == 0:
                    self.buffer = silence
                else:
                    self.buffer = np.concatenate((self.buffer, silence))

        # Take exactly one WebRTC frame
        frame_samples = self.buffer[: self.samples_per_frame]

        # Remove them from buffer
        self.buffer = self.buffer[self.samples_per_frame :]

        frame = av.AudioFrame.from_ndarray(
            frame_samples.reshape(1, -1),
            format="s16",
            layout="mono",
        )



        frame.sample_rate = self.sample_rate

        frame.pts = self.samples_sent

        frame.time_base = fractions.Fraction(
            1,
            self.sample_rate,
        )


        self.samples_sent += self.samples_per_frame

        return frame
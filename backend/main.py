import asyncio
import av
import json
from fastapi import FastAPI, WebSocket
from aiortc import (
    RTCPeerConnection,
    RTCSessionDescription,
    RTCIceCandidate,
)
from deepgram_stt import DeepgramLiveTranscriber
from webrtc_audio_track import OutgoingAudioTrack

from eleven_labs_tts import ElevenLabsTTS
import uvicorn
import numpy as np 

app = FastAPI()

deepgram = None
tts = None
audio_track = OutgoingAudioTrack()

resampler = av.AudioResampler(format="s16",layout="mono",rate=16000,)


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    deepgram.set_websocket(ws, asyncio.get_running_loop())
    audio_track.set_event_loop(
        asyncio.get_running_loop()
    )
    pc = RTCPeerConnection()
    pc.addTrack(audio_track)
    @pc.on("track")
    async def on_track(track):

            while True:

                

               

                # Inside while True
                frame = await track.recv()

                new_frames = resampler.resample(frame)

                for new_frame in new_frames:
                    pcm = new_frame.to_ndarray()
                    deepgram.send_audio(pcm.tobytes())
                
    @pc.on("icecandidate")
    async def on_icecandidate(candidate):

        if candidate is not None:

            await ws.send_text(json.dumps({
                "type": "candidate",
                "candidate": candidate.to_sdp()
            }))
    @pc.on("connectionstatechange")
    async def on_connectionstatechange():
        print("Connection:", pc.connectionState)
    while True:

        message = json.loads(await ws.receive_text())

        if message["type"] == "offer":

            offer = RTCSessionDescription(
                sdp=message["sdp"],
                type="offer"
            )

            await pc.setRemoteDescription(offer)

            answer = await pc.createAnswer()

            await pc.setLocalDescription(answer)

            await ws.send_text(json.dumps({
                "type": "answer",
                "sdp": pc.localDescription.sdp
            }))
            

        elif message["type"] == "candidate":
            # Ignore ICE candidates for now.
            # Browser and backend are on the same machine.
            pass


if __name__ == "__main__":

    tts = ElevenLabsTTS()

    deepgram = DeepgramLiveTranscriber()

    deepgram.set_tts_client(tts)
    deepgram.set_tts_track(audio_track)
    deepgram.start()

    uvicorn.run(app, host="0.0.0.0", port=8000)
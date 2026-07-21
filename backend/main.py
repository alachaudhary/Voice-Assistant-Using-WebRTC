
import json
from fastapi import FastAPI, WebSocket
from aiortc import (
    RTCPeerConnection,
    RTCSessionDescription,
    RTCIceCandidate,
)
from deepgram_stt import DeepgramLiveTranscriber

from eleven_labs_tts import ElevenLabsTTS
import uvicorn
import numpy as np 

app = FastAPI()

deepgram = None
tts = None




@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()

    pc = RTCPeerConnection()
    @pc.on("track")
    async def on_track(track):

            print(f"Track received: {track.kind}")

            while True:

                frame = await track.recv()

                print("Format:", frame.format.name)
                print("Layout:", frame.layout.name)
                pcm = frame.to_ndarray()

                print(
                    "Shape:", pcm.shape,
                    "dtype:", pcm.dtype,
                    "bytes:", len(pcm.tobytes())
                )
                print("Sample rate:", frame.sample_rate)


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

            candidate = RTCIceCandidate.from_sdp(
                message["candidate"]["candidate"]
            )

            candidate.sdpMid = message["candidate"]["sdpMid"]
            candidate.sdpMLineIndex = message["candidate"]["sdpMLineIndex"]

            await pc.addIceCandidate(candidate)


if __name__ == "__main__":

    tts = ElevenLabsTTS()

    deepgram = DeepgramLiveTranscriber()

    deepgram.set_tts_client(tts)

    deepgram.start()

    uvicorn.run(app, host="0.0.0.0", port=8000)
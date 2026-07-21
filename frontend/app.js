lucide.createIcons();

const micButton = document.getElementById("micButton");
const chat = document.getElementById("chatMessages");
const status = document.getElementById("status");
const socket = new WebSocket("ws://localhost:8000/ws");

const pc = new RTCPeerConnection();
pc.onicecandidate = (event) => {

    if (event.candidate) {

        socket.send(JSON.stringify({
            type: "candidate",
            candidate: event.candidate
        }));

        console.log("Sent ICE Candidate");
    }

};
pc.onconnectionstatechange = () => {
    console.log("Connection:", pc.connectionState);
};

pc.oniceconnectionstatechange = () => {
    console.log("ICE:", pc.iceConnectionState);
};

socket.onopen = () => {
    console.log("✅ WebSocket Connected");
};

socket.onmessage = async (event) => {

    const message = JSON.parse(event.data);

    switch (message.type) {

        case "answer":

            await pc.setRemoteDescription({
                type: "answer",
                sdp: message.sdp
            });

            console.log("Answer received");
            break;

        case "candidate":

            await pc.addIceCandidate(message.candidate);

            console.log("Remote ICE Candidate Added");
            break;
    }

};
let listening = false;

function addMessage(text, sender){

    const div = document.createElement("div");

    div.className = `message ${sender}`;

    div.innerText = text;

    chat.appendChild(div);

    chat.scrollTop = chat.scrollHeight;
}

micButton.addEventListener("click", async () => {

    if (!listening) {

      try {

        const stream = await navigator.mediaDevices.getUserMedia({
            audio: true,
            video: false
        });

        window.localStream = stream;

        // Add microphone track to WebRTC PeerConnection
        stream.getTracks().forEach(track => {
            pc.addTrack(track, stream);
        });

        // Create SDP Offer
        const offer = await pc.createOffer();

        // Save as local description
        await pc.setLocalDescription(offer);

        // Send Offer to Python over WebSocket
        socket.send(JSON.stringify({
            type: "offer",
            sdp: pc.localDescription.sdp
        }));

        listening = true;

        micButton.classList.add("listening");

        status.innerText = "Connecting...";

        addMessage("🎤 Microphone permission granted", "assistant");

        console.log("Offer sent to backend.");

      } catch (err) {

        console.error(err);

        status.innerText = "Permission Denied";

        addMessage("❌ Microphone permission denied", "assistant");
      }

    } else {

        window.localStream.getTracks().forEach(track => track.stop());

        listening = false;

        micButton.classList.remove("listening");

        status.innerText = "Idle";

        addMessage("Microphone stopped.", "assistant");
    }

});


document.addEventListener("DOMContentLoaded", () => {
    const micBtn = document.getElementById('mic-btn');
    const messageInput = document.getElementById('message-input');
    
    let mediaRecorder;
    let audioChunks = [];
    let isRecording = false;

    // Check if browser supports audio recording
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        console.warn("Media stream not supported by this browser.");
        micBtn.style.display = 'none';
        return;
    }

    micBtn.addEventListener('click', toggleRecording);

    async function toggleRecording() {
        if (isRecording) {
            stopRecording();
        } else {
            await startRecording();
        }
    }

    async function startRecording() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            mediaRecorder = new MediaRecorder(stream);
            audioChunks = [];

            mediaRecorder.ondataavailable = event => {
                if (event.data.size > 0) {
                    audioChunks.push(event.data);
                }
            };

            mediaRecorder.onstop = processAudio;

            mediaRecorder.start();
            isRecording = true;
            
            // UI Feedback: Make the mic button pulse red
            micBtn.innerHTML = '<i class="fa-solid fa-stop text-lg text-white"></i>';
            micBtn.classList.remove('text-gray-400', 'hover:text-red-400');
            micBtn.classList.add('bg-red-600', 'text-white', 'animate-pulse', 'shadow-[0_0_15px_rgba(220,38,38,0.7)]');
            
            messageInput.placeholder = "Listening...";

        } catch (err) {
            console.error("Microphone access denied or error:", err);
            alert("Please allow microphone access to talk to ANDSE.");
        }
    }

    function stopRecording() {
        if (mediaRecorder && mediaRecorder.state !== 'inactive') {
            mediaRecorder.stop();
            // Stop all audio tracks to release the hardware light
            mediaRecorder.stream.getTracks().forEach(track => track.stop());
        }
        
        isRecording = false;
        
        // UI Feedback: Revert mic button
        micBtn.innerHTML = '<i class="fa-solid fa-microphone text-lg"></i>';
        micBtn.classList.add('text-gray-400', 'hover:text-red-400');
        micBtn.classList.remove('bg-red-600', 'text-white', 'animate-pulse', 'shadow-[0_0_15px_rgba(220,38,38,0.7)]');
        
        messageInput.placeholder = "Transcribing...";
    }

    async function processAudio() {
        // 1. Create a Blob from the recorded chunks
        const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
        
        // 2. Prepare FormData to send to our backend
        const formData = new FormData();
        formData.append('audio', audioBlob, 'recording.webm');

        try {
            // 3. Send to backend STT (Speech-to-Text) endpoint
            const response = await fetch('/chat/transcribe', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (data.success) {
                // 4. Inject the transcribed text into the chat input
                messageInput.value = data.text;
                messageInput.style.height = 'auto';
                messageInput.style.height = (messageInput.scrollHeight) + 'px';
                messageInput.placeholder = "Message ANDSE...";
                
                // Optional: Auto-send the message once transcribed
                // document.getElementById('send-btn').click(); 
            } else {
                messageInput.placeholder = "Message ANDSE...";
                alert("Could not understand audio. Please try again.");
            }
        } catch (error) {
            console.error("Transcription error:", error);
            messageInput.placeholder = "Message ANDSE...";
        }
    }
});
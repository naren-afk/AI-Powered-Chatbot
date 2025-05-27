document.addEventListener("DOMContentLoaded", function () {
    const micButton = document.getElementById("micButton");
    const waveAnimation = document.getElementById("waveAnimation");
    const chatBox = document.getElementById("chatBox");
    const welcomeText = document.getElementById("welcomeText");

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.lang = "en-US";
    recognition.interimResults = false;

    let speechSynthesisUtterance = new SpeechSynthesisUtterance();
    let speaking = false; // Track if AI is speaking
    
    window.addEventListener("beforeunload", function (event) {
        console.log("🔄 Page is reloading!");
    });
    
    function appendMessage(sender, message) {
        // Ensure chatBox is visible
        chatBox.classList.remove("hidden");

        // Append user or AI message
        let messageDiv = document.createElement("div");
        messageDiv.classList.add(sender === "user" ? "user-message" : "ai-message");
        messageDiv.textContent = message;
        chatBox.appendChild(messageDiv);

        // Scroll to the latest message
        chatBox.scrollTop = chatBox.scrollHeight;
    }
    micButton.addEventListener("click", function (event) {
        event.preventDefault(); // Stops any unwanted form submission or default behavior
        if (speaking) {
            window.speechSynthesis.cancel(); // Stop speaking if mic is pressed again
            speaking = false;
        }
        startListening();
    });
    

    function startListening() {
        welcomeText.classList.add("hidden");
        chatBox.classList.remove("hidden");

        waveAnimation.classList.remove("hidden");
        waveAnimation.style.opacity = 1;
        recognition.start();
    }

    recognition.onresult = function (event) {
        let lastIndex = event.results.length - 1; // Get the latest result
        let userCommand = event.results[lastIndex][0].transcript.toLowerCase().trim(); // Ensure lowercase & trimmed text

        console.log("Recognized Command:", userCommand); // Debugging output

        addMessage(userCommand, "user"); // Show user message in UI
        sendToBackend(userCommand); // Send processed command to AI backend
    };

    recognition.onerror = function (event) {
        console.error("Speech recognition error:", event.error);
        addMessage("Sorry, I didn't catch that.", "ai");
        stopAnimation();
    };

    recognition.onend = function () {
        stopAnimation();
         chatBox.classList.remove("hidden");
        console.log("🎤 Listening stopped, but keeping chat visible.");
    };

    function sendToBackend(command) {
        fetch("http://127.0.0.1:8000/process_voice", {  
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ text: command }),
        })
        .then(response => response.json())
        .then(data => {
            // ✅ Immediately show response in the frontend
            appendMessage("ai", data.response);
    
            if (data.details) {
                appendMessage("ai", data.details);
            }
    
            if (data.read_aloud) {
                readAloud(data.response);
            }
    
            // ✅ Store chat in the background (async) without affecting UI
            setTimeout(() => storeChat(command, data.response), 100000);
        })
        .catch(error => {
            console.error("Error:", error);
            appendMessage("ai", "An error occurred.");
        });
    }
    

    function storeChat(userInput, aiResponse) {
        fetch("http://127.0.0.1:8000/store_chat", {  
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ 
                user_input: userInput, 
                ai_response: aiResponse 
            }),
        })
        .then(response => response.json())
        .then(data => {
            console.log("✅ Chat stored successfully:", data);
        })
        .catch(error => {
            console.error("🚨 Error storing chat:", error);
        });
    }
    
    

    function addMessage(text, sender) {
        let message = document.createElement("div");
        message.classList.add(sender);
        message.textContent = text;
        chatBox.appendChild(message);
        chatBox.scrollTop = chatBox.scrollHeight;
        chatBox.classList.remove("hidden"); 
        chatBox.scrollTop = chatBox.scrollHeight; 
    
    }

    function typeMessage(text, sender) {
        let message = document.createElement("div");
        message.classList.add(sender, "typing");
        chatBox.appendChild(message);

        let index = 0;
        let interval = setInterval(() => {
            if (index < text.length) {
                message.textContent = text.substring(0, index + 1);
                index++;
            } else {
                clearInterval(interval);
                message.classList.remove("typing");
            }
        }, 50);
        
        chatBox.scrollTop = chatBox.scrollHeight;
    }
    function readAloud(text) {
        // Configure the speech synthesis utterance
        speechSynthesisUtterance.text = text;
        window.speechSynthesis.speak(speechSynthesisUtterance);
        speaking = true;
    }
    function stopAnimation() {
        waveAnimation.style.opacity = 0;
        setTimeout(() => waveAnimation.classList.add("hidden"), 500);
    }
});

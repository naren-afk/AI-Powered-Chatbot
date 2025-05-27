document.addEventListener("DOMContentLoaded", function () {
    fetchSessions();
});

function fetchSessions() {
    fetch("http://127.0.0.1:8000/get_sessions")
        .then(response => response.json())
        .then(data => {
            console.log("✅ Session Data Received:", data); // Debugging output
            const sessionList = document.getElementById("session-list");
            sessionList.innerHTML = "";

            if (!data || Object.keys(data).length === 0) {
                sessionList.innerHTML = "<p>No chat sessions found.</p>";
                return;
            }

            for (const category in data) {
                if (Array.isArray(data[category]) && data[category].length > 0) {
                    const sectionDiv = document.createElement("div");
                    sectionDiv.className = "session-group";
                    sectionDiv.innerHTML = `<h3>${category}</h3>`;

                    const table = document.createElement("table");
                    table.className = "session-table";
                    table.innerHTML = `
                        <tr>
                            <th>#</th>
                            <th>Session ID</th>
                            <th>Usage Time</th>
                            <th>Action</th>
                        </tr>
                    `;

                    data[category].forEach((session, index) => {
                        if (session.id && session.time) {  // Ensure session data exists
                            const row = document.createElement("tr");
                            row.innerHTML = `
                                <td>${index + 1}</td>
                                <td>Session ${session.id}</td>
                                <td>${session.time}</td>
                                <td><button class="view-btn" onclick="viewSession(${session.id})">View</button></td>
                            `;
                            table.appendChild(row);
                        }
                    });

                    sectionDiv.appendChild(table);
                    sessionList.appendChild(sectionDiv);
                }
            }
        })
        .catch(error => {
            console.error("🚨 Fetch Sessions Error:", error); // Debugging output
            document.getElementById("session-list").innerHTML = "<p>Error loading chat sessions. Try again later.</p>";
        });
}


function viewSession(sessionId) {
    document.getElementById("session-list").style.display = "none";

    fetch(`http://127.0.0.1:8000/get_chat_history/${sessionId}`)
        .then(response => response.json())
        .then(messages => {
            const chatContainer = document.getElementById("chat-container");
            const chatMessages = document.getElementById("chat-messages");

            chatMessages.innerHTML = ""; // Clear previous messages

            if (!Array.isArray(messages) || messages.length === 0) {
                chatMessages.innerHTML = "<p>No messages found for this session.</p>";
            } else {
                messages.forEach(msg => {
                    if (msg.user && msg.bot && msg.time) {  // Ensure message fields exist
                        chatMessages.innerHTML += `
                            <div class="message">
                                <p class="user-msg"><strong>User:</strong> ${msg.user}</p>
                                <p class="bot-msg"><strong>AI:</strong> ${msg.bot}</p>
                                <span class="msg-time">${msg.time}</span>
                            </div>
                        `;
                    }
                });
            }

            chatContainer.style.display = "block"; // Show chat box
        })
        .catch(error => {
            console.error("🚨 Error fetching chat messages:", error);
            document.getElementById("chat-messages").innerHTML = "<p>Error loading messages. Try again later.</p>";
        });
}

function closeChat() {
    document.getElementById("chat-container").style.display = "none";
    document.getElementById("session-list").style.display = "block"; // Show sessions again
}

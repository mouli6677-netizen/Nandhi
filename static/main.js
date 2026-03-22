// static/main.js
// FIX: original sent ws.send(input.value) — a raw string. The server's
// websocket_endpoint does json.loads(data) and reads msg["type"], so sending
// a plain string caused a JSONDecodeError and broke the connection on every
// message. Wrap the message in the expected JSON envelope instead.

let ws = new WebSocket("ws://localhost:8080/ws");

let chatDiv = document.getElementById("chat");
let input = document.getElementById("input");
let sendBtn = document.getElementById("send");

ws.onmessage = function(event) {
    let data = JSON.parse(event.data);

    // Only render chat messages (ignore stats-only frames)
    if (data.type !== "chat") return;

    let html = `<p><span class="user">You:</span> ${data.user}</p>`;
    html += `<p><span class="nandhi">Nandhi:</span> ${data.nandhi}</p>`;
    html += `<p>Confidence: ${data.confidence}, Memory: ${data.memory_count}, Reward: ${data.reward_score}, Knowledge Nodes: ${data.knowledge_nodes}, Active Threads: ${data.active_threads}</p>`;
    chatDiv.innerHTML += html + "<hr>";
    chatDiv.scrollTop = chatDiv.scrollHeight;
};

sendBtn.onclick = function() {
    let text = input.value.trim();
    if (!text) return;
    // FIX: send JSON envelope that the server can parse
    ws.send(JSON.stringify({ type: "chat", message: text }));
    input.value = "";
};

// FIX: also allow sending with Enter key — omitted in original
input.addEventListener("keydown", function(e) {
    if (e.key === "Enter") sendBtn.onclick();
});
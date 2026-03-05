let ws = new WebSocket("ws://localhost:8080/ws");

let chatDiv = document.getElementById("chat");
let input = document.getElementById("input");
let sendBtn = document.getElementById("send");

ws.onmessage = function(event) {
    let data = JSON.parse(event.data);
    let html = `<p><span class="user">You:</span> ${data.user}</p>`;
    html += `<p><span class="nandhi">Nandhi:</span> ${data.nandhi}</p>`;
    html += `<p>Confidence: ${data.confidence}, Memory: ${data.memory_count}, Reward: ${data.reward_score}, Knowledge Nodes: ${data.knowledge_nodes}, Active Threads: ${data.active_threads}</p>`;
    chatDiv.innerHTML += html + "<hr>";
    chatDiv.scrollTop = chatDiv.scrollHeight;
};

sendBtn.onclick = function() {
    ws.send(input.value);
    input.value = "";
};
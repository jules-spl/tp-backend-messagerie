document.addEventListener("DOMContentLoaded", () => {
    let ws = null;
    let currentUser = null;
    let inboxMessages = [];
    let sentMessages = [];

    const loginSection = document.getElementById("loginSection");
    const appContainer = document.getElementById("app");

    // fonction de connexion
    const connect = () => {
        const username = document.getElementById("userName").value.trim();
        const email = document.getElementById("userEmail").value.trim();

        if (!username || !email) return alert("Pseudo et Email requis !");

        currentUser = username;
        ws = new WebSocket(`ws://localhost:8000/ws/${currentUser}`);

        ws.onopen = () => {
            loginSection.classList.add("hidden");
            appContainer.classList.remove("hidden");
            document.getElementById("connectedAs").innerText = currentUser;
        };

        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (data.action === "userlist") {
                updateSidebar(data.users);
            } else if (data.action === "message") {
                inboxMessages.push(data);
                renderMessages("Inbox", inboxMessages);
            }
        };

        ws.onclose = () => {
            alert("Déconnecté du serveur.");
            loginSection.classList.remove("hidden");
            appContainer.classList.add("hidden");
        };
    };

    // bouton de connexion
    document.getElementById("setUsername").onclick = connect;

    // envoi de message
    document.getElementById("sendMessage").onclick = () => {
        const recipient = document.getElementById("recipient").value.trim();
        const text = document.getElementById("message").value;

        if (!recipient || !text) return alert("Destinataire et message requis.");

        const payload = {
            action: "sendmessage",
            recipient: recipient,
            subject: document.getElementById("subject").value || "Chat",
            message: text
        };

        ws.send(JSON.stringify(payload));
        sentMessages.push({ ...payload, sender: currentUser, time: new Date().toLocaleTimeString() });
        renderMessages("Sent", sentMessages);
        document.getElementById("message").value = "";
    };

    // mise à jour de la barre de contacts 
    const updateSidebar = (users) => {
    const ul = document.getElementById("allUsers");
    ul.innerHTML = users.map(u => `
        <li class="user-item">
            <span class="status-online"></span> ${u} ${u === currentUser ? "(Moi)" : ""}
        </li>
    `).join('');
    };

    // affichage des messages
    const renderMessages = (id, list) => {
        const container = document.getElementById(id);
        container.innerHTML = list.map(m => `
            <div class="bubble ${id === 'Inbox' ? 'received' : 'sent'}">
                <span class="msg-author">${id === 'Inbox' ? m.sender : 'À: '+m.recipient}</span>
                <p>${m.message}</p>
            </div>
        `).join('');
        container.scrollTop = container.scrollHeight;
    };

    // onglets
    document.getElementById("btnInbox").onclick = () => switchTab("Inbox", "btnInbox");
    document.getElementById("btnSent").onclick = () => switchTab("Sent", "btnSent");

    function switchTab(tabId, btnId) {
        document.querySelectorAll(".tabcontent").forEach(t => t.style.display = "none");
        document.querySelectorAll(".tablinks").forEach(b => b.classList.remove("active"));
        document.getElementById(tabId).style.display = "flex";
        document.getElementById(btnId).classList.add("active");
    }
});
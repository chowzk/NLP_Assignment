let chatStarted = false;
const chatArea = document.getElementById('chat-area');
const inputArea = document.getElementById('input-area');
const messageInput = document.getElementById('message-input');
const chatTitle = document.querySelector('.chat-title');
const loading = document.getElementById('loading');

// Theme toggle
document.getElementById('toggle-theme').addEventListener('click', function() {
    const body = document.body;
    const sidebar = document.getElementById('sidebar');
    const chatItems = document.querySelectorAll('.list-group-item');
    const toggleButton = this;
    const searchInput = document.querySelector('.form-control');
    const searchIcon = document.querySelector('.input-group-text');
    const dropdownButtons = document.querySelectorAll('.dropdown-toggle');
    const dropdownMenus = document.querySelectorAll('.dropdown-menu');

    if (body.getAttribute('data-theme') === 'dark') {
        body.setAttribute('data-theme', 'light');
        sidebar.classList.replace('dark-theme', 'light-theme');
        chatItems.forEach(item => item.classList.replace('dark-theme', 'light-theme'));
        toggleButton.classList.replace('btn-outline-light', 'btn-outline-dark');
        toggleButton.textContent = '🌞';
        searchInput.classList.remove('bg-dark', 'text-white');
        searchIcon.classList.remove('bg-dark', 'text-white');
        dropdownButtons.forEach(btn => btn.classList.replace('btn-dark', 'btn-light'));
        dropdownMenus.forEach(menu => {
            menu.classList.replace('dropdown-menu-dark', 'dropdown-menu-light');
            menu.style.backgroundColor = '#ffffff';
            menu.querySelectorAll('.dropdown-item').forEach(item => {
                item.style.color = 'black';
                item.addEventListener('mouseover', () => item.style.backgroundColor = '#e9ecef');
                item.addEventListener('mouseout', () => item.style.backgroundColor = '');
            });
        });
    } else {
        body.setAttribute('data-theme', 'dark');
        sidebar.classList.replace('light-theme', 'dark-theme');
        chatItems.forEach(item => item.classList.replace('light-theme', 'dark-theme'));
        toggleButton.classList.replace('btn-outline-dark', 'btn-outline-light');
        toggleButton.textContent = '🌙';
        searchInput.classList.add('bg-dark', 'text-white');
        searchIcon.classList.add('bg-dark', 'text-white');
        dropdownButtons.forEach(btn => btn.classList.replace('btn-light', 'btn-dark'));
        dropdownMenus.forEach(menu => {
            menu.classList.replace('dropdown-menu-light', 'dropdown-menu-dark');
            menu.style.backgroundColor = '#343a40';
            menu.querySelectorAll('.dropdown-item').forEach(item => {
                item.style.color = 'white';
                item.addEventListener('mouseover', () => item.style.backgroundColor = '#495057');
                item.addEventListener('mouseout', () => item.style.backgroundColor = '');
            });
        });
    }
});

// Chat functionality
chatTitle.addEventListener('mouseover', () => {
    if (chatStarted) chatTitle.style.border = '1px solid var(--border-color)';
});

chatTitle.addEventListener('mouseout', () => {
    if (!chatTitle.classList.contains('editing')) chatTitle.style.border = 'none';
});

chatTitle.addEventListener('click', () => {
    if (!chatStarted) return;
    chatTitle.contentEditable = true;
    chatTitle.classList.add('editing');
    chatTitle.focus();
});

chatTitle.addEventListener('blur', () => {
    const text = chatTitle.textContent.trim();
    if (text === '' || /^\s+$/.test(text)) chatTitle.textContent = 'New Chat';
    chatTitle.contentEditable = false;
    chatTitle.classList.remove('editing');
    chatTitle.style.border = 'none';
});

function sendMessage() {
    const message = messageInput.value.trim();
    if (!message) return;

    if (!chatStarted) {
        chatStarted = true;
        chatArea.classList.add('active');
        chatArea.querySelector('.greeting').remove();
        inputArea.classList.add('fixed');
        chatTitle.textContent = message.slice(0, 20) + (message.length > 20 ? '...' : '');
    }

    const userBubble = document.createElement('div');
    userBubble.className = 'chat-bubble user';
    userBubble.textContent = message;
    chatArea.appendChild(userBubble);
    messageInput.value = '';

    loading.style.display = 'block';
    const startTime = Date.now();

    fetch('/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message })
    })
    .then(response => response.json())
    .then(data => {
        loading.style.display = 'none';
        const assistantBubble = document.createElement('div');
        assistantBubble.className = 'chat-bubble assistant';
        assistantBubble.textContent = data.response;

        const actions = document.createElement('div');
        actions.className = 'response-actions';
        actions.innerHTML = `
            <img src="https://via.placeholder.com/20?text=📋" alt="Copy" title="Copy Response" onclick="copyResponse('${data.response}')">
            <img src="https://via.placeholder.com/20?text=🔄" alt="Regenerate" title="Regenerate" onclick="regenerateResponse('${message}')">
        `;
        assistantBubble.appendChild(actions);

        const timeUsed = document.createElement('div');
        timeUsed.className = 'time-used';
        timeUsed.textContent = `Generated in ${(Date.now() - startTime) / 1000} seconds`;
        assistantBubble.appendChild(timeUsed);

        chatArea.appendChild(assistantBubble);
        chatArea.scrollTop = chatArea.scrollHeight;
    });
}

function copyResponse(text) {
    navigator.clipboard.writeText(text);
    alert('Response copied!');
}

function regenerateResponse(message) {
    const lastAssistant = chatArea.querySelector('.chat-bubble.assistant:last-child');
    if (lastAssistant) lastAssistant.remove();
    sendMessage(message);
}

function deleteChat() {
    chatArea.innerHTML = '<div class="greeting"><h2>Hi, I\'m TextInsight</h2><p>Upload a document so I can help you.</p></div>';
    inputArea.classList.remove('fixed');
    chatTitle.textContent = 'New Chat';
    chatStarted = false;
}

function exportChat() {
    const chatContent = Array.from(chatArea.querySelectorAll('.chat-bubble'))
        .map(bubble => `${bubble.classList.contains('user') ? 'You' : 'TextInsight'}: ${bubble.textContent}`)
        .join('\n');
    const blob = new Blob([chatContent], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'chat.txt';
    a.click();
    URL.revokeObjectURL(url);
}

messageInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});
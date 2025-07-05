document.addEventListener('DOMContentLoaded', function() {
    const chatMessages = document.getElementById('chatMessages');
    const messageInput = document.getElementById('messageInput');
    const sendButton = document.getElementById('sendButton');
    const voiceButton = document.getElementById('voiceButton');
    const stopVoiceButton = document.getElementById('stopVoiceButton');
    const voiceStatus = document.getElementById('voiceStatus');
    const exampleButtons = document.querySelectorAll('.example-question');
    const searchInput = document.getElementById('searchInput');
    const partsTable = document.getElementById('partsTable');
    let selectedLang = document.querySelector('input[name="language"]:checked')?.value || 'en-US';

    // Update selected language
    document.querySelectorAll('input[name="language"]').forEach(radio => {
        radio.addEventListener('change', function() {
            selectedLang = this.value;
        });
    });

    // Search functionality
    if (searchInput && partsTable) {
        searchInput.addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase();
            const rows = partsTable.querySelectorAll('tr');
            
            rows.forEach(row => {
                const text = row.textContent.toLowerCase();
                if (text.includes(searchTerm)) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            });
        });
    }

    // Append message to chat
    function appendMessage(content, sender) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message ' + (sender === 'bot' ? 'bot-message' : 'user-message');
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        contentDiv.textContent = content;
        messageDiv.appendChild(contentDiv);
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    // Send message to backend
    function sendMessage(text) {
        if (!text) return;
        appendMessage(text, 'user');
        messageInput.value = '';
        fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: text, language: selectedLang })
        })
        .then(res => res.json())
        .then(data => {
            if (data.response) {
                appendMessage(data.response, 'bot');
                speakText(data.response, selectedLang);
            } else if (data.error) {
                appendMessage('Error: ' + data.error, 'bot');
            }
        })
        .catch(err => {
            appendMessage('Error: ' + err, 'bot');
        });
    }

    if (sendButton && messageInput) {
        sendButton.addEventListener('click', () => sendMessage(messageInput.value.trim()));
        messageInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter') sendMessage(messageInput.value.trim());
        });
    }

    exampleButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            messageInput.value = btn.textContent;
            sendMessage(btn.textContent);
        });
    });

    // Voice recognition
    let recognition;
    if ('webkitSpeechRecognition' in window) {
        recognition = new webkitSpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = false;
        recognition.lang = selectedLang;

        recognition.onstart = function() {
            voiceStatus.textContent = 'Listening...';
            voiceButton.style.display = 'none';
            stopVoiceButton.style.display = '';
        };
        recognition.onend = function() {
            voiceStatus.textContent = '';
            voiceButton.style.display = '';
            stopVoiceButton.style.display = 'none';
        };
        recognition.onerror = function(event) {
            voiceStatus.textContent = 'Error: ' + event.error;
            voiceButton.style.display = '';
            stopVoiceButton.style.display = 'none';
        };
        recognition.onresult = function(event) {
            const transcript = event.results[0][0].transcript;
            messageInput.value = transcript;
            sendMessage(transcript);
        };

        if (voiceButton) {
            voiceButton.addEventListener('click', function() {
                recognition.lang = selectedLang;
                recognition.start();
            });
        }
        if (stopVoiceButton) {
            stopVoiceButton.addEventListener('click', function() {
                recognition.stop();
            });
        }
    } else {
        if (voiceButton) {
            voiceButton.disabled = true;
        }
        if (voiceStatus) {
            voiceStatus.textContent = 'Voice recognition not supported in this browser.';
        }
    }

    // Text-to-speech
    function speakText(text, lang) {
        if ('speechSynthesis' in window) {
            const utterance = new SpeechSynthesisUtterance(text);
            utterance.lang = lang;
            window.speechSynthesis.speak(utterance);
        }
    }
}); 
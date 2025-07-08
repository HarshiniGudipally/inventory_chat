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
    const exportBtn = document.getElementById('exportBtn');
    let selectedLang = document.querySelector('input[name="language"]:checked')?.value || 'en-US';
    let currentSessionId = null;

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
        
        const requestData = { 
            message: text, 
            language: selectedLang 
        };
        
        if (currentSessionId) {
            requestData.session_id = currentSessionId;
        }
        
        fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestData)
        })
        .then(res => res.json())
        .then(data => {
            if (data.response) {
                appendMessage(data.response, 'bot');
                speakText(data.response, selectedLang);
                
                // Store session ID and show export button
                if (data.session_id) {
                    currentSessionId = data.session_id;
                    if (exportBtn) exportBtn.style.display = 'inline-block';
                }
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
    
    // Clear chat function
    window.clearChat = function() {
        if (confirm('Are you sure you want to clear the chat?')) {
            chatMessages.innerHTML = `
                <div class="message bot-message">
                    <div class="message-content">
                        Hello! I'm your AI assistant for the SLN AUTOMOBILES inventory. Ask me anything about parts, stock levels, suppliers, or get restock recommendations. You can speak or type your questions.
                    </div>
                </div>
            `;
            currentSessionId = null;
            if (exportBtn) exportBtn.style.display = 'none';
        }
    };
    
    // Export chat function
    window.exportChat = function() {
        if (currentSessionId) {
            window.open(`/api/export-chat/${currentSessionId}`, '_blank');
        } else {
            alert('No chat session to export');
        }
    };
    
    // Simple hover preview functionality
    function initImagePreview() {
        // Remove existing preview if any
        const existingPreview = document.querySelector('.image-preview');
        if (existingPreview) {
            existingPreview.remove();
        }
        
        // Create preview element
        const preview = document.createElement('div');
        preview.className = 'image-preview';
        preview.innerHTML = `
            <img src="" alt="Preview">
            <div class="preview-info"></div>
        `;
        document.body.appendChild(preview);
        
        // Add hover events to images
        const previewImages = document.querySelectorAll('img.hover-preview');
        
        previewImages.forEach(img => {
            img.onmouseenter = function(e) {
                const imageSrc = this.src;
                const partName = this.alt || 'Part';
                const partNumber = this.getAttribute('data-part-number') || 'Unknown';
                
                if (imageSrc) {
                    const previewImg = preview.querySelector('img');
                    const previewInfo = preview.querySelector('.preview-info');
                    
                    previewImg.src = imageSrc;
                    previewInfo.textContent = `${partName} (${partNumber})`;
                    
                    preview.style.left = (e.clientX + 20) + 'px';
                    preview.style.top = (e.clientY - 20) + 'px';
                    preview.classList.add('show');
                }
            };
            
            img.onmouseleave = function() {
                preview.classList.remove('show');
            };
        });
    }
    
    // Initialize image preview when page loads
    if (document.querySelector('.hover-preview')) {
        initImagePreview();
    }
    
    // Initialize image preview when page loads
    window.addEventListener('load', function() {
        if (document.querySelector('.hover-preview')) {
            initImagePreview();
        }
    });
    
    // Also initialize after any dynamic content changes
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.addedNodes.length > 0) {
                const hasNewImages = Array.from(mutation.addedNodes).some(node => 
                    node.nodeType === 1 && node.querySelector && node.querySelector('.hover-preview')
                );
                if (hasNewImages) {
                    initImagePreview();
                }
            }
        });
    });
    
    // Start observing
    if (document.body) {
        observer.observe(document.body, { childList: true, subtree: true });
    }
}); 
// static/script.js

const chatBox = document.getElementById('chat-box');
const chatForm = document.getElementById('chat-form');
const userInput = document.getElementById('user-input');
const sendButton = chatForm.querySelector('button');
const resetButton = document.getElementById('reset-button'); // Get reset button

// Admin Panel Elements
// ... (Admin elements remain the same) ...
const adminUnderstanding = document.getElementById('admin-understanding');
const adminFunctions = document.getElementById('admin-functions');
const adminSummarization = document.getElementById('admin-summarization');
const adminErrorSection = document.getElementById('admin-error-section');
const adminErrorMessage = document.getElementById('admin-error-message');


let websocket;
let currentAiMessageDiv = null;
let currentThinkingUl = null;
let thoughtQueue = [];
let isProcessingQueue = false;
let isThinkingGloballyVisible = false;

// --- Animation Configuration ---
const thoughtFadeInDuration = 500;
const interThoughtDelay = 100;

// --- WebSocket Connection ---
// ... (connectWebSocket remains the same) ...
function connectWebSocket() {
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${wsProtocol}//${window.location.host}/ws`;
    console.log(`Connecting to WebSocket: ${wsUrl}`);

    websocket = new WebSocket(wsUrl);

    websocket.onopen = (event) => {
        console.log("WebSocket connection opened");
        userInput.disabled = false;
        sendButton.disabled = false;
        resetButton.disabled = false; // Enable reset button on connect
        userInput.focus();
        const connError = document.getElementById('connection-error');
        if (connError) connError.remove();
    };

    websocket.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            handleWebSocketMessage(data);
        } catch (e) {
            console.error("Failed to parse WebSocket message or handle it:", e);
            addErrorMessageToChat(`Error processing message from server: ${e}`);
        }
    };

    websocket.onerror = (event) => {
        console.error("WebSocket error:", event);
        addErrorMessageToChat("Connection error. Please refresh the page.", "connection-error");
        userInput.disabled = true;
        sendButton.disabled = true;
        resetButton.disabled = true; // Disable reset button on error
    };

    websocket.onclose = (event) => {
        console.log("WebSocket connection closed:", event.code, event.reason);
        if (!event.wasClean) {
             addErrorMessageToChat("Connection closed unexpectedly. Please refresh the page.", "connection-error");
        }
        userInput.disabled = true;
        sendButton.disabled = true;
        resetButton.disabled = true; // Disable reset button on close
        currentAiMessageDiv = null;
        currentThinkingUl = null;
        thoughtQueue = [];
        isProcessingQueue = false;
    };
}


// --- UI Update Functions ---
// ... (addUserMessage, createAiMessageContainer, queueThoughtOrStatusForAnimation, processThoughtQueue, addFinalResponseToCurrentMessage, addErrorMessageToChat, toggleThinking, updateAdminPanel, scrollToBottom remain the same) ...
function addUserMessage(message) {
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('message', 'user-message');
    const contentDiv = document.createElement('div');
    contentDiv.classList.add('message-content');
    contentDiv.textContent = message;
    messageDiv.appendChild(contentDiv);
    chatBox.appendChild(messageDiv);
    scrollToBottom();
}

function createAiMessageContainer() {
    currentAiMessageDiv = document.createElement('div');
    currentAiMessageDiv.classList.add('message', 'ai-message');

    const contentDiv = document.createElement('div');
    contentDiv.classList.add('message-content');
    currentAiMessageDiv.appendChild(contentDiv);

    const thinkingPlaceholder = document.createElement('div');
    thinkingPlaceholder.classList.add('thinking-placeholder');
    thinkingPlaceholder.textContent = 'Understanding your request...';
    contentDiv.appendChild(thinkingPlaceholder);

    chatBox.appendChild(currentAiMessageDiv);
    scrollToBottom();
    return contentDiv;
}

function queueThoughtOrStatusForAnimation(text, isStatus = false) {
    thoughtQueue.push({ text: text, isStatus: isStatus });
    if (!isProcessingQueue) {
        processThoughtQueue();
    }
}

function processThoughtQueue() {
    if (thoughtQueue.length === 0) {
        isProcessingQueue = false;
        return;
    }

    isProcessingQueue = true;
    const item = thoughtQueue.shift();
    const text = item.text;
    const isStatus = item.isStatus;

    if (!currentAiMessageDiv) {
        console.warn("No current AI message div, creating one for thought/status.");
        createAiMessageContainer();
    }
    const contentDiv = currentAiMessageDiv.querySelector('.message-content');
    let thinkingDiv = contentDiv.querySelector('.thinking-process');
    let toggleButton = contentDiv.querySelector('.toggle-thinking');
    let thinkingPlaceholder = contentDiv.querySelector('.thinking-placeholder');

    if (thinkingPlaceholder) {
        contentDiv.removeChild(thinkingPlaceholder);
        thinkingPlaceholder = null;
    }

    // Create thinking area if it doesn't exist
    if (!thinkingDiv) {
        toggleButton = document.createElement('button');
        toggleButton.classList.add('toggle-thinking');
        toggleButton.textContent = isThinkingGloballyVisible ? 'Hide thinking' : 'Show thinking';
        toggleButton.onclick = () => toggleThinking(toggleButton);
        contentDiv.insertBefore(toggleButton, contentDiv.firstChild);

        thinkingDiv = document.createElement('div');
        thinkingDiv.classList.add('thinking-process');
        if (!isThinkingGloballyVisible) {
            thinkingDiv.classList.add('hidden');
        }
        const thinkingTitle = document.createElement('h4');
        thinkingTitle.textContent = 'Thinking Process:';
        thinkingDiv.appendChild(thinkingTitle);
        currentThinkingUl = document.createElement('ul');
        thinkingDiv.appendChild(currentThinkingUl);
        contentDiv.insertBefore(thinkingDiv, toggleButton.nextSibling);
    }

    const li = document.createElement('li');
    li.classList.add('thought-item');
    if (isStatus) {
        li.style.fontStyle = 'italic';
        li.style.color = '#555';
        li.style.listStyle = 'none';
        li.style.paddingLeft = '5px';
    }
    li.textContent = text;

    if (currentThinkingUl) {
        currentThinkingUl.appendChild(li);
        if (isThinkingGloballyVisible) {
             scrollToBottom();
        }
        requestAnimationFrame(() => {
            li.classList.add('visible');
        });
    } else {
        console.error("Could not find thinking UL to append thought/status.");
    }

    setTimeout(() => {
        isProcessingQueue = false;
        processThoughtQueue();
    }, interThoughtDelay);
}

function addFinalResponseToCurrentMessage(aiMessageText, citationsMap) {
     if (!currentAiMessageDiv) {
        console.error("Trying to add final response but no current AI message container exists.");
        createAiMessageContainer();
    }
    const contentDiv = currentAiMessageDiv.querySelector('.message-content');
    let thinkingPlaceholder = contentDiv.querySelector('.thinking-placeholder');

    if (thinkingPlaceholder) {
        contentDiv.removeChild(thinkingPlaceholder);
    }

    const responseDiv = document.createElement('div');
    responseDiv.classList.add('ai-response-text');
    aiMessageText.split('\n').forEach(paragraph => {
        if (paragraph.trim()) {
            const p = document.createElement('p');
            p.textContent = paragraph;
            responseDiv.appendChild(p);
        }
    });
    contentDiv.appendChild(responseDiv);

    if (citationsMap && Object.keys(citationsMap).length > 0) {
        const sourcesDiv = document.createElement('div');
        sourcesDiv.classList.add('sources-section');
        const sourcesTitle = document.createElement('h5');
        sourcesTitle.textContent = 'Sources:';
        sourcesDiv.appendChild(sourcesTitle);
        const sourcesList = document.createElement('ol');
        sourcesList.classList.add('sources-list');
        const sortedKeys = Object.keys(citationsMap).sort((a, b) => parseInt(a) - parseInt(b));
        sortedKeys.forEach(key => {
            const citation = citationsMap[key];
            if (citation && citation.link && citation.title) {
                const li = document.createElement('li');
                const a = document.createElement('a');
                a.href = citation.link;
                a.textContent = citation.title;
                a.target = '_blank';
                a.rel = 'noopener noreferrer';
                li.appendChild(a);
                sourcesList.appendChild(li);
            }
        });
        sourcesDiv.appendChild(sourcesList);
        contentDiv.appendChild(sourcesDiv);
    }

    const thinkingDiv = contentDiv.querySelector('.thinking-process');
    const toggleButton = contentDiv.querySelector('.toggle-thinking');
    if (thinkingDiv && toggleButton) {
        contentDiv.insertBefore(toggleButton, responseDiv);
        contentDiv.insertBefore(thinkingDiv, responseDiv);
    }

    scrollToBottom();
    currentAiMessageDiv = null;
    currentThinkingUl = null;
    thoughtQueue = [];
    isProcessingQueue = false;
}

function addErrorMessageToChat(errorMessage, elementId = null) {
    if (elementId) {
        const existingError = document.getElementById(elementId);
        if (existingError) existingError.remove();
    }
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('message', 'ai-message', 'error-message');
    if (elementId) messageDiv.id = elementId;
    const contentDiv = document.createElement('div');
    contentDiv.classList.add('message-content');
    contentDiv.textContent = `Error: ${errorMessage}`;
    messageDiv.appendChild(contentDiv);
    chatBox.appendChild(messageDiv);
    scrollToBottom();
}

// --- ADDED: Function to add system messages ---
function addSystemMessageToChat(systemMessage) {
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('message', 'system-message'); // Use a new class

    const contentDiv = document.createElement('div');
    contentDiv.classList.add('message-content');
    contentDiv.textContent = systemMessage;
    messageDiv.appendChild(contentDiv);
    chatBox.appendChild(messageDiv);
    scrollToBottom();
}
// --------------------------------------------

function toggleThinking(button) {
    isThinkingGloballyVisible = !isThinkingGloballyVisible;
    console.log("Global thinking visibility:", isThinkingGloballyVisible);

    const allToggleButtons = document.querySelectorAll('#chat-box .toggle-thinking');
    allToggleButtons.forEach(btn => {
        const contentDiv = btn.closest('.message-content');
        if (!contentDiv) return;
        const thinkingDiv = contentDiv.querySelector('.thinking-process');
        if (thinkingDiv) {
            if (isThinkingGloballyVisible) {
                thinkingDiv.classList.remove('hidden');
                btn.textContent = 'Hide thinking';
            } else {
                thinkingDiv.classList.add('hidden');
                btn.textContent = 'Show thinking';
            }
        }
    });

    if (isThinkingGloballyVisible && button) {
         const contentDiv = button.closest('.message-content');
         if (contentDiv) {
            scrollToBottom();
         }
    }
}

function updateAdminPanel(adminData) {
    adminUnderstanding.innerHTML = '';
    adminFunctions.innerHTML = '';
    adminSummarization.innerHTML = '';
    adminErrorSection.style.display = 'none';
    adminErrorMessage.textContent = '';

    // Understanding
    if (adminData.understanding_thoughts && adminData.understanding_thoughts.length > 0) {
        adminData.understanding_thoughts.forEach(thought => {
            const li = document.createElement('li');
            li.textContent = thought;
            adminUnderstanding.appendChild(li);
        });
    }

    // Function Calling
    if (adminData.function_calls_made && adminData.function_calls_made.length > 0) {
        adminData.function_calls_made.forEach(call => {
            const li = document.createElement('li');
            const callInfoDiv = document.createElement('div');
            const rawResult = call.raw_result;

            let flagsHTML = '';
            if (rawResult?.asked_for_sticky) {
                flagsHTML += `<span class="admin-flag sticky-flag">(Sticky Request)</span> `;
            }
            if (rawResult?.rejected) {
                flagsHTML += `<span class="admin-flag rejected-flag">(Rejected)</span> `;
            }

            const argsString = JSON.stringify(call.all_args || {}, null, 2);
            callInfoDiv.innerHTML = `<strong>${call.name || 'N/A'}</strong> ${flagsHTML}: ${call.query || 'N/A'}<pre>${argsString}</pre>`;

            if (rawResult?.rejected && rawResult?.rejection_reason) {
                 const reasonP = document.createElement('p');
                 reasonP.classList.add('admin-rejection-reason');
                 reasonP.textContent = `Reason: ${rawResult.rejection_reason}`;
                 callInfoDiv.appendChild(reasonP);
            }

            li.appendChild(callInfoDiv);

            if (rawResult !== undefined && rawResult !== null) {
                const details = document.createElement('details');
                details.classList.add('admin-raw-result');
                const summary = document.createElement('summary');
                summary.textContent = 'Show Raw Result / Details';
                details.appendChild(summary);
                const resultPre = document.createElement('pre');
                resultPre.textContent = JSON.stringify(rawResult, null, 2);
                details.appendChild(resultPre);
                li.appendChild(details);
            } else {
                 const pendingSpan = document.createElement('span');
                 pendingSpan.classList.add('admin-pending-result');
                 pendingSpan.textContent = ' (Result pending...)';
                 callInfoDiv.appendChild(pendingSpan);
            }
            adminFunctions.appendChild(li);
        });
    }

    // Summarization
    if (adminData.summarization_thoughts && adminData.summarization_thoughts.length > 0) {
        adminData.summarization_thoughts.forEach(thought => {
            const li = document.createElement('li');
            li.textContent = thought;
            adminSummarization.appendChild(li);
        });
    }

     // Error
    if (adminData.error) {
        adminErrorMessage.textContent = adminData.error;
        adminErrorSection.style.display = 'block';
    }
}

function scrollToBottom() {
    setTimeout(() => {
        chatBox.scrollTop = chatBox.scrollHeight;
    }, 50);
}


// --- WebSocket Message Handler (MODIFIED for system_message) ---
function handleWebSocketMessage(data) {
    switch (data.type) {
        case 'thought':
            queueThoughtOrStatusForAnimation(data.data, false);
            break;
        case 'status':
             queueThoughtOrStatusForAnimation(data.data, true);
            break;
        case 'admin_update':
            updateAdminPanel(data.data);
            break;
        case 'final_response':
            addFinalResponseToCurrentMessage(data.data.ai_message, data.data.citations);
            userInput.disabled = false;
            sendButton.disabled = false;
            userInput.focus();
            break;
        case 'error':
            console.error("Received error from server:", data.data);
            addErrorMessageToChat(data.data);
            userInput.disabled = false;
            sendButton.disabled = false;
            userInput.focus();
            currentAiMessageDiv = null;
            currentThinkingUl = null;
            thoughtQueue = [];
            isProcessingQueue = false;
            break;
        // --- ADDED: Handle System Messages (like reset confirmation) ---
        case 'system_message':
            console.log("Received system message:", data.data);
            addSystemMessageToChat(data.data);
            break;
        // -------------------------------------------------------------
        default:
            console.warn("Received unknown message type:", data.type);
    }
}

// --- Event Listeners ---
chatForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const message = userInput.value.trim();
    if (!message || !websocket || websocket.readyState !== WebSocket.OPEN) {
        console.log("WebSocket not open or message empty");
        return;
    }

    addUserMessage(message);
    userInput.value = '';
    userInput.disabled = true;
    sendButton.disabled = true;
    resetButton.disabled = true; // Disable reset during processing

    currentAiMessageDiv = null;
    currentThinkingUl = null;
    thoughtQueue = [];
    isProcessingQueue = false;

    createAiMessageContainer();

    updateAdminPanel({ // Reset admin panel visually immediately
        understanding_thoughts: [],
        function_calls_made: [],
        summarization_thoughts: [],
        error: null
    });

    websocket.send(JSON.stringify({ message: message })); // Send user query
});

// --- ADDED: Reset Button Listener ---
resetButton.addEventListener('click', () => {
    if (websocket && websocket.readyState === WebSocket.OPEN) {
        console.log("Sending reset request...");
        // Clear the chat box immediately for visual feedback
        chatBox.innerHTML = '';
        // Add back initial welcome message? Optional.
        // addSystemMessageToChat("Hello! How can I help you with QuickBooks today?"); // Or wait for server confirmation

        // Clear admin panel immediately
         updateAdminPanel({
            understanding_thoughts: [],
            function_calls_made: [],
            summarization_thoughts: [],
            error: null
        });

        // Send the reset command
        websocket.send(JSON.stringify({ type: "reset" }));

        // Re-enable input after sending reset (optional, user might type immediately)
        // userInput.disabled = false;
        // sendButton.disabled = false;
        // resetButton.disabled = false; // Re-enable reset button
        // userInput.focus();

    } else {
        console.error("Cannot reset: WebSocket is not open.");
        addErrorMessageToChat("Cannot reset chat. Connection is closed.");
    }
});
// ---------------------------------


// --- Initialize ---
connectWebSocket(); // Connect on page load
resetButton.disabled = true; // Start disabled until WS connects
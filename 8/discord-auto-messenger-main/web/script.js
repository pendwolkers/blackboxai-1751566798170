// Store state in memory
let isMessaging = false;
let lastStatusMessages = [];
let selectedChannels = {};  // {channel_id: {server_name, channel_name}}

// Load configuration on page load
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM Content Loaded');
    loadConfig();
    loadMessages();
    
    // Add click event listener to the Add Channel button
    const addButton = document.getElementById('addChannelBtn');
    if (addButton) {
        console.log('Add Channel button found');
        addButton.addEventListener('click', (e) => {
            e.preventDefault();
            console.log('Add Channel button clicked');
            addChannel();
        });
    } else {
        console.error('Add Channel button not found');
    }
});

function refreshChannels() {
    const token = document.getElementById('token').value.trim();
    if (!token) {
        logStatus('Error: Please enter Discord token first');
        return;
    }

    logStatus('Fetching channels...');
    fetch('/refresh-channels', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ token })
    })
    .then(response => response.json())
    .then(data => {
        if (!data.success) {
            throw new Error(data.error || 'Failed to fetch channels');
        }

        const serverTree = document.getElementById('serverTree');
        serverTree.innerHTML = '';

        // Sort servers by name
        data.servers.sort((a, b) => a.name.localeCompare(b.name));

        data.servers.forEach(server => {
            const serverDiv = document.createElement('div');
            serverDiv.className = 'mb-4';
            
            // Server header
            const serverHeader = document.createElement('div');
            serverHeader.className = 'font-semibold text-gray-800 mb-2';
            serverHeader.textContent = server.name;
            serverDiv.appendChild(serverHeader);

            // Channel list
            const channelList = document.createElement('div');
            channelList.className = 'ml-4 space-y-1';

            // Sort channels by name
            server.channels.sort((a, b) => a.name.localeCompare(b.name));

            server.channels.forEach(channel => {
                const channelDiv = document.createElement('div');
                channelDiv.className = 'flex items-center space-x-2';

                const checkbox = document.createElement('input');
                checkbox.type = 'checkbox';
                checkbox.className = 'form-checkbox h-4 w-4 text-blue-500';
                checkbox.checked = selectedChannels.hasOwnProperty(channel.id);
                checkbox.addEventListener('change', () => toggleChannel(channel.id, server.name, channel.name));

                const label = document.createElement('label');
                label.className = 'text-sm text-gray-700';
                label.textContent = `#${channel.name}`;

                channelDiv.appendChild(checkbox);
                channelDiv.appendChild(label);
                channelList.appendChild(channelDiv);
            });

            serverDiv.appendChild(channelList);
            serverTree.appendChild(serverDiv);
        });

        logStatus('✅ Successfully fetched channels');
    })
    .catch(error => {
        logStatus('❌ ' + error.message);
    });
}

function toggleChannel(channelId, serverName, channelName) {
    if (selectedChannels[channelId]) {
        delete selectedChannels[channelId];
        logStatus(`Unselected #${channelName} from ${serverName}`);
    } else {
        selectedChannels[channelId] = {
            server_name: serverName,
            channel_name: channelName
        };
        logStatus(`Selected #${channelName} from ${serverName}`);
    }
}

function logStatus(message) {
    const statusLog = document.getElementById('statusLog');
    const timestamp = new Date().toLocaleString();
    const formattedMessage = `[${timestamp}] ${message}`;
    
    const messageDiv = document.createElement('div');
    messageDiv.textContent = formattedMessage;
    statusLog.appendChild(messageDiv);
    statusLog.scrollTop = statusLog.scrollHeight;
}

function addServerStatusMessage(message) {
    const statusLog = document.getElementById('statusLog');
    const messageDiv = document.createElement('div');
    messageDiv.textContent = message;
    statusLog.appendChild(messageDiv);
    statusLog.scrollTop = statusLog.scrollHeight;
}

function verifyToken() {
    const token = document.getElementById('token').value.trim();
    if (!token) {
        logStatus('Error: Please enter a Discord token');
        return;
    }

    logStatus('Verifying token...');
    fetch('/verify-token', {
        method: 'POST',
        headers: {
            'Content-Type': 'text/plain',
        },
        body: token
    })
    .then(response => {
        if (response.ok) {
            logStatus('✅ Token verification successful!');
        } else {
            logStatus('❌ Invalid token. Please check and try again.');
        }
    })
    .catch(error => {
        logStatus('Error verifying token: ' + error);
    });
}

function saveConfig() {
    const config = {
        token: document.getElementById('token').value,
        channels: Object.keys(selectedChannels)
    };

    // Save to info.txt
    const configText = `${config.token}\n${config.channels.join('\n')}`;
    
    fetch('/save-config', {
        method: 'POST',
        headers: {
            'Content-Type': 'text/plain',
        },
        body: configText
    })
    .then(response => {
        if (response.ok) {
            logStatus('Configuration saved successfully');
        } else {
            logStatus('Error saving configuration');
        }
    })
    .catch(error => {
        logStatus('Error saving configuration: ' + error);
    });
}

function loadConfig() {
    fetch('/load-config')
    .then(response => response.text())
    .then(data => {
        const lines = data.split('\n');
        if (lines.length >= 1) {
            document.getElementById('token').value = lines[0];
            channels = lines.slice(1).filter(line => line.trim());
            updateChannelList();
            logStatus('Configuration loaded successfully');
        }
    })
    .catch(error => {
        logStatus('Error loading configuration: ' + error);
    });
}

// Load messages from messages.txt
function loadMessages() {
    fetch('/load-messages')
    .then(response => response.text())
    .then(data => {
        document.getElementById('messages').value = data;
        logStatus('Messages loaded successfully');
    })
    .catch(error => {
        logStatus('Error loading messages: ' + error);
    });
}

// Save messages to messages.txt
function saveMessages() {
    const messages = document.getElementById('messages').value;
    
    fetch('/save-messages', {
        method: 'POST',
        headers: {
            'Content-Type': 'text/plain',
        },
        body: messages
    })
    .then(response => {
        if (response.ok) {
            logStatus('Messages saved successfully');
        } else {
            logStatus('Error saving messages');
        }
    })
    .catch(error => {
        logStatus('Error saving messages: ' + error);
    });
}

function startMessaging() {
    const config = {
        token: document.getElementById('token').value,
        channels: channels,
        loopCount: parseInt(document.getElementById('loopCount').value),
        loopDelay: parseInt(document.getElementById('loopDelay').value),
        sleepTime: parseInt(document.getElementById('sleepTime').value)
    };

    if (!config.token || channels.length === 0) {
        logStatus('Error: Please enter Discord token and add at least one channel');
        return;
    }

    isMessaging = true;
    lastStatusMessages = []; // Reset status messages tracking
    document.getElementById('startBtn').disabled = true;
    document.getElementById('startBtn').classList.add('opacity-50', 'cursor-not-allowed');
    document.getElementById('stopBtn').disabled = false;
    document.getElementById('stopBtn').classList.remove('opacity-50', 'cursor-not-allowed');

    fetch('/start-messaging', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(config)
    })
    .then(response => {
        if (response.ok) {
            logStatus('Started messaging process');
            // Start polling for status updates
            pollMessagingStatus();
        } else {
            logStatus('Error starting messaging process');
            stopMessaging();
        }
    })
    .catch(error => {
        logStatus('Error: ' + error);
        stopMessaging();
    });
}

function stopMessaging() {
    isMessaging = false;
    document.getElementById('stopBtn').disabled = true;
    document.getElementById('stopBtn').classList.add('opacity-50', 'cursor-not-allowed');
    document.getElementById('startBtn').disabled = false;
    document.getElementById('startBtn').classList.remove('opacity-50', 'cursor-not-allowed');

    fetch('/stop-messaging', {
        method: 'POST'
    })
    .then(response => {
        if (response.ok) {
            logStatus('Messaging process stopped');
        } else {
            logStatus('Error stopping messaging process');
        }
    })
    .catch(error => {
        logStatus('Error: ' + error);
    });
}

function pollMessagingStatus() {
    if (!isMessaging) return;

    fetch('/messaging-status')
    .then(response => response.json())
    .then(data => {
        // Update status log with new messages from server
        if (data.messages && data.messages.length > 0) {
            data.messages.forEach(message => {
                // Only add new messages that we haven't seen before
                if (!lastStatusMessages.includes(message)) {
                    addServerStatusMessage(message);
                    lastStatusMessages.push(message);
                }
            });
        }

        if (data.status === 'completed') {
            logStatus('✅ Message sending process completed!');
            stopMessaging();
        } else if (data.status === 'stopped') {
            logStatus('🛑 Message sending process stopped by user');
            stopMessaging();
        } else if (data.status === 'error') {
            logStatus('❌ Error in messaging process: ' + data.error);
            stopMessaging();
        } else {
            // Continue polling if still running
            setTimeout(pollMessagingStatus, 1000);
        }
    })
    .catch(error => {
        logStatus('Error checking status: ' + error);
        stopMessaging();
    });
}

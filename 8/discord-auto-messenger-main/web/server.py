from flask import Flask, request, send_from_directory, jsonify
import json
import time
from datetime import datetime
from http.client import HTTPSConnection
import threading
import os

app = Flask(__name__)

INFO_FILE = "../info.txt"
MESSAGES_FILE = "../messages.txt"

# Global variables for message status
messaging_thread = None
is_messaging = False
messaging_status = {"status": "idle"}
status_messages = []

def get_timestamp():
    return "[" + str(datetime.now().strftime("%Y-%m-%d %H:%M:%S")) + "]"

def add_status_message(message):
    global status_messages
    timestamp = get_timestamp()
    status_message = f"{timestamp} {message}"
    status_messages.append(status_message)
    print(status_message)
    # Keep only last 100 messages to prevent memory issues
    if len(status_messages) > 100:
        status_messages = status_messages[-100:]

def send_message(conn, channel_id, message_data, header_data, channel_name, server_name):
    try:
        conn.request("POST", f"/api/v9/channels/{channel_id}/messages", message_data, header_data)
        resp = conn.getresponse()
        if 199 < resp.status < 300:
            success_msg = f'Message sent to #{channel_name} in {server_name}!'
            return True, success_msg
        else:
            error_msg = f'Failed to send message to #{channel_name}: HTTP {resp.status}'
            return False, error_msg
    except Exception as e:
        error_msg = f'Error sending message to #{channel_name}: {str(e)}'
        return False, error_msg

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/script.js')
def script():
    return send_from_directory('.', 'script.js')

@app.route('/save-config', methods=['POST'])
def save_config():
    try:
        config_text = request.data.decode('utf-8')
        with open(INFO_FILE, 'w') as f:
            f.write(config_text)
        add_status_message("Configuration saved successfully")
        return jsonify({"success": True})
    except Exception as e:
        add_status_message(f"Error saving configuration: {str(e)}")
        return jsonify({"success": False, "error": str(e)})

@app.route('/load-config')
def load_config():
    try:
        with open(INFO_FILE, 'r') as f:
            return f.read()
    except FileNotFoundError:
        return ''

@app.route('/save-messages', methods=['POST'])
def save_messages():
    try:
        messages = request.data.decode('utf-8')
        with open(MESSAGES_FILE, 'w') as f:
            f.write(messages)
        add_status_message("Messages saved successfully")
        return jsonify({"success": True})
    except Exception as e:
        add_status_message(f"Error saving messages: {str(e)}")
        return jsonify({"success": False, "error": str(e)})

@app.route('/load-messages')
def load_messages():
    try:
        with open(MESSAGES_FILE, 'r') as f:
            return f.read()
    except FileNotFoundError:
        return ''

@app.route('/get-status-messages')
def get_status_messages():
    return jsonify({"messages": status_messages})

def message_sender(config):
    global is_messaging, messaging_status
    conn = None
    
    try:
        is_messaging = True
        messaging_status = {"status": "running"}
        add_status_message("Starting messaging process...")
        
        # Read messages
        with open(MESSAGES_FILE, "r") as file:
            messages = file.read().splitlines()
            
        if not messages:
            messaging_status = {"status": "error", "error": "No messages found in messages.txt"}
            add_status_message("Error: No messages found in messages.txt")
            return

        # Get channel info from server
        conn = HTTPSConnection("discord.com", 443)
        headers = {
            "authorization": config['token'],
            "content-type": "application/json"
        }
        
        # Get channel names
        channel_info = {}
        for channel_id in config['channels']:
            conn.request("GET", f"/api/v9/channels/{channel_id}", headers=headers)
            resp = conn.getresponse()
            if resp.status == 200:
                channel_data = json.loads(resp.read())
                channel_info[channel_id] = {
                    'name': channel_data['name'],
                    'guild_id': channel_data['guild_id']
                }
                
                # Get server name
                conn.request("GET", f"/api/v9/guilds/{channel_data['guild_id']}", headers=headers)
                resp = conn.getresponse()
                if resp.status == 200:
                    guild_data = json.loads(resp.read())
                    channel_info[channel_id]['guild_name'] = guild_data['name']

        add_status_message(f"Loaded {len(messages)} messages from messages.txt")
        add_status_message(f"Will send to {len(config['channels'])} channels for {config['loopCount']} loops")

        for i in range(config['loopCount']):
            if not is_messaging:
                messaging_status = {"status": "stopped"}
                add_status_message("Messaging process stopped by user")
                return

            add_status_message(f"Starting loop {i + 1}/{config['loopCount']}")

            for message_index, message in enumerate(messages):
                if not is_messaging:
                    messaging_status = {"status": "stopped"}
                    return

                message_data = json.dumps({"content": message})
                add_status_message(f"Sending message {message_index + 1}/{len(messages)}: \"{message}\"")
                
                for channel_id in config['channels']:
                    if not is_messaging:
                        messaging_status = {"status": "stopped"}
                        return

                    header_data = {
                        "content-type": "application/json",
                        "authorization": config['token'],
                        "host": "discord.com"
                    }
                    
                    channel_name = channel_info.get(channel_id, {}).get('name', 'unknown-channel')
                    server_name = channel_info.get(channel_id, {}).get('guild_name', 'Unknown Server')
                    
                    conn = HTTPSConnection("discord.com", 443)
                    success, msg = send_message(conn, channel_id, message_data, header_data, channel_name, server_name)
                    conn.close()
                    
                    if success:
                        add_status_message(f"✅ Successfully sent to #{channel_name} in {server_name}")
                    else:
                        add_status_message(f"❌ Failed to send to #{channel_name} in {server_name}: {msg}")
                    
                    time.sleep(config['sleepTime'])

            add_status_message(f"Completed loop {i + 1}/{config['loopCount']}")
            if i < config['loopCount'] - 1 and is_messaging:
                add_status_message(f"Waiting {config['loopDelay']} seconds before next loop...")
                time.sleep(config['loopDelay'])

        if is_messaging:
            messaging_status = {"status": "completed"}
            add_status_message("🎉 All messages have been sent successfully!")

    except Exception as e:
        error_msg = f"Error in message sender: {str(e)}"
        add_status_message(f"❌ {error_msg}")
        messaging_status = {"status": "error", "error": str(e)}
    finally:
        if conn:
            conn.close()

@app.route('/refresh-channels', methods=['POST'])
def refresh_channels():
    try:
        token = request.json.get('token')
        if not token:
            return jsonify({"success": False, "error": "Token is required"})
            
        # Get user guilds (servers)
        conn = HTTPSConnection("discord.com", 443)
        headers = {
            "authorization": token,
            "content-type": "application/json"
        }
        
        # Get servers
        conn.request("GET", "/api/v9/users/@me/guilds", headers=headers)
        resp = conn.getresponse()
        if resp.status != 200:
            return jsonify({"success": False, "error": "Failed to fetch servers"})
            
        guilds = json.loads(resp.read())
        servers = []
        
        # For each server, get channels
        for guild in guilds:
            guild_id = guild["id"]
            guild_name = guild["name"]
            
            # Get channels for this server
            conn.request("GET", f"/api/v9/guilds/{guild_id}/channels", headers=headers)
            resp = conn.getresponse()
            if resp.status != 200:
                continue
                
            channels = json.loads(resp.read())
            text_channels = [
                {"id": ch["id"], "name": ch["name"]}
                for ch in channels
                if ch["type"] == 0  # Text channel
            ]
            
            if text_channels:  # Only add servers that have text channels
                servers.append({
                    "id": guild_id,
                    "name": guild_name,
                    "channels": text_channels
                })
                
        return jsonify({
            "success": True,
            "servers": servers
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})
    finally:
        conn.close()

@app.route('/start-messaging', methods=['POST'])
def start_messaging():
    global messaging_thread, is_messaging, messaging_status, status_messages
    
    try:
        if messaging_thread and messaging_thread.is_alive():
            return jsonify({"success": False, "error": "Messaging process already running"})

        config = request.json
        is_messaging = True
        messaging_status = {"status": "running"}
        
        # Clear previous status messages when starting new session
        status_messages = []
        
        messaging_thread = threading.Thread(target=message_sender, args=(config,))
        messaging_thread.daemon = True
        messaging_thread.start()
        
        add_status_message("Messaging process started")
        return jsonify({"success": True})
    except Exception as e:
        error_msg = f"Error starting messaging process: {str(e)}"
        add_status_message(f"❌ {error_msg}")
        messaging_status = {"status": "error", "error": str(e)}
        return jsonify({"success": False, "error": str(e)})

@app.route('/stop-messaging', methods=['POST'])
def stop_messaging():
    global is_messaging, messaging_status
    is_messaging = False
    messaging_status = {"status": "stopped"}
    add_status_message("🛑 Stop messaging requested by user")
    return jsonify({"success": True})

@app.route('/messaging-status')
def get_messaging_status():
    return jsonify({
        "status": messaging_status.get("status", "idle"),
        "error": messaging_status.get("error", None),
        "messages": status_messages[-10:]  # Return last 10 status messages
    })

@app.route('/verify-token', methods=['POST'])
def verify_token():
    try:
        token = request.data.decode('utf-8')
        conn = HTTPSConnection("discord.com", 443)
        headers = {
            "authorization": token,
            "content-type": "application/json"
        }
        conn.request("GET", "/api/v9/users/@me", headers=headers)
        response = conn.getresponse()
        
        if response.status == 200:
            add_status_message("Token verification successful")
            return jsonify({"success": True}), 200
        else:
            add_status_message("Token verification failed")
            return jsonify({"success": False}), 401
            
    except Exception as e:
        error_msg = f"Error verifying token: {str(e)}"
        add_status_message(error_msg)
        return jsonify({"success": False, "error": error_msg}), 500
    finally:
        conn.close()

if __name__ == '__main__':
    # Ensure we're in the correct directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    app.run(host='0.0.0.0', port=8000)

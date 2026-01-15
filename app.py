from flask import Flask, render_template_string
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'sin_php_2024'
socketio = SocketIO(app)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Chat @sin_php</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700&display=swap" rel="stylesheet">
    <style>
        * { box-sizing: border-box; font-family: 'Tajawal', sans-serif; }
        body { background: #e5ddd5; margin: 0; display: flex; flex-direction: column; height: 100vh; }
        header { background: #075e54; color: white; padding: 15px; text-align: center; box-shadow: 0 2px 5px rgba(0,0,0,0.2); z-index: 10; }
        .rights { float: left; font-size: 0.8em; color: #25d366; font-weight: bold; }
        #chat-window { flex: 1; overflow-y: auto; padding: 20px; display: flex; flex-direction: column; gap: 8px; background-image: url('https://user-images.githubusercontent.com/15075759/28719144-86dc0f70-73b1-11e7-911d-60d70fcded21.png'); }
        .message { max-width: 75%; padding: 8px 12px; border-radius: 10px; font-size: 14px; position: relative; box-shadow: 0 1px 1px rgba(0,0,0,0.1); }
        .received { background: white; align-self: flex-start; border-top-right-radius: 0; }
        .sent { background: #dcf8c6; align-self: flex-end; border-top-left-radius: 0; }
        .user-name { font-weight: bold; display: block; font-size: 0.8em; margin-bottom: 4px; color: #075e54; }
        .input-area { background: #f0f0f0; padding: 10px; display: flex; gap: 8px; align-items: center; }
        input[type="text"] { border: none; padding: 12px; border-radius: 20px; outline: none; font-size: 14px; }
        #username { width: 100px; background: #fff; }
        #msg { flex: 1; background: #fff; }
        button { background: #075e54; color: white; border: none; width: 45px; height: 45px; border-radius: 50%; cursor: pointer; display: flex; align-items: center; justify-content: center; transition: 0.3s; }
        button:hover { background: #128c7e; transform: scale(1.05); }
    </style>
</head>
<body>

<header>
    <span class="rights">@sin_php</span>
    <strong>dev web </strong>
</header>

<div id="chat-window"></div>

<div class="input-area">
    <input type="text" id="username" placeholder="name">
    <input type="text" id="msg" placeholder="massage " autocomplete="off">
    <button onclick="sendMessage()">➤</button>
</div>

<script>
    const socket = io();
    const chatWindow = document.getElementById('chat-window');
    const usernameInput = document.getElementById('username');
    const messageInput = document.getElementById('msg');

    socket.on('message', function(data) {
        const div = document.createElement('div');
        const isMyMsg = data.user === usernameInput.value && usernameInput.value !== "";
        div.className = `message ${isMyMsg ? 'sent' : 'received'}`;
        div.innerHTML = `<span class="user-name">${data.user}</span>${data.msg}`;
        chatWindow.appendChild(div);
        chatWindow.scrollTop = chatWindow.scrollHeight;
    });

    function sendMessage() {
        const user = usernameInput.value.trim() || 'مجهول';
        const msg = messageInput.value.trim();
        if (msg !== "") {
            socket.emit('message', { user: user, msg: msg });
            messageInput.value = '';
        }
    }

    messageInput.addEventListener("keypress", (e) => { if (e.key === "Enter") sendMessage(); });
</script>

</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@socketio.on('message')
def handle_message(data):
    emit('message', data, broadcast=True)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
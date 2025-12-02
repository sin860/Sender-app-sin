from flask import Flask, render_template_string
from flask_socketio import SocketIO, emit

APP_NAME = "APPV1"
SECRET_KEY = '8584509611wB5GzWiL1NhopFFjXb6t25SSeeink'
DEV_HANDLE = "@SIN_PHP"

app = Flask(APP_NAME)
app.config['SECRET_KEY'] = SECRET_KEY
socketio = SocketIO(app)

CHAT_INTERFACE_TEMPLATE = f"""
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0"> 
    <title>SIN.COM</title>
    <style>
        body {{ 
            font-family: 'Tahoma', sans-serif; 
            background-color: #f0f0f0; 
            margin: 0; 
            display: flex; 
            justify-content: center; 
            align-items: center; 
            height: 100vh; 
        }}
        #chat-window {{ 
            display: flex; 
            flex-direction: column; 
            width: 100%; 
            max-width: 420px; 
            height: 100%; 
            max-height: 800px; 
            background: #e5ddd5; 
            box-shadow: 0 0 20px rgba(0,0,0,0.2); 
            border-radius: 0; 
        }}
        @media (min-width: 421px) {{
            #chat-window {{
                border-radius: 12px;
                height: 90vh;
            }}
        }}
        #messages {{ 
            list-style-type: none; 
            padding: 10px; 
            flex-grow: 1; 
            overflow-y: auto; 
            margin: 0; 
        }}
        #messages li {{ 
            padding: 8px 12px; 
            margin-bottom: 8px; 
            max-width: 80%;
            border-radius: 18px; 
            line-height: 1.4;
            word-wrap: break-word; 
            font-size: 15px;
        }}
        .message-sent {{ 
            background-color: #dcf8c6; 
            margin-left: auto; 
        }}
        .message-received {{ 
            background-color: #ffffff; 
            margin-right: auto; 
            box-shadow: 0 1px 0.5px rgba(0,0,0,0.1);
        }}
        #input-area {{ 
            display: flex; 
            padding: 8px; 
            background-color: #f0f0f0; 
            align-items: center;
        }}
        #message_input {{ 
            flex-grow: 1; 
            padding: 10px 15px; 
            border: 1px solid #ccc;
            border-radius: 20px; 
            margin: 0 8px;
            font-size: 16px;
        }}
        #input-area button {{ 
            padding: 10px; 
            background-color: #075e54; 
            color: white; 
            border: none; 
            border-radius: 50%; 
            width: 45px;
            height: 45px;
            font-size: 18px;
            cursor: pointer; 
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        #footer {{
            text-align: center;
            padding: 5px;
            font-size: 10px;
            color: #777;
            background-color: #fff;
            border-top: 1px solid #ddd;
        }}
    </style>
    <script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>
</head>
<body>
    <div id="chat-window">
        <ul id="messages"></ul>
        <div id="input-area">
            <input id="message_input" type="text" placeholder="مضرط .. " autofocus>
            <button onclick="sendMessage()">&#x27A4;</button>
        </div>
        <div id="footer">
          {DEV_HANDLE}
        </div>
    </div>

    <script>
        const socket = io();
        const USER_SESSION_ID = 'User_' + Math.floor(Math.random() * 10000); 

        socket.on('receive_message', function(data) {{
            const messages = document.getElementById('messages');
            const newItem = document.createElement('li');
            
            if (data.user_id === USER_SESSION_ID) {{
                newItem.classList.add('message-sent');
            }} else {{
                newItem.classList.add('message-received');
            }}

            newItem.textContent = data.message;
            messages.appendChild(newItem);
            
            messages.scrollTop = messages.scrollHeight;
        }});

        function sendMessage() {{
            const messageInput = document.getElementById('message_input');
            const message = messageInput.value.trim();
            
            if (message) {{
                socket.emit('send_message', {{
                    user_id: USER_SESSION_ID,
                    message: message
                }});
                
                messageInput.value = '';
                messageInput.focus();
            }}
        }}
        
        document.getElementById('message_input').addEventListener('keypress', function(e) {{
            if (e.key === 'Enter') {{
                sendMessage();
            }}
        }});
        
        window.onload = function() {{
            const messages = document.getElementById('messages');
            messages.scrollTop = messages.scrollHeight;
        }};
    </script>
</body>
</html>
"""

@app.route('/')
def home_page():
    return render_template_string(CHAT_INTERFACE_TEMPLATE)

@socketio.on('send_message')
def handle_incoming_message(data: dict):
    emit('receive_message', data, broadcast=True) 

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)

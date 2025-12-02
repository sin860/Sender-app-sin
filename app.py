import os
import requests
from flask import Flask, render_template_string, request, redirect, url_for, session
from flask_socketio import SocketIO, emit
APP_NAME = "SIN.COM"
SECRET_KEY = os.environ.get('SECRET_KEY', 'default_fallback_key_DO_NOT_USE_IN_PROD')
DEV_HANDLE = "@SIN_PHP"
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')
PORT = int(os.environ.get('PORT', 5000))

app = Flask(APP_NAME)
app.config['SECRET_KEY'] = SECRET_KEY
socketio = SocketIO(app, cors_allowed_origins="*") 

def send_to_telegram(message):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print(f"!! تنبيه: لم يتم إعداد API تيليجرام. الرسالة: {message}")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': message,
        'parse_mode': 'Markdown'
    }
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print(f"حدث خطأ في الإرسال إلى تيليجرام: {e}")

@app.route('/')
def index():
    if 'username' in session:
        return redirect(url_for('chat_page'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'username' in session:
        return redirect(url_for('chat_page'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        if username:
            session['username'] = username
            return redirect(url_for('chat_page'))
    
    FORM_TEMPLATE = """
    <!DOCTYPE html>
    <html lang="ar" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <title>تسجيل الدخول</title>
        <style>
            body { font-family: Tahoma; display: flex; justify-content: center; align-items: center; height: 100vh; background-color: #f0f0f0; }
            .container { background: white; padding: 20px; border-radius: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); text-align: center; }
            input[type="text"] { padding: 10px; margin: 10px 0; border: 1px solid #ccc; border-radius: 5px; width: 90%; }
            button { padding: 10px 20px; background-color: #075e54; color: white; border: none; border-radius: 5px; cursor: pointer; }
        </style>
    </head>
    <body>
        <div class="container">
            <h2>دخول الدردشة</h2>
            <form method="POST">
                <input type="text" name="username" placeholder="اسم المستخدم (مثل ID)" required>
                <button type="submit">دخول</button>
            </form>
        </div>
    </body>
    </html>
    """
    return render_template_string(FORM_TEMPLATE)

@app.route('/chat')
def chat_page():
    if 'username' not in session:
        return redirect(url_for('login'))
        
    CURRENT_USERNAME = session['username']
    
    CHAT_INTERFACE_TEMPLATE = f"""
    <!DOCTYPE html>
    <html lang="ar" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0"> 
        <title>الدردشة العامة</title>
        <style>
            body {{ font-family: 'Tahoma', sans-serif; background-color: #f0f0f0; margin: 0; display: flex; justify-content: center; align-items: center; height: 100vh; }}
            #chat-window {{ display: flex; flex-direction: column; width: 100%; max-width: 420px; height: 100%; max-height: 800px; background: #e5ddd5; box-shadow: 0 0 20px rgba(0,0,0,0.2); position: relative; border-radius: 0; }}
            @media (min-width: 421px) {{ #chat-window {{ border-radius: 12px; height: 90vh; }} }}
            #messages {{ list-style-type: none; padding: 10px; flex-grow: 1; overflow-y: auto; margin: 0; }}
            #messages li {{ padding: 8px 12px; margin-bottom: 8px; max-width: 80%; border-radius: 18px; line-height: 1.4; word-wrap: break-word; font-size: 15px; }}
            .message-sent {{ background-color: #dcf8c6; margin-left: auto; text-align: left; }}
            .message-received {{ background-color: #ffffff; margin-right: auto; box-shadow: 0 1px 0.5px rgba(0,0,0,0.1); text-align: right; }}
            .username {{ font-weight: bold; font-size: 12px; color: #333; display: block; margin-bottom: 4px; }}
            #header {{ background-color: #075e54; color: white; padding: 10px 15px; display: flex; justify-content: space-between; align-items: center; }}
            #menu-icon {{ font-size: 24px; cursor: pointer; padding: 0 5px; line-height: 1; transform: rotate(90deg); user-select: none; }}
            #dropdown-menu {{ position: absolute; top: 50px; right: 10px; background-color: #ffffff; box-shadow: 0px 8px 16px 0px rgba(0,0,0,0.2); z-index: 10; min-width: 220px; border-radius: 4px; display: none; }}
            #dropdown-menu a {{ color: black; padding: 12px 16px; text-decoration: none; display: block; font-size: 14px; border-bottom: 1px solid #eee; }}
            #dropdown-menu a:hover {{ background-color: #f1f1f1; }}
            #dropdown-menu p {{ padding: 12px 16px 5px; margin: 0; font-size: 12px; color: #777; }}
            #input-area {{ display: flex; padding: 8px; background-color: #f0f0f0; align-items: center; }}
            #message_input {{ flex-grow: 1; padding: 10px 15px; border: 1px solid #ccc; border-radius: 20px; margin: 0 8px; font-size: 16px; }}
            #input-area button {{ padding: 10px; background-color: #075e54; color: white; border: none; border-radius: 50%; width: 45px; height: 45px; font-size: 18px; cursor: pointer; display: flex; align-items: center; justify-content: center; }}
            #footer {{ text-align: center; padding: 5px; font-size: 10px; color: #777; background-color: #fff; border-top: 1px solid #ddd; }}
        </style>
        <script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>
    </head>
    <body>
        <div id="chat-window">
            <div id="header">
                <span>الدردشة العامة (ID: {CURRENT_USERNAME})</span>
                <div id="menu-container">
                    <span id="menu-icon" onclick="toggleMenu()">&#x22EE;</span> 
                    <div id="dropdown-menu">
                        <p>معلومات المطور</p>
                        <a href="https://t.me/SIN_PYHTON" target="_blank">قناة تليجرام: SIN</a>
                        <a href="https://t.me/SIN_PHP" target="_blank">يوزر تليجرام: {DEV_HANDLE}</a>
                        <a href="/logout">تسجيل الخروج</a>
                    </div>
                </div>
            </div>
            <ul id="messages"></ul>
            <div id="input-area">
                <input id="message_input" type="text" placeholder="اكتب رسالتك...">
                <button onclick="sendMessage()">&#x27A4;</button>
            </div>
            <div id="footer">
                حقوق المطور: {DEV_HANDLE}
            </div>
        </div>

        <script>
            const socket = io({{ transports: ['websocket', 'polling'] }});
            const CURRENT_USERNAME = "{{ CURRENT_USERNAME }}"; 
            
            function toggleMenu() {{
                const menu = document.getElementById('dropdown-menu');
                menu.style.display = menu.style.display === 'block' ? 'none' : 'block';
            }}

            socket.on('receive_message', function(data) {{
                const messages = document.getElementById('messages');
                const newItem = document.createElement('li');
                
                const usernameSpan = document.createElement('span');
                usernameSpan.classList.add('username');
                
                usernameSpan.textContent = "ID: " + data.user_identifier + ":";
                
                newItem.appendChild(usernameSpan);
                newItem.appendChild(document.createTextNode(data.message));
                
                if (data.user_identifier === CURRENT_USERNAME) {{
                    newItem.classList.remove('message-received');
                    newItem.classList.add('message-sent');
                }} else {{
                    newItem.classList.remove('message-sent');
                    newItem.classList.add('message-received');
                }}

                messages.appendChild(newItem);
                messages.scrollTop = messages.scrollHeight;
            }});

            function sendMessage() {{
                const messageInput = document.getElementById('message_input');
                const message = messageInput.value.trim();
                
                if (message && CURRENT_USERNAME) {{
                    socket.emit('send_message', {{ message: message }});
                    messageInput.value = '';
                }}
            }}
            
            document.getElementById('message_input').addEventListener('keypress', function(e) {{
                if (e.key === 'Enter') {{
                    sendMessage();
                }}
            }});

            window.onclick = function(event) {{
                if (!event.target.matches('#menu-icon')) {{
                    const dropdowns = document.getElementById("dropdown-menu");
                    if (dropdowns.style.display === 'block') {{
                        dropdowns.style.display = 'none';
                    }}
                }}
            }}
        </script>
    </body>
    </html>
    """
    return render_template_string(CHAT_INTERFACE_TEMPLATE)

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@socketio.on('send_message')
def handle_incoming_message(data: dict):
    if 'username' not in session:
        return 
        
    user_id = session['username']
    message = data.get('message')
    
    telegram_message = f"رسالة جديدة:\n*ID:* {user_id}\n*الرسالة:* {message}"
    send_to_telegram(telegram_message)
    
    data['user_identifier'] = user_id
    emit('receive_message', data, broadcast=True)

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=PORT)

from flask import Flask, render_template_string, request, redirect, url_for
from flask_socketio import SocketIO, emit
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required

APP_NAME = "Chat_App_Final"
SECRET_KEY = 'YOUR_HIGHLY_SECURE_SECRET_KEY_HERE'
DEV_HANDLE = "@SIN_PHP"
TELEGRAM_CHANNEL_NAME = "SIN"
TELEGRAM_CHANNEL_LINK = "https://t.me/SIN_PYHTON"

app = Flask(APP_NAME)
app.config['SECRET_KEY'] = SECRET_KEY
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
socketio = SocketIO(app) 
login_manager = LoginManager(app)
login_manager.login_view = 'register_login' 

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    role = db.Column(db.String(10), default='user') 

    def is_admin(self):
        return self.role == 'admin'

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id)) 

def setup_database():
    with app.app_context():
        db.create_all() 
        
        admin_user = db.session.execute(db.select(User).filter_by(username=DEV_HANDLE)).scalar_one_or_none()
        
        if not admin_user:
            admin_user = User(username=DEV_HANDLE, role='admin')
            db.session.add(admin_user)
            db.session.commit()
        elif admin_user.role != 'admin':
            admin_user.role = 'admin'
            db.session.commit()

setup_database()

@app.route('/register', methods=['GET', 'POST'])
def register_login():
    if current_user.is_authenticated:
        return redirect(url_for('home_page'))
    
    message = None
    if request.method == 'POST':
        username = request.form.get('username')
        if not username:
            message = "الرجاء إدخال اسم المستخدم."
        else:
            user = db.session.execute(db.select(User).filter_by(username=username)).scalar_one_or_none()
            
            if user:
                login_user(user)
            else:
                new_user = User(username=username, role='user')
                db.session.add(new_user)
                db.session.commit()
                login_user(new_user)
            
            return redirect(url_for('home_page'))
    
    form_template = f"""
    <!DOCTYPE html>
    <html lang="ar" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <title>تسجيل/دخول</title>
        <style>
            body {{ font-family: Tahoma; display: flex; justify-content: center; align-items: center; height: 100vh; background-color: #f0f0f0; }}
            .container {{ background: white; padding: 20px; border-radius: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); text-align: center; }}
            input[type="text"] {{ padding: 10px; margin: 10px 0; border: 1px solid #ccc; border-radius: 5px; width: 90%; }}
            button {{ padding: 10px 20px; background-color: #075e54; color: white; border: none; border-radius: 5px; cursor: pointer; }}
            .error {{ color: red; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h2>تسجيل الدخول / إنشاء حساب</h2>
            <p class="error">{message or ''}</p>
            <form method="POST">
                <input type="text" name="username" placeholder="اسم المستخدم" required>
                <button type="submit">دخول الدردشة</button>
                <p style="font-size: 12px; color: #777;">* إذا كان الاسم موجوداً سيتم تسجيل الدخول، وإلا سيتم إنشاء حساب جديد.</p>
            </form>
        </div>
    </body>
    </html>
    """
    return form_template

@app.route('/admin/users')
@login_required 
def admin_users():
    if not current_user.is_admin():
        return "غير مصرح لك برؤية هذه الصفحة.", 403

    all_users = db.session.execute(db.select(User)).scalars().all()
    
    users_list_html = "<ul>"
    for user in all_users:
        users_list_html += f"<li>ID: {user.id} | اليوزر: {user.username} | الدور: {user.role}</li>"
    users_list_html += "</ul>"

    admin_page_template = f"""
    <!DOCTYPE html>
    <html lang="ar" dir="rtl">
    <head>
        <title>قاعدة بيانات المستخدمين (للمالك فقط)</title>
        <style>
            body {{ font-family: Tahoma; padding: 20px; }}
            h1 {{ color: #075e54; }}
        </style>
    </head>
    <body>
        <h1>قاعدة بيانات مستخدمي الدردشة</h1>
        <p>مرحباً بك يا مالك الموقع (@{DEV_HANDLE}).</p>
        <hr>
        {users_list_html}
        <p><a href="/">العودة للدردشة</a></p>
    </body>
    </html>
    """
    return admin_page_template

@app.route('/')
@login_required 
def home_page():
    return render_template_string(CHAT_INTERFACE_TEMPLATE, 
                                  current_user_id=current_user.id,
                                  is_admin=current_user.is_admin(),
                                  admin_handle=DEV_HANDLE)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('register_login'))

@socketio.on('connect')
def handle_connect():
    if not current_user.is_authenticated:
        return False 

@socketio.on('send_message')
def handle_incoming_message(data: dict):
    data['user_identifier'] = current_user.id
    data['is_admin'] = current_user.is_admin()
    
    emit('receive_message', data, broadcast=True)

CHAT_INTERFACE_TEMPLATE = f"""
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0"> 
    <title>الدردشة الخاصة</title>
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
            position: relative;
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
            text-align: left;
        }}
        .message-received {{ 
            background-color: #ffffff; 
            margin-right: auto; 
            box-shadow: 0 1px 0.5px rgba(0,0,0,0.1);
            text-align: right;
        }}
        .username {{
            font-weight: bold;
            font-size: 12px;
            color: #333;
            display: block;
            margin-bottom: 4px;
        }}
        .admin-message {{
            background-color: #25d366 !important;
            color: white;
        }}
        .admin-message .username {{
            color: #ccc; 
        }}

        #header {{
            background-color: #075e54;
            color: white;
            padding: 10px 15px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        #menu-icon {{
            font-size: 24px;
            cursor: pointer;
            padding: 0 5px;
            line-height: 1;
            transform: rotate(90deg);
            user-select: none;
        }}
        #dropdown-menu {{
            position: absolute;
            top: 50px; 
            right: 10px; 
            background-color: #ffffff;
            box-shadow: 0px 8px 16px 0px rgba(0,0,0,0.2);
            z-index: 10;
            min-width: 220px;
            border-radius: 4px;
            display: none; 
        }}
        #dropdown-menu a {{
            color: black;
            padding: 12px 16px;
            text-decoration: none;
            display: block;
            font-size: 14px;
            border-bottom: 1px solid #eee;
        }}
        #dropdown-menu a:hover {{
            background-color: #f1f1f1;
        }}
        #dropdown-menu p {{
            padding: 12px 16px 5px;
            margin: 0;
            font-size: 12px;
            color: #777;
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
        
        <div id="header">
            <span>الدردشة العامة (ID: {{ current_user_id }})</span>
            
            <div id="menu-container">
                <span id="menu-icon" onclick="toggleMenu()">&#x22EE;</span> 
                
                <div id="dropdown-menu">
                    <p>معلومات المطور</p>
                    
                    {{% if is_admin %}}
                    <a href="/admin/users" style="color: red;">عرض قاعدة البيانات (للمالك فقط)</a>
                    {{% endif %}}
                    
                    <a href="{TELEGRAM_CHANNEL_LINK}" target="_blank">قناة تليجرام: {TELEGRAM_CHANNEL_NAME}</a>
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
        const socket = io();
        const CURRENT_USER_ID = "{{ current_user_id }}"; 
        
        function toggleMenu() {{
            const menu = document.getElementById('dropdown-menu');
            if (menu.style.display === 'block') {{
                menu.style.display = 'none';
            }} else {{
                menu.style.display = 'block';
            }}
        }}

        socket.on('receive_message', function(data) {{
            const messages = document.getElementById('messages');
            const newItem = document.createElement('li');
            
            const usernameSpan = document.createElement('span');
            usernameSpan.classList.add('username');
            
            usernameSpan.textContent = "ID: " + data.user_identifier + (data.is_admin ? ' (مالك):' : ':');
            
            newItem.appendChild(usernameSpan);
            newItem.appendChild(document.createTextNode(data.message));
            
            if (data.user_identifier.toString() === CURRENT_USER_ID.toString()) {{
                newItem.classList.remove('message-received');
                newItem.classList.add('message-sent');
            }} else {{
                newItem.classList.remove('message-sent');
                newItem.classList.add('message-received');
            }}
            
            if (data.is_admin) {{
                newItem.classList.add('admin-message');
            }}


            messages.appendChild(newItem);
            messages.scrollTop = messages.scrollHeight;
        }});

        function sendMessage() {{
            const messageInput = document.getElementById('message_input');
            const message = messageInput.value.trim();
            
            if (message && CURRENT_USER_ID) {{
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

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)

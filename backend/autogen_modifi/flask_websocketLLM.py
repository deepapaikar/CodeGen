import sys
sys.path.append('/home/xin/semantic_SEARCH/autogen/autogen_fix_websocket/CodeGen_Backend/backend/autogen_modifi')
# app.py
from flask import Flask, request, render_template
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_login import current_user, login_user, logout_user, login_required
import autogen, re
from flask_cors import CORS
from groupchat_flask import groupchat_a

app = Flask(__name__)
CORS(app, supports_credentials=True)

# ---------------- gpt config
# The default config list in notebook.
config_list = [
    {
        "model": "mistral-7b",
        "base_url": "https://trout-bloggers-sporting-fbi.trycloudflare.com/v1",
        'api_key': "NULL"

    }]

config_list_gpt4 = {
    "cache_seed": 42,  # change the cache_seed for different trials
    "temperature": 0,
    "config_list": config_list,
    "timeout": 120,
}

socketio = SocketIO(app, cors_allowed_origins='*')
@app.route('/')
def index():
    return render_template('frontend_runchat.html')

pattern = re.compile(r"You: (.+?)\nAgent: (.+?)(?=You:|$)", re.DOTALL)

user_proxys = {}
assistants = {}

@socketio.on('connect')
def handle_connect():
    join_room(request.sid)
    user_proxys[request.sid], assistants[request.sid] = groupchat_a(config_list_gpt4,request.sid)
    print('connect', request.sid)

# SocketIO event for updating LLM base URL
@socketio.on('update_LLM_base_url')
def handle_update_LLM_baseUrl(message):
    new_base_url = message['base_url']
    # Here we update the first configuration's API key
    config_list[0]['base_url'] = new_base_url
    print('LLM base url updated:', config_list[0]['base_url'])
    # Add any other logic you need after updating the key


@socketio.on('message')
def handle_message(message):
    print('receive message', message)
    try:
        user_input = message.get('content')
        user_proxy = user_proxys[request.sid]
        user_proxy.initiate_chat(assistants[request.sid], message=user_input)
        print(assistants[request.sid].groupchat.messages)
        dialogue = user_proxy.get_stored_output()  # save dialogue for differenet user in dialogue
        matches = pattern.findall(dialogue)
        dialogue = [{"you": match[0], "agent": match[1]} for match in matches]
    except Exception as e:
        response = {"error": str(e)}

if __name__ == '__main__':
    socketio.run(app, debug=True,port=5002)

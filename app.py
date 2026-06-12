from flask import Flask, jsonify
from flask_socketio import SocketIO, emit
from google import genai
from google.genai import types
from dotenv import load_dotenv
import os

load_dotenv()

MODELO = "gemini-3.1-flash-lite"
instrucoes = "Você é um assistente virtual amigável. Responda de forma concisa e objetiva."

client = genai.Client(api_key=os.getenv("GENAI_KEY"))
app = Flask(__name__)
# O CORS agora aponta para o seu domínio da Vercel
socketio = SocketIO(app, cors_allowed_origins="https://teste-chatbot-cwvi.vercel.app")

active_chats = {}

def get_chat_session(session_id):
    if session_id not in active_chats:
        chat_session = client.chats.create(
            model=MODELO,
            config=types.GenerateContentConfig(system_instruction=instrucoes)
        )
        active_chats[session_id] = chat_session
    return active_chats[session_id]

@socketio.on('enviar_mensagem')
def handle_enviar_mensagem(data):
    session_id = data.get("session_id")
    mensagem_usuario = data.get("mensagem")
    
    if not session_id or not mensagem_usuario:
        emit('erro', {"erro": "Dados inválidos."})
        return

    try:
        user_chat = get_chat_session(session_id)
        resposta = user_chat.send_message(mensagem_usuario)
        texto = resposta.text if hasattr(resposta, 'text') else resposta.candidates[0].content.parts[0].text
        
        emit('nova_mensagem', {"remetente": "bot", "texto": texto})
    except Exception as e:
        emit('erro', {"erro": str(e)})

if __name__ == "__main__":
    socketio.run(app, port=6500)

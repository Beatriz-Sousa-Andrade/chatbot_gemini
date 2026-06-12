from flask import Flask, jsonify
from flask_socketio import SocketIO, emit
from google import genai
from google.genai import types
from dotenv import load_dotenv
import os

load_dotenv()

# Mantendo o modelo que a API suporta com segurança
MODELO = "gemini-3.5-flash" 

instrucoes = """Você é um especialista em ocultismo da Ordem Paranormal. 
Seu tom é misterioso, sério e técnico. Responda como se estivesse analisando um Caso Paranormal."""

app = Flask(__name__)
# O '*' em cors_allowed_origins é o que resolve o erro de CORS de vez
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

client = genai.Client(api_key=os.getenv("GENAI_KEY"))
active_chats = {}

@app.route('/')
def index():
    return "Servidor Rodando"

@socketio.on('enviar_mensagem')
def handle_message(data):
    session_id = data.get("session_id")
    msg = data.get("mensagem")
    
    if session_id not in active_chats:
        active_chats[session_id] = client.chats.create(
            model=MODELO, 
            config=types.GenerateContentConfig(system_instruction=instrucoes)
        )
    
    try:
        response = active_chats[session_id].send_message(msg)
        texto = response.text
        emit('nova_mensagem', {"texto": texto})
    except Exception as e:
        emit('erro', {"erro": str(e)})

if __name__ == '__main__':
    # Porta 6500 como você definiu
    socketio.run(app, host='0.0.0.0', port=6500)

import sys
from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit
from google import genai
from google.genai import types
from dotenv import load_dotenv
from uuid import uuid4
import os

# Carrega as variáveis ocultas
load_dotenv()

MODELO = "gemini-3.5-flash" 

instrucoes = """
Você é um especialista em ocultismo da Ordem Paranormal. 
Seu tom é misterioso, sério e técnico. Você lida com rituais, elementos (Sangue, Morte, Energia, Conhecimento), 
criaturas e investigações. Responda como se estivesse analisando um Caso Paranormal. 
Se a pergunta for irrelevante, trate-a como uma brecha na Membrana.
"""

client = genai.Client(api_key=os.getenv("GENAI_KEY"))
app = Flask(__name__)

# Configuração de SocketIO otimizada para Render
# Usamos '*' para evitar bloqueios de CORS. 
# ping_timeout é importante para conexões instáveis do plano gratuito.
# Mude a linha do socketio para esta:
socketio = SocketIO(
    app, 
    cors_allowed_origins="*",  # O asterisco libera qualquer origem para teste
    async_mode='eventlet',
    ping_timeout=120,
    ping_interval=25
)

active_chats = {}

def get_chat_session(session_id):
    """Gerencia a sessão de chat baseada no ID enviado pelo cliente"""
    if session_id not in active_chats:
        chat_session = client.chats.create(
            model=MODELO,
            config=types.GenerateContentConfig(system_instruction=instrucoes)
        )
        active_chats[session_id] = chat_session
    return active_chats[session_id]

@app.route('/')
def root():
    return jsonify({"status": "Servidor Operante", "tema": "Ordem Paranormal"})

# ------------------------------------------------------------------
# EVENTOS SOCKET.IO
# ------------------------------------------------------------------

@socketio.on('connect')
def handle_connect():
    print(f"Cliente conectado: {request.sid}")

@socketio.on('enviar_mensagem')
def handle_enviar_mensagem(data):
    # Agora pegamos o ID que o seu script.js envia no 'data'
    session_id = data.get("session_id")
    mensagem_usuario = data.get("mensagem")

    if not session_id or not mensagem_usuario:
        emit('erro', {"erro": "Dados incompletos"})
        return

    try:
        user_chat = get_chat_session(session_id)
        resposta = user_chat.send_message(mensagem_usuario)
        
        texto = resposta.text if hasattr(resposta, 'text') else resposta.candidates[0].content.parts[0].text
        
        emit('nova_mensagem', {"remetente": "bot", "texto": texto})
    except Exception as e:
        print(f"Erro no processamento: {e}")
        emit('erro', {"erro": "A Membrana está instável, tente novamente."})

@socketio.on('disconnect')
def handle_disconnect():
    print(f"Cliente desconectado: {request.sid}")

if __name__ == "__main__":
    # O Render ignora o port=5000 e usa a variável de ambiente, 
    # mas o eventlet funcionará corretamente com esta chamada:
    socketio.run(app, port=6500)

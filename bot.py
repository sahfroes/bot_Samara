import os
import time
from threading import Thread
import telebot
from telebot import types  # <--- ESSA LINHA É OBRIGATÓRIA PARA OS BOTÕES
from dotenv import load_dotenv
from flask import Flask

load_dotenv()

CHAVE_API = os.getenv("CHAVE_API")
if not CHAVE_API:
    raise ValueError("ERRO: CHAVE_API não encontrada!")

bot = telebot.TeleBot(CHAVE_API)
app = Flask('')

@app.route('/')
def home():
    return "O bot está online com botões!"

def run_server():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port, use_reloader=False)

def keep_alive():
    t = Thread(target=run_server, daemon=True)
    t.start()

# FUNÇÃO QUE GERA OS BOTÕES CLICÁVEIS
def criar_menu_botoes():
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn_site = types.InlineKeyboardButton("🌐 Acessar o Site", callback_data="btn_site")
    btn_suporte = types.InlineKeyboardButton("🛠️ Suporte Técnico", callback_data="btn_suporte")
    btn_ajuda = types.InlineKeyboardButton("❓ Ajuda", callback_data="btn_ajuda")
    markup.add(btn_site, btn_suporte, btn_ajuda)
    return markup

# Capta /start, /iniciar ou a palavra "start" solta (como você digitou no print)
@bot.message_handler(commands=['iniciar', 'start'])
@bot.message_handler(func=lambda msg: msg.text.lower() == 'start')
def boas_vindas(mensagem):
    texto = "Olá! Eu sou a Agente Samanta. Como posso te ajudar hoje?\n\nEscolha uma opção nos botões abaixo:"
    # O 'reply_markup' é quem anexa os botões à mensagem!
    bot.send_message(mensagem.chat.id, texto, reply_markup=criar_menu_botoes())

@bot.message_handler(commands=['ajuda'])
def ajuda(mensagem):
    bot.send_message(mensagem.chat.id, "Escolha uma opção:", reply_markup=criar_menu_botoes())

# TRATAMENTO DOS CLIQUES DOS BOTÕES
@bot.callback_query_handler(func=lambda call: True)
def responder_cliques(call):
    bot.answer_callback_query(call.id)

    #pegando o id do chat de forma segura para responder
    chat_id = call.message.chat.id
    
    if call.data == "btn_site":
        bot.send_message(chat_id, "Nosso site oficial é: https://site.cff.org.br/")
    elif call.data == "btn_suporte":
        texto_suporte = "📞 Suporte Técnico TI:\n\n📧 E-mail: ti@cff.org.br\n📱 Telefone: (61) 9380-7000"
        bot.send_message(chat_id, texto_suporte)
    elif call.data == "btn_ajuda":
        texto_ajuda = "💡 Use os botões abaixo da tela para navegar de forma rápida!"
        bot.send_message(chat_id, texto_ajuda)


if __name__ == "__main__":
    import time
    
    print("Iniciando servidor de sobrevivência Flask...")
    keep_alive()
    
    print("Forçando encerramento de conexões antigas...")
    try:
        bot.close()  # <--- NOVA LINHA: Diz ao Telegram para fechar sessões antigas deste token
    except Exception:
        pass
        
    print("Limpando webhooks travados...")
    bot.delete_webhook(drop_pending_updates=True)
    
    print("Bot da Samara escutando as mensagens com botões!")
    while True:
        try:
            bot.polling(non_stop=True, interval=0, timeout=20)
        except Exception as e:
            print(f"Erro: {e}")
            time.sleep(5)
    
import os
import logging
import time
from threading import Thread
import telebot
from telebot import types
from dotenv import load_dotenv
from flask import Flask

# Importa a função modificada 
from ia import gerar_resposta

# 1. Configurações de Ambiente e Logs
load_dotenv()

CHAVE_API = os.getenv("CHAVE_API")
if not CHAVE_API:
    raise ValueError("ERRO: CHAVE_API não encontrada!")

bot = telebot.TeleBot(CHAVE_API)

# Desativa os logs repetitivos do Flask para limpar o terminal
hl = logging.getLogger('werkzeug')
hl.setLevel(logging.ERROR)
app = Flask('')

@app.route('/')
def home():
    return "O bot da Samara está online e perfeito!"

def run_server():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port, use_reloader=False)

def keep_alive():
    t = Thread(target=run_server, daemon=True)
    t.start()

# 2. Gerenciadores de Menus (Interface Visual)
def menu_principal():
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn_site = types.InlineKeyboardButton("🌐 Portal Oficial CFF", callback_data="btn_site")
    btn_ajuda = types.InlineKeyboardButton("🩺 Central do Farmacêutico", callback_data="btn_ajuda")
    btn_ia = types.InlineKeyboardButton("💬 Tirar Dúvida (IA Samara)", callback_data="btn_ia")
    btn_suporte = types.InlineKeyboardButton("🛠️ Suporte Técnico TI", callback_data="btn_suporte")
    markup.add(btn_site, btn_ajuda, btn_ia, btn_suporte)
    return markup

def menu_farmaceutico():
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn_legislacao = types.InlineKeyboardButton("📜 Legislação e Resoluções", url="https://site.cff.org.br/legislacao")
    btn_cedula_digital = types.InlineKeyboardButton("🪪 Emissão de Cédula Digital", url="https://site.cff.org.br/cedula")
    btn_publicacao = types.InlineKeyboardButton("📚 Manuais Práticos e Guias", url="https://site.cff.org.br/publicacoes")
    btn_sei = types.InlineKeyboardButton("💻 Sistema SEI", url="https://site.cff.org.br/sei")
    btn_fale_conosco = types.InlineKeyboardButton("📞 Fale com o CFF (Contatos)", url="https://site.cff.org.br/fale-com-cff")
    btn_voltar = types.InlineKeyboardButton("« Voltar ao Menu Principal", callback_data="btn_voltar")
    markup.add(btn_legislacao, btn_cedula_digital, btn_publicacao, btn_sei, btn_fale_conosco, btn_voltar)
    return markup

# ==========================================================
# 3. Handlers de Comandos de Texto e Conexão IA
# ==========================================================

# Alterado o nome apenas para organização 
def processar_duvida_ia(mensagem):
    chat_id = mensagem.chat.id
    pergunta = mensagem.text

    # Caso o usuário envie um comando por texto em vez de uma dúvida
    if pergunta in ['/start', '/ajuda', '/comecar', '/iniciar', '/menu']:
        exibir_menu_inicial(chat_id)
        return

    bot.send_chat_action(chat_id, 'typing')
    
    # Chama a IA 
    resposta_ia = gerar_resposta(pergunta)

    markup_voltar = types.InlineKeyboardMarkup().add(
        types.InlineKeyboardButton("« Voltar ao Menu", callback_data="btn_voltar")
    )
    bot.send_message(chat_id, resposta_ia, reply_markup=markup_voltar, parse_mode="Markdown")

# Regra A: Atende comandos por cliques (/start, /ajuda, etc)
@bot.message_handler(commands=['iniciar', 'start', 'comecar', 'ajuda', 'menu'])
def enviar_boas_vindas_comando(mensagem):
    exibir_menu_inicial(mensagem.chat.id)

# Regra B: Se o usuário enviar QUALQUER outro texto padrão, abre o menu
@bot.message_handler(func=lambda msg: True)
def enviar_boas_vindas_texto(mensagem):
    exibir_menu_inicial(mensagem.chat.id)

def exibir_menu_inicial(chat_id):
    texto = """👋 *Olá! Eu sou a Agente Samara.*

Estou aqui para facilitar o seu acesso aos serviços do *CFF*. Como posso te ajudar hoje?

📌 *Selecione uma opção nos botões abaixo:*"""
    bot.send_message(chat_id, texto, reply_markup=menu_principal(), parse_mode="Markdown")


# 4. Tratamento Inteligente dos Cliques (Edição de Mensagem)
@bot.callback_query_handler(func=lambda call: True)
def responder_cliques(call):
    bot.answer_callback_query(call.id)
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    
    if call.data == "btn_site":
        texto_site = """🌐 *Portal do CFF*

O site oficial do Conselho Federal de Farmácia está disponível no link abaixo:
🔗 https://site.cff.org.br/"""
        bot.edit_message_text(texto_site, chat_id, message_id, reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("« Voltar", callback_data="btn_voltar")), parse_mode="Markdown")
        
    elif call.data == "btn_suporte":
        texto_suporte = """🛠️ *Suporte Técnico TI — CFF*

Precisa de auxílio técnico? Entre em contato com a nossa equipe:

📧 *E-mail:* ti@cff.org.br
📱 *Telefone:* (61) 9380-7000
🕒 *Atendimento:* Segunda a Sexta-feira, das 8h às 18h"""
        bot.edit_message_text(texto_suporte, chat_id, message_id, reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("« Voltar", callback_data="btn_voltar")), parse_mode="Markdown")
      
    elif call.data == "btn_ajuda":
        texto_ajuda = """⚡ *Central de Ajuda ao Farmacêutico*

Plataforma de acesso rápido aos serviços integrados. Clique no botão correspondente para ser direcionado de forma segura:"""
        bot.edit_message_text(texto_ajuda, chat_id, message_id, reply_markup=menu_farmaceutico(), parse_mode="Markdown")

    elif call.data == "btn_ia":
        texto_ia = """💬 *Modo Inteligente Ativado!*

Eu sou a Samara. Pode me fazer qualquer pergunta sobre legislação farmacêutica, ética ou desafios da profissão.

👉 *Digite sua dúvida abaixo:*"""
        msg_enviada = bot.edit_message_text(texto_ia, chat_id, message_id, parse_mode="Markdown")
        
        # Vincula o próximo passo à  função atualizada
        bot.register_next_step_handler(msg_enviada, processar_duvida_ia)

    elif call.data == "btn_voltar":
        texto_voltar = """👋 *Olá! Eu sou a Agente Samara.*

Como posso te ajudar hoje? Selecione uma opção nos botões abaixo:"""
        bot.edit_message_text(texto_voltar, chat_id, message_id, reply_markup=menu_principal(), parse_mode="Markdown")

# 5. Inicialização do Bot
if __name__ == "__main__":
    print("Iniciando servidor de sobrevivência Flask...")
    keep_alive()
    
    print("Forçando encerramento de conexões antigas...")
    try:
        bot.close()
    except Exception:
        pass
        
    print("Configurando botões de comando padrão no Telegram...")
    bot.set_my_commands([
        types.BotCommand("start", "Menu Principal / Iniciar"),
        types.BotCommand("ajuda", "Central do Farmacêutico")
    ])
    
    bot.delete_webhook(drop_pending_updates=True)
    print("Bot da Samara online, lindo e escutando mensagens com IA!")
    
    while True:
        try:
            bot.polling(non_stop=True, interval=0, timeout=20)
        except Exception as e:
            print(f"Erro detectado: {e}")
            time.sleep(5)
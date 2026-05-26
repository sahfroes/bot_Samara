import os
import time
from threading import Thread
import telebot
from telebot import types
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
    return "O bot está online, elegante e com botões!"

def run_server():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port, use_reloader=False)

def keep_alive():
    t = Thread(target=run_server, daemon=True)
    t.start()

# MENU PRINCIPAL (Mais limpo e com foco visual)
def criar_menu_botoes():
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn_site = types.InlineKeyboardButton("🌐 Portal Oficial CFF", callback_data="btn_site")
    btn_ajuda = types.InlineKeyboardButton("🩺 Central do Farmacêutico", callback_data="btn_ajuda")
    btn_suporte = types.InlineKeyboardButton("🛠️ Suporte Técnico TI", callback_data="btn_suporte")
    markup.add(btn_site, btn_ajuda, btn_suporte)
    return markup

# Boas-vindas formatado com Markdown para dar destaque às palavras
@bot.message_handler(commands=['iniciar', 'start','começar'])
@bot.message_handler(func=lambda msg: msg.text.lower() == 'start')

def boas_vindas(mensagem):
    texto = """ *Olá! Eu sou a Agente Samara.*

Estou aqui para facilitar o seu acesso aos serviços do *CFF*. Como posso te ajudar hoje?

📌 *Selecione uma opção nos botões abaixo:*"""
    bot.send_message(mensagem.chat.id, texto, reply_markup=criar_menu_botoes(), parse_mode="Markdown")

@bot.message_handler(commands=['ajuda'])
def ajuda(mensagem):
    texto = " *Menu de Navegação Rápida*\n\nSelecione a opção desejada abaixo:"
    bot.send_message(mensagem.chat.id, texto, reply_markup=criar_menu_botoes(), parse_mode="Markdown")

# TRATAMENTO DOS CLIQUES DOS BOTÕES
@bot.callback_query_handler(func=lambda call: True)
def responder_cliques(call):
    bot.answer_callback_query(call.id)
    chat_id = call.message.chat.id
    
    # Correção do bug 'btnite' -> 'btn_site'
    if call.data == "btn_site":
        texto_site = """🌐 *Portal do CFF*

O site oficial do Conselho Federal de Farmácia está disponível no link abaixo:
🔗 https://site.cff.org.br/"""
        bot.send_message(chat_id, texto_site, parse_mode="Markdown")
        
    elif call.data == "btn_suporte":
        texto_suporte = """🛠️ *Suporte Técnico TI — CFF*

Precisa de auxílio técnico? Entre em contato com a nossa equipe:

📧 *E-mail:* ti@cff.org.br
📱 *Telefone:* (61) 9380-7000
🕒 *Atendimento:* Segunda a Sexta-feira"""
        bot.send_message(chat_id, texto_suporte, parse_mode="Markdown")
      
    elif call.data == "btn_ajuda":
        menu_ajuda = types.InlineKeyboardMarkup(row_width=1)
        
        # Botões organizados com foco total na usabilidade do Farmacêutico
        btn_legislacao = types.InlineKeyboardButton("📜 Legislação e Resoluções", url="https://site.cff.org.br/legislacao")
        btn_cedula_digital = types.InlineKeyboardButton("🪪 Emissão de Cédula Digital", url="https://site.cff.org.br/cedula")
        btn_publicacao = types.InlineKeyboardButton("📚 Manuais Práticos e Guias", url="https://site.cff.org.br/publicacoes")
        btn_sei = types.InlineKeyboardButton("💻 Sistema SEI", url="https://site.cff.org.br/sei")
        btn_fale_conosco = types.InlineKeyboardButton("📞 Fale com o CFF (Contatos)", url="https://site.cff.org.br/fale-com-cff")

        menu_ajuda.add(btn_legislacao, btn_cedula_digital, btn_publicacao, btn_sei, btn_fale_conosco)

        texto_ajuda = """⚡ *Central de Ajuda ao Farmacêutico*

Plataforma de acesso rápido aos serviços integrados. Clique no botão correspondente para ser direcionado de forma segura:"""
        
        bot.send_message(chat_id, texto_ajuda, reply_markup=menu_ajuda, parse_mode="Markdown")

if __name__ == "__main__":
    print("Iniciando servidor de sobrevivência Flask...")
    keep_alive()
    
    print("Forçando encerramento de conexões antigas...")
    try:
        bot.close()
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
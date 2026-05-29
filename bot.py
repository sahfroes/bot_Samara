import os
import logging
import time
from threading import Thread
import telebot
from telebot import types
from dotenv import load_dotenv
from flask import Flask

# Importações dos outros arquivos
from ia import gerar_resposta
from banco import inicializar_banco, consultar_cadastro

# 1. Configurações de Ambiente e Logs
load_dotenv()

CHAVE_API = os.getenv("TELEGRAM_BOT_TOKEN") or os.getenv("CHAVE_API")
if not CHAVE_API:
    raise ValueError("ERRO: TELEGRAM_BOT_TOKEN ou CHAVE_API não encontrada!")

bot = telebot.TeleBot(CHAVE_API)

# Dicionário na memória para guardar as sessões ativas (CORRIGIDO: adicionado aqui)
usuarios_logados = {}

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

# Função Auxiliar para evitar erros de cliques repetidos
def editar_mensagem_segura(texto, chat_id, message_id, reply_markup=None):
    try:
        bot.edit_message_text(texto, chat_id, message_id, reply_markup=reply_markup, parse_mode="Markdown")
    except telebot.apihelper.ApiTelegramException as e:
        if "message is not modified" not in e.description:
            raise e

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

def processar_duvida_ia(mensagem):
    chat_id = mensagem.chat.id
    pergunta = mensagem.text

    if pergunta in ['/start', '/ajuda', '/comecar', '/iniciar', '/menu', 'sair', 'Sair']:
        bot.clear_step_handler_by_chat_id(chat_id=chat_id)
        exibir_menu_inicial(chat_id)
        return

    bot.send_chat_action(chat_id, 'typing')
    resposta_ia = gerar_resposta(pergunta)

    markup_voltar = types.InlineKeyboardMarkup().add(
        types.InlineKeyboardButton("« Sair da IA (Menu Principal)", callback_data="btn_voltar")
    )
    bot.send_message(chat_id, resposta_ia, reply_markup=markup_voltar, parse_mode="Markdown")
    
    ajuda_texto = "✍️ *Pode fazer outra pergunta se desejar (ou envie /menu para sair):*"
    proxima_msg = bot.send_message(chat_id, ajuda_texto, parse_mode="Markdown")
    bot.register_next_step_handler(proxima_msg, processar_duvida_ia)

# Fluxo de Autenticação inicial
def iniciar_autenticacao(mensagem):
    chat_id = mensagem.chat.id
    bot.clear_step_handler_by_chat_id(chat_id=chat_id)
    
    if chat_id in usuarios_logados:
        exibir_menu_inicial(chat_id)
        return

    texto_cpf = """👋 *Olá! Eu sou a Agente Samara, assistente virtual oficial do CFF.*

Para iniciar o seu atendimento personalizado, por favor, **digite o seu CPF** (apenas números):"""
    msg = bot.send_message(chat_id, texto_cpf, parse_mode="Markdown")
    bot.register_next_step_handler(msg, processar_cpf)

def processar_cpf(mensagem):
    chat_id = mensagem.chat.id
    cpf_digitado = mensagem.text

    if cpf_digitado.startswith('/'):
        bot.clear_step_handler_by_chat_id(chat_id=chat_id)
        enviar_boas_vindas_comando(mensagem)
        return

    bot.send_chat_action(chat_id, 'typing')
    dados_farmaceutico = consultar_cadastro(cpf_digitado)
    
    if dados_farmaceutico:
        tratamento = "Doutora" if dados_farmaceutico["genero"] == "F" else "Doutor"
        primeiro_nome = dados_farmaceutico["nome"].split()[0]
        
        usuarios_logados[chat_id] = {
            "nome": primeiro_nome,
            "tratamento": tratamento
        }
        
        bot.send_message(chat_id, f"🎉 Cadastro localizado!\nSeja bem-vindo(a), *{tratamento} {primeiro_nome}*.", parse_mode="Markdown")
        exibir_menu_inicial(chat_id)
    else:
        usuarios_logados[chat_id] = {"nome": "Colega", "tratamento": "Doutor(a)"}
        bot.send_message(chat_id, "⚠️ CPF não localizado no sistema. Acesso liberado como visitante.")
        exibir_menu_inicial(chat_id)

# Regra A: Quando o usuário clica ou digita comandos de menu
@bot.message_handler(commands=['iniciar', 'start', 'comecar', 'ajuda', 'menu'])
def enviar_boas_vindas_comando(mensagem):
    iniciar_autenticacao(mensagem)

# Regra B: Só intercepta se o usuário mandar textos aleatórios sem cadastro
@bot.message_handler(func=lambda msg: True)
def enviar_boas_vindas_texto(mensagem):
    iniciar_autenticacao(mensagem)

def exibir_menu_inicial(chat_id):
    dados = usuarios_logados.get(chat_id, {"nome": "Colega", "tratamento": "Doutor(a)"})
    texto = f"""👋 *Olá, {dados['tratamento']} {dados['nome']}!*

Como posso te ajudar hoje nos serviços do *CFF*?

📌 *Selecione uma opção nos botões abaixo:*"""
    bot.send_message(chat_id, texto, reply_markup=menu_principal(), parse_mode="Markdown")

# 4. Tratamento dos Cliques
@bot.callback_query_handler(func=lambda call: True)
def responder_cliques(call):
    bot.answer_callback_query(call.id)
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    
    if call.data == "btn_site":
        texto_site = """🌐 *Portal do CFF*\n\nO site oficial do Conselho Federal de Farmácia está disponível no link abaixo:\n🔗 https://site.cff.org.br/"""
        editar_mensagem_segura(texto_site, chat_id, message_id, reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("« Voltar", callback_data="btn_voltar")))
        
    elif call.data == "btn_suporte":
        texto_suporte = """🛠️ *Suporte Técnico TI — CFF*\n\nPrecisa de auxílio técnico? Entre em contato:\n\n📧 *E-mail:* ti@cff.org.br\n📱 *Telefone:* (61) 9380-7000\n🕒 *Atendimento:* Segunda a Sexta, das 8h às 18h"""
        editar_mensagem_segura(texto_suporte, chat_id, message_id, reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("« Voltar", callback_data="btn_voltar")))
      
    elif call.data == "btn_ajuda":
        texto_ajuda = """⚡ *Central de Ajuda ao Farmacêutico*\n\nPlataforma de acesso rápido aos serviços integrados:"""
        editar_mensagem_segura(texto_ajuda, chat_id, message_id, reply_markup=menu_farmaceutico())

    elif call.data == "btn_ia":
        texto_ia = """💬 *Modo Inteligente Ativado!*\n\nEu sou a Samara. Pode me fazer qualquer pergunta sobre legislação farmacêutica, ética ou desafios da profissão.\n\n👉 *Digite sua dúvida abaixo:*"""
        bot.clear_step_handler_by_chat_id(chat_id=chat_id)
        msg_enviada = bot.edit_message_text(texto_ia, chat_id, message_id, parse_mode="Markdown")
        bot.register_next_step_handler(msg_enviada, processar_duvida_ia)

    elif call.data == "btn_voltar":
        bot.clear_step_handler_by_chat_id(chat_id=chat_id)
        dados = usuarios_logados.get(chat_id, {"nome": "Colega", "tratamento": "Doutor(a)"})
        texto_voltar = f"👋 *Olá, {dados['tratamento']} {dados['nome']}!*\n\nComo posso te ajudar hoje? Selecione uma opção abaixo:"
        editar_mensagem_segura(texto_voltar, chat_id, message_id, reply_markup=menu_principal())

# 5. Inicialização do Bot
if __name__ == "__main__":
    print("Inicializando e verificando banco de dados...")
    inicializar_banco()  #

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
    print("Bot da Samara online e escutando mensagens com IA!")
    
    while True:
        try:
            bot.polling(non_stop=True, interval=0, timeout=20)
        except Exception as e:
            print(f"Erro detectado: {e}")
            time.sleep(5)
import os
import logging
import time
import re
from threading import Thread
import telebot
from telebot import types
from dotenv import load_dotenv
from flask import Flask

# Importações dos outros arquivos locais
from ia import gerar_resposta
from banco import inicializar_banco, consultar_cadastro
from banco import inicializar_banco, consultar_cadastro, armazenar_conversa, buscar_historico, limpar_historico

# 1. Configurações de Ambiente e Logs
load_dotenv()

CHAVE_API = os.getenv("TELEGRAM_BOT_TOKEN") or os.getenv("CHAVE_API")
if not CHAVE_API:
    raise ValueError("ERRO: TELEGRAM_BOT_TOKEN ou CHAVE_API não encontrada!")

# Criando a instância do BOT
bot = telebot.TeleBot(CHAVE_API)

# Dicionário na memória para guardar as sessões ativas
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

    if not pergunta:
        return

    # Se decidir sair da IA por texto ou comando, limpa o histórico do banco de dados
    if pergunta.strip() in ['/start', '/ajuda', '/comecar', '/iniciar', '/menu', 'sair', 'Sair']:
        limpar_historico(chat_id)
        bot.clear_step_handler_by_chat_id(chat_id=chat_id)
        exibir_menu_inicial(chat_id)
        return

    # 1. Salva a pergunta que o usuário acabou de fazer no banco de dados
    armazenar_conversa(chat_id, role="user", content=pergunta)

    # 2. Busca o histórico recente (as últimas 6 interações) para dar contexto à Samara
    historico = buscar_historico(chat_id, limite=6)

    bot.send_chat_action(chat_id, 'typing')
    
    # 3. Envia o histórico estruturado para o arquivo ia.py obter a resposta do Llama
    resposta_ia = gerar_resposta(historico, pergunta)

    # 4. Salva a resposta que a IA gerou no banco de dados também, para ela se lembrar na próxima rodada
    armazenar_conversa(chat_id, role="assistant", content=resposta_ia)

    markup_voltar = types.InlineKeyboardMarkup().add(
        types.InlineKeyboardButton("« Sair da IA (Menu Principal)", callback_data="btn_voltar")
    )
    bot.send_message(chat_id, resposta_ia, reply_markup=markup_voltar, parse_mode="Markdown")
    
    ajuda_texto = "✍️ *Pode continuar a conversa ou fazer outra pergunta (envie /menu para sair):*"
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
    texto_usuario = mensagem.text or ""

    if texto_usuario.startswith('/'):
        bot.clear_step_handler_by_chat_id(chat_id=chat_id)
        enviar_boas_vindas_comando(mensagem)
        return

    # Remove qualquer caractere que não seja número
    cpf_digitado = re.sub(r'\D', '', texto_usuario)

    if len(cpf_digitado) != 11:
        msg = bot.send_message(chat_id, "⚠️ *CPF inválido.* Por favor, digite um CPF válido contendo exatamente 11 dígitos (apenas números):", parse_mode="Markdown")
        bot.register_next_step_handler(msg, processar_cpf)
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
        usuarios_logados[chat_id] = {
            "nome": "Colega", 
            "tratamento": "Doutor(a)"
        }
        bot.send_message(chat_id, "⚠️ CPF não localizado no sistema. Acesso liberado como visitante.")
        exibir_menu_inicial(chat_id)

# Regra A: Quando o usuário clica ou digita comandos de menu
@bot.message_handler(commands=['iniciar', 'start', 'comecar', 'ajuda', 'menu'])
def enviar_boas_vindas_comando(mensagem):
    chat_id = mensagem.chat.id
    limpar_historico(chat_id) 
    iniciar_autenticacao(mensagem)

# Regra B: Intercepta se o usuário mandar textos aleatórios sem cadastro
@bot.message_handler(func=lambda msg: True)
def enviar_boas_vindas_texto(mensagem):
    chat_id = mensagem.chat.id
    if bot.get_state(chat_id) is not None or chat_id in bot.next_step_handlers:
        return
        
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
    
    # IMPORTANTE: Limpa steps de texto ativos para evitar comportamento fantasma se usar botões inline
    bot.clear_step_handler_by_chat_id(chat_id=chat_id)
    
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
        limpar_historico(chat_id) # Garante que a conversa começará do zero, sem lixo antigo
        texto_ia = """💬 *Modo Inteligente Ativado!*\n\nEu sou a Samara. Agora eu consigo me lembrar do contexto da nossa conversa! Pode falar comigo naturalmente.\n\n👉 *Digite sua dúvida abaixo:*"""
        msg_enviada = bot.edit_message_text(texto_ia, chat_id, message_id, parse_mode="Markdown")
        bot.register_next_step_handler(msg_enviada, processar_duvida_ia)

    elif call.data == "btn_voltar":
        dados = usuarios_logados.get(chat_id, {"nome": "Colega", "tratamento": "Doutor(a)"})
        texto_voltar = f"👋 *Olá, {dados['tratamento']} {dados['nome']}!*\n\nComo posso te ajudar hoje? Selecione uma opção abaixo:"
        editar_mensagem_segura(texto_voltar, chat_id, message_id, reply_markup=menu_principal())     

    elif call.data == "btn_voltar":
        limpar_historico(chat_id) # Limpa os dados de histórico para economizar espaço se ele saiu do menu
        dados = usuarios_logados.get(chat_id, {"nome": "Colega", "tratamento": "Doutor(a)"})
        texto_voltar = f"👋 *Olá, {dados['tratamento']} {dados['nome']}!*\n\nComo posso te ajudar hoje? Selecione uma opção abaixo:"
        editar_mensagem_segura(texto_voltar, chat_id, message_id, reply_markup=menu_principal())

# 5. Inicialização do Bot
if __name__ == "__main__":
    print("Inicializando e verificando banco de dados...")
    inicializar_banco()

    print("Iniciando servidor de sobrevivência Flask...")
    keep_alive()
    
    print("Forçando encerramento de conexões antigas...")
    try:
        bot.remove_webhook()
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
    
    # O infinity_polling nativo já cuida de erros e reconexões automaticamente
    bot.infinity_polling(skip_pending=True, timeout=60, long_polling_timeout=20)
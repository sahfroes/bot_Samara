import os
import telebot
from dotenv import load_dotenv
from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "O bot da Samara está online e funcionando!"

def run():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

#aqui ele carrega as varias do arquivo .env para a memoria
load_dotenv()

CHAVE_API = os.getenv("CHAVE_API")
bot = telebot.TeleBot(CHAVE_API)

# Função para responder a mensagem de boas-vindas
@bot.message_handler(commands=['iniciar', 'start'])
def boas_vindas(mensagem):
    # Juntamos o texto usando \n para pular linha, sem risco de erro de espaço!
    texto = "Olá! Eu sou a Agente Samanta. Como posso te ajudar hoje?\n\n" \
            "Escolha uma opção digitando o comando correspondente:\n" \
            "/site - Para receber o link do nosso site.\n" \
            "/suporte - Para falar com o suporte técnico.\n" \
            "/ajuda - Para ver as instruções de ajuda."
    bot.reply_to(mensagem, texto)

# Função para responder a mensagem de ajuda
@bot.message_handler(commands=['ajuda'])
def ajuda(mensagem):
    texto = "Escolha uma opção para continuar:\n" \
            "/site - Para receber o link do nosso site.\n" \
            "/suporte - Para falar com um atendente da TI."
    bot.reply_to(mensagem, texto)

# Função para responder a mensagem de enviar o link do site
@bot.message_handler(commands=['site'])
def enviar_site(mensagem):
    bot.reply_to(mensagem, "Nosso site oficial é: https://site.cff.org.br/")

# Função para responder a mensagem de solicitar suporte
@bot.message_handler(commands=['suporte'])
def solicitar_suporte(mensagem):
    texto = " Suporte Técnico TI:\n\n" \
            " E-mail: ti@cff.org.br\n" \
            " Telefone: (61) 9380700"
    bot.reply_to(mensagem, texto)

# Função que mantém o bot rodando e escutando as mensagens
#bot.polling()

# 3. Execução em paralelo (Servidor Web + Bot do Telegram)
if __name__ == "__main__":
    print("Iniciando servidor de sobrevivência Flask...")
    keep_alive()  # Ativa o mini site que o Render exige
    
    print("Limpando conexões antigas e webhooks travados no Telegram...")
    bot.delete_webhook(drop_pending_updates=True)  # Resolve o erro de conflito 409
    
    print("Bot da Samara escutando as mensagens!")
    # non_stop=True faz com que o bot não caia sozinho por instabilidade de rede
    bot.polling(non_stop=True)
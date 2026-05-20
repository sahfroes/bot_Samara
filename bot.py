import os
import telebot
from dotenv import load_dotenv

#aqui ele carrega as varias do arquivo .env para a memoria
load_dotenv()

CHAVE_API = os.getenv("TELEGRAM_TOKEN")
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
            " Telefone: (61) 380700"
    bot.reply_to(mensagem, texto)

# Função que mantém o bot rodando e escutando as mensagens
bot.polling()
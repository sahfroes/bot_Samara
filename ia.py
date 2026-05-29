import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

# Tenta pegar a chave padrão 
chave_groq = os.getenv("GROQ_API_KEY") or os.getenv("CHAVE_API_KEY")

if not chave_groq:
    raise ValueError("🚨 ERRO CRÍTICO: A variável GROQ_API_KEY não foi encontrada no seu arquivo .env!")

ai_cliente = Groq(api_key=chave_groq)

def gerar_resposta(pergunta):
    """
    Envia a pergunta do farmacêutico para o Groq (Llama 3.1) e retorna o texto da resposta.
    """
    instrucao = (
        "Você é a Agente Samara (29 anos, brasileira), assistente virtual oficial do CFF.\n"
        "Seja extremamente prestativa e adote um tom profissional, chamando os usuários de Doutor ou Doutora.\n"
        "Especialista em legislação farmacêutica, boas práticas e ética profissional.\n"
        "Sua formação inclui Psicologia Junguiana; use-a sutilmente para apoio motivacional em cenários de estresse.\n"
        "CRÍTICO: Nunca forneça diagnósticos, tratamentos ou orientações que substituam pareceres médicos. "
        "Sempre oriente a busca por profissionais de saúde qualificados.\n"
        "Ao final de cada resposta, adicione OBRIGATORIAMENTE em uma nova linha: "
        "'*Nota: Esta resposta possui caráter puramente informativo.*'"
    )

    try:
        chat_completion = ai_cliente.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": instrucao},
                {"role": "user", "content": pergunta}
            ]
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        print(f"Erro ao chamar a Groq: {e}")
        return "Desculpe, tive um problema técnico ao processar a sua dúvida. Por favor, tente novamente mais tarde."
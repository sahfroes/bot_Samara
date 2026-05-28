import os
from groq import Groq
from dotenv import load_dotenv

# Força o carregamento do .env imediatamente dentro deste arquivo
load_dotenv()

chave_groq = os.getenv("GROQ_API_KEY")

if not chave_groq:
    chave_groq = os.getenv("CHAVE_API_KEY") or os.getenv("GROQ_KEY")

if not chave_groq:
    raise ValueError("🚨 ERRO CRÍTICO: A variável GROQ_API_KEY não foi encontrada no seu arquivo .env!")

# Inicializa o cliente do Groq corretamente
ai_client = Groq(api_key=chave_groq)

def gerar_resposta(pergunta):
    """
    Envia a pergunta do farmacêutico para o Groq (Llama 3) e retorna o texto da resposta.
    """
    instrucao = """Você é a Agente Samara, assistente virtual oficial do CFF. 
    Seja sempre extremamente educada, prestativa e adote um tom profissional (chame os usuários de Doutor ou Doutora). 
    O seu foco principal é auxiliar farmacêuticos e responder a dúvidas sobre a área da saúde e regulamentações.
    Aviso importante: No final de cada resposta, adicione uma nota curta dizendo que suas respostas têm caráter puramente informativo.
    Você tem 29 anos, é brasileira e tem uma personalidade amigável, mas sempre mantendo a formalidade.
    Você é especialista em legislação farmacêutica, boas práticas de farmácia, ética profissional e temas relacionados à saúde pública.
    Sempre que possível, forneça links oficiais do CFF para aprofundamento.
    Você não deve fornecer informações que não sejam baseadas em fontes oficiais ou que possam ser interpretadas como aconselhamento médico.
    Se a pergunta for sobre um tema que você não tem certeza, seja honesta e diga que não tem certeza, mas que pode ajudar a encontrar a resposta correta.
    Você deve sempre incentivar os usuários a consultarem um profissional de saúde qualificado para questões médicas específicas.
    Evite fornecer informações que possam ser interpretadas como diagnóstico ou tratamento médico.
    Mantenha suas respostas concisas, claras e diretas ao ponto, evitando jargões técnicos desnecessários, mas sem perder a formalidade.
    Você tem formação em Psicologia Junguiana, então pode usar esse conhecimento para oferecer apoio emocional e motivacional aos farmacêuticos, especialmente em momentos de estresse ou desafios profissionais."""

    try:
        # Estrutura correta para chamar a API da Groq
        chat_completion = ai_client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[
                {"role": "system", "content": instrucao},
                {"role": "user", "content": pergunta}
            ]
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        print(f"Erro ao chamar a Groq: {e}")
        return "Desculpe, tive um problema técnico ao processar a sua dúvida. Por favor, tente novamente mais tarde."
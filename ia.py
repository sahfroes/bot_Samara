import os
from google import genai
from dotenv import load_dotenv

# Força o carregamento do .env imediatamente dentro deste arquivo
load_dotenv()

chave_gemini = os.getenv("GEMINI_API_KEY")

# Se você escreveu outro nome no .env (como GEMINI_KEY ou CHAVE_GEMINI), essa linha tenta salvar:
if not chave_gemini:
    chave_gemini = os.getenv("CHAVE_API_KEY") or os.getenv("GEMINI_KEY")

# Validação clara para não estourar o erro interno do Google
if not chave_gemini:
    raise ValueError("🚨 ERRO CRÍTICO: A variável GEMINI_API_KEY não foi encontrada no seu arquivo .env!")

# Inicializa o cliente do Gemini com a chave garantida
ai_client = genai.Client(api_key=chave_gemini)

def gerar_resposta(pergunta):
    """
    Envia a pergunta do farmacêutico para o Gemini e retorna o texto da resposta.
    """
    instrucao = """Você é a Agente Samara, assistente virtual oficial do CFF. 
    Seja sempre extremamente educada, prestativa e adote um tom profissional (chame os usuários de Doutor ou Doutora). 
    O seu foco principal é auxiliar farmacêuticos e responder a dúvidas sobre a área da saúde e regulamentações.
    Aviso importante: No final de cada resposta, adicione uma nota corta dizendo que suas respostas têm caráter puramente informativo.
    Você tem 29 anos, é brasileira e tem uma personalidade amigável, mas sempre mantendo a formalidade.
    Você é especialista em legislação farmacêutica, boas práticas de farmácia, ética profissional e temas relacionados à saúde pública.
    Sempre que possível, forneça links oficiais do CFF para aprofundamento.
    Você não deve fornecer informações que não sejam baseadas em fontes oficiais ou que possam ser interpretadas como aconselhamento médico.
    Se a pergunta for sobre um tema que você não tem certeza, seja honesta e diga que não tem certeza, mas que pode ajudar a encontrar a resposta correta.
    Você deve sempre incentivar os usuários a consultarem um profissional de saúde qualificado para questões médicas específicas.
    Evite fornecer informações que possam ser interpretadas como diagnóstico ou tratamento médico.
    Mantenha suas respostas concisas, claras e diretas ao ponto, evitando jargões técnicos desnecessários, mas sem perder a formalidade.
    Você tem formação em Psicologia Junguiana, então pode usar esse conhecimento para oferecer apoio emotional e motivacional aos farmacêuticos, especialmente em momentos de estresse ou desafios profissionais."""

    try:
        response = ai_client.models.generate_content(
            model='gemini-1.5-flash',
            contents=pergunta,
            config={'system_instruction': instrucao}
        )
        return response.text
    except Exception as e:
        print(f"Erro ao chamar o Gemini: {e}")
        return "Desculpe, tive um problema técnico ao processar a sua dúvida. Por favor, tente novamente mais tarde."
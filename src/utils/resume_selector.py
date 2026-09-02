import os
from config.questions import questions_data
from src.utils.logger import logger


def select_resume_path(job_title: str, job_description: str) -> str:
    """
    Analyzes the job title and description to dynamically select the best resume PDF:
    - 'CV_Gabriel_Henrique_Vicentin_Caldeira - I.pdf' for AI / Machine Learning / Data Science / LLM
    - 'CV_Gabriel_Henrique_Vicentin_Caldeira - C.pdf' for Comercial / Vendas / Gestão de Contas
    - 'CV_Gabriel_Henrique_Vicentin_Caldeira - E.pdf' for Engenharia / Processos / Química
    - 'C V _Gabriel_Henrique_Vicentin_Caldeira.pdf' as fallback
    """
    title_lower = (job_title or "").lower()
    desc_lower = (job_description or "").lower()
    full_text = f"{title_lower} {desc_lower}"

    # 1. AI / Tech / Software / Data / Product Keywords
    ai_keywords = [
        "inteligência artificial", "inteligencia artificial", "artificial intelligence",
        "machine learning", "deep learning", "llm", "data science", "cientista de dados",
        "engenheiro de ia", "ai engineer", "prompt engineer", "visão computacional", "nlp",
        "desenvolvedor", "developer", "software engineer", "full stack", "fullstack",
        "frontend", "front-end", "backend", "back-end", "react", "typescript", "python",
        "product manager", "product owner", "tech product", "analytics engineer"
    ]

    # 2. Commercial / E-commerce / Sales / Account Management Keywords
    comercial_keywords = [
        "e-commerce", "ecommerce", "marketplace", "marketplaces", "canal direto", "mercado livre",
        "comercial", "vendas", "vendas técnicas", "vendas tecnicas", "consultor técnico",
        "consultor tecnico", "gerente de contas", "account executive", "account manager",
        "sales", "business development", "desenvolvimento de negócios", "inside sales", "b2b", "pricing"
    ]

    # 3. Engineering / Process / Operations Keywords
    engineering_keywords = [
        "engenharia", "engenheiro", "processos", "process engineer", "químico", "quimica",
        "engenheiro químico", "engenheiro quimico", "qualidade", "produção", "projetos", "planta",
        "planejamento", "pcp", "s&op", "operações", "operacoes", "lean"
    ]

    # Matching priority: Title match first, then full text
    selected_path = None
    category = "Padrão"

    if any(kw in title_lower for kw in comercial_keywords):
        selected_path = questions_data.resume_comercial_path
        category = "Comercial / E-commerce / Vendas"
    elif any(kw in title_lower for kw in ai_keywords):
        selected_path = questions_data.resume_ia_path
        category = "Inteligência Artificial (IA) & Tech"
    elif any(kw in title_lower for kw in engineering_keywords):
        selected_path = questions_data.resume_engenharia_path
        category = "Engenharia"
    elif any(kw in full_text for kw in comercial_keywords):
        selected_path = questions_data.resume_comercial_path
        category = "Comercial / E-commerce / Vendas"
    elif any(kw in full_text for kw in ai_keywords):
        selected_path = questions_data.resume_ia_path
        category = "Inteligência Artificial (IA) & Tech"
    elif any(kw in full_text for kw in engineering_keywords):
        selected_path = questions_data.resume_engenharia_path
        category = "Engenharia"
    else:
        selected_path = questions_data.default_resume_path
        category = "Padrão"

    # Verify if file exists, fallback to default if missing
    if selected_path and os.path.exists(selected_path):
        logger.info(f"-> [CV Selector] Selected '{category}' CV ({os.path.basename(selected_path)}) for job: '{job_title}'")
        return selected_path
    
    logger.info(f"-> [CV Selector] Selected default CV ({os.path.basename(questions_data.default_resume_path)}) for job: '{job_title}'")
    return questions_data.default_resume_path

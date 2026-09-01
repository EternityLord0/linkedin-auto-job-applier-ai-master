#  Copyright (c) 2026 Ajinkya Kardile. All rights reserved.
#
#  This work is licensed under the terms of the MIT license.
#  For a copy, see <https://opensource.org/licenses/MIT>.

from config.schema.question_model import QuestionsModel

# ==========================================
# INSTANTIATE YOUR DATA HERE
# ==========================================
questions_data = QuestionsModel(
    default_resume_path="resume/C V _Gabriel_Henrique_Vicentin_Caldeira.pdf",
    resume_comercial_path="resume/CV_Gabriel_Henrique_Vicentin_Caldeira - C.pdf",
    resume_engenharia_path="resume/CV_Gabriel_Henrique_Vicentin_Caldeira - E.pdf",
    resume_ia_path="resume/CV_Gabriel_Henrique_Vicentin_Caldeira - I.pdf",
    years_of_experience=3,
    additional_months_of_experience=6,
    require_visa="No",
    website="https://polyanalytics.com.br/",
    linkedIn="https://www.linkedin.com/in/gabrielhvcaldeira",
    github="https://github.com/EternityLord0",
    us_citizenship="Other",
    desired_salary=8000,
    current_ctc=8000,
    notice_period=15,
    linkedin_headline="AI Product Builder | React · Supabase · LLMs | E-commerce & Data",
    linkedin_summary="Construo produtos digitais com IA em produção (React, TypeScript, Supabase, LLMs). Supervisor de E-commerce e Inteligência de Dados na The Duracell Company com histórico de crescimento de faturamento (+20% em 2024 e +50% em 2025). Graduado em Engenharia Química pela UFSCar e pós-graduando em Gestão de Projetos pela USP/Esalq.",
    cover_letter="""Prezado(a) Recrutador(a),

Gostaria de apresentar minha candidatura para a oportunidade. Atuo na intersecção entre Desenvolvimento de Produtos com IA, Inteligência de Dados e Operações de Negócio.

Na The Duracell Company, atuo como Supervisor liderando operações e inteligência de marketplaces, estruturando dashboards em Power BI (DAX) e rotinas em Python, contribuindo diretamente para o crescimento de +20% no faturamento em 2024 e mais de 50% em 2025.

Paralelamente, desenvolvo produtos digitais escaláveis em produção com IA (Polyanalytics e Trackerinvest), dominando React, TypeScript, Supabase (Postgres/Edge Functions) e APIs de LLMs (Gemini, Claude, OpenAI). Sou graduado em Engenharia Química pela UFSCar e pós-graduando em Gestão de Projetos (USP/Esalq), com inglês fluente e foco absoluto em entregar soluções eficientes e com impacto real no negócio.

Estou à disposição para agendarmos uma conversa.

Atenciosamente,
Gabriel Henrique Vicentin Caldeira""",
    user_information_all="Gabriel Henrique Vicentin Caldeira. AI Product Builder e Supervisor de E-commerce & Dados na The Duracell Company. Engenheiro Químico (UFSCar) e Pós-graduando em Gestão de Projetos (USP/Esalq). Stack: React, TypeScript, Supabase, Python, LLMs (Gemini/Claude/OpenAI), Power BI, PDCA. Inglês fluente (TOEFL), CNH B ativa, total disponibilidade para trabalho remoto com pretensão salarial de R$ 8.000/mês.",
    recent_employer="The Duracell Company",
    confidence_level="9"
)

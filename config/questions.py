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
    years_of_experience=5,
    additional_months_of_experience=0,
    require_visa="No",
    website="",
    linkedIn="https://www.linkedin.com/",
    github="",
    us_citizenship="Other",
    desired_salary=10000,
    current_ctc=8000,
    notice_period=15,
    linkedin_headline="Engenheiro Químico | Engenharia Comercial & Vendas Técnicas",
    linkedin_summary="Engenheiro Químico com sólida experiência técnica e comercial. Atuação no desenvolvimento de novos negócios, gestão de contas técnicas, consultoria de vendas e otimização de processos industriais.",
    cover_letter="""Prezado(a) Recrutador(a),

Gostaria de demonstrar meu forte interesse na oportunidade oferecida pela empresa. Sou Engenheiro Químico com sólida bagagem na área comercial e de vendas técnicas, aliando conhecimento técnico à gestão de clientes e desenvolvimento de negócios.

Tenho facilidade na comunicação, negociação técnica e entrega de soluções personalizadas que atendem às necessidades industriais e comerciais.

Fico à disposição para agendarmos uma entrevista e apresentar detalhadamente como minhas habilidades podem agregar valor aos objetivos do time.

Atenciosamente.""",
    user_information_all="Engenheiro Químico com experiência comercial, gestão de clientes, vendas técnicas e processos industriais.",
    recent_employer="Engenharia Química / Comercial",
    confidence_level="9"
)

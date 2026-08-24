#  Copyright (c) 2026 Ajinkya Kardile. All rights reserved.
#
#  This work is licensed under the terms of the MIT license.
#  For a copy, see <https://opensource.org/licenses/MIT>.

from config.schema.search_model import SearchModel

# ==========================================
# INSTANTIATE YOUR DATA HERE
# ==========================================
search_data = SearchModel(
    search_terms=[
        "Engenheiro Químico", 
        "Engenharia Química", 
        "Engenheiro de Processos", 
        "Engenheiro de Produção", 
        "Engenheiro", 
        "Engenheiro Comercial", 
        "Engenheiro de Vendas", 
        "Consultor Técnico", 
        "Vendas Técnicas", 
        "Gerente de Contas Técnico",
        "Analista Comercial",
        "Engenheiro de IA",
        "AI Engineer",
        "Inteligência Artificial",
        "Cientista de Dados",
        "Engenheiro de Dados",
        "Machine Learning"
    ],
    search_location="Brasil",
    switch_number=30,
    randomize_search_order=False,
    sort_by="",
    date_posted="Past week", # Filtra vagas da última semana
    salary="",
    easy_apply_only=True,
    experience_level=[],
    job_type=["Full-time"],
    on_site=["Remote", "Hybrid", "On-site"],
    companies=[],
    location=[],
    industry=[],
    job_function=[],
    job_titles=[],
    benefits=[],
    commitments=[],
    under_10_applicants=False,
    in_your_network=False,
    fair_chance_employer=False,
    job_title_bad_words=["Estágio", "Intern", "Jovem Aprendiz", "Director", "VP"],
    job_desc_bad_words=["Sem remuneração", "Voluntário"],
    about_company_bad_words=["Crossover"],
    about_company_good_words=[],
    security_clearance=False,
    did_masters=False,
    current_experience=5
)

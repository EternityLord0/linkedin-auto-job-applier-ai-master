# src/ai/post_generator.py
import os
from config.questions import questions_data
from src.utils.logger import logger


POST_TEMPLATES = [
    {
        "id": "ai_product_builder",
        "title": "Arquitetura de Produtos com IA & LLMs (Engenharia de IA)",
        "banner": "banners/4_AI_Architecture.jpg",
        "content": """Construir soluções com Inteligência Artificial vai muito além de integrar uma API de LLM.

O verdadeiro desafio da Engenharia de IA está em criar sistemas robustos, com baixa latência, respostas estruturadas e total controle sobre o fluxo de dados.

Na prática, o que separa um protótipo de um produto em produção:
🔹 Engenharia de Prompt e Structured Outputs (garantindo JSON determinístico)
🔹 Orquestração inteligente e roteamento entre múltiplos modelos (Gemini, Claude, OpenAI)
🔹 Otimização de contexto e redução drástica de tokens
🔹 Integração sólida com backend escalável (Edge Functions + PostgreSQL)

Trabalhar na intersecção entre Produto, Código e IA é o que permite transformar complexidade técnica em impacto real de negócio.

Como você tem estruturado a arquitetura de IA nos seus projetos hoje?

#InteligenciaArtificial #AIEngineering #LLMs #SoftwareEngineering #Python #ProductBuilder #TechArchitecture"""
    },
    {
        "id": "polyanalytics_fullstack",
        "title": "Polyanalytics: Full Stack Moderno & Dados Escaláveis",
        "banner": "banners/7_Polyanalytics_Network.jpg",
        "content": """Velocidade de desenvolvimento e performance em produção precisam andar juntas.

Ao projetar arquiteturas web modernas (como no Polyanalytics), a escolha da stack é decisiva para entregar valor rápido sem abrir mão da robustez:

⚡ Frontend Reativo: React + TypeScript para interfaces fluidas, previsíveis e componentização limpa.
⚡ Backend Serverless: Supabase com Edge Functions e PostgreSQL para consultas rápidas e segurança em nível de linha (RLS).
⚡ IA Integrada: Pipelines automatizados consumindo modelos de linguagem diretamente nos fluxos de dados.

Menos fricção operacional, mais entrega de produto.

Qual tem sido a sua stack favorita para construir produtos com escala e agilidade?

#ReactJS #TypeScript #Supabase #FullStack #WebDevelopment #PostgreSQL #DataIntelligence #BuildInPublic"""
    },
    {
        "id": "ecommerce_data_growth",
        "title": "Inteligência de Dados no E-commerce (+50% Faturamento)",
        "banner": "banners/3_Data_Waves_Probability.jpg",
        "content": """Dados sem tomada de ação estratégica são apenas gráficos bonitos.

Na liderança de operações de e-commerce e inteligência de marketplaces na The Duracell Company, o foco sempre foi conectar análise quantitativa a resultados práticos no faturamento:

📊 Dashboards executivos em Power BI com modelagem avançada em DAX para visibilidade total de margens e sell-out.
⚙️ Rotinas automatizadas em Python para monitoramento de estoques, precificação dinâmica e auditoria de canais.
🎯 Método PDCA contínuo: hipótese, teste rápido e expansão do que gera tração.

O resultado? Um crescimento consistente de +20% no faturamento em 2024 e mais de 50% em 2025.

Quando Engenharia, Dados e Negócio jogam juntos, a escala é consequência.

#Ecommerce #BusinessIntelligence #PowerBI #Python #DataAnalytics #Liderança #GestaoDeProjetos #Marketplace"""
    },
    {
        "id": "minimalist_tech",
        "title": "Engenharia de Software: Simplicidade, Foco e Execução",
        "banner": "banners/6_Vercel_Minimal.jpg",
        "content": """A melhor tecnologia é aquela que resolve o problema do usuário com a menor complexidade necessária.

Na busca por excelência em software:
1. Menos dependências desnecessárias, mais código legível e manutenível.
2. Arquiteturas modulares que facilitam evolução e testes.
3. Foco obsessivo na experiência do usuário final e na velocidade de resposta.

Engenharia de ponta é sobre disciplina técnica e clareza de propósito.

#SoftwareEngineering #CleanCode #TechLeadership #FullStack #DeveloperExperience #Inovacao"""
    }
]


class PostGenerator:
    def __init__(self, ai_manager=None):
        self.ai_manager = ai_manager

    def get_template_posts(self) -> list[dict]:
        """Returns the curated high-converting post templates."""
        return POST_TEMPLATES

    def generate_custom_post(self, topic: str) -> str:
        """Generates a custom LinkedIn post using Gemini if available."""
        if not self.ai_manager or not self.ai_manager.is_active:
            return f"Post sobre {topic}\n\nCompartilhando aprendizados e insights práticos sobre desenvolvimento, inteligência de dados e tecnologia.\n\n#Tecnologia #Inovação"

        prompt = f"""
Crie uma publicação persuasiva e de alto engajamento para o LinkedIn em Português (Brasil).
O autor é Gabriel Caldeira (AI Product Builder, Desenvolvedor Full Stack React/Supabase/Python e Supervisor de Inteligência de Dados).

Tema específico: {topic}

Estrutura da publicação:
1. Gancho inicial forte (primeiras 2 linhas que prendem a atenção).
2. Desenvolvimento com bullets objetivos e insights práticos (sem clichês corporativos vazios).
3. Conclusão com pergunta provocativa para gerar comentários.
4. 4 a 6 hashtags estratégicas no final.

Retorne APENAS o texto pronto do post, sem explicações adicionais.
"""
        try:
            client = self.ai_manager.client
            if client and hasattr(client, 'model'):
                response = client.model.generate_content(prompt)
                if response.parts:
                    return response.text.strip()
        except Exception as e:
            logger.warning(f"Failed to generate custom post with AI: {e}")

        return POST_TEMPLATES[0]["content"]

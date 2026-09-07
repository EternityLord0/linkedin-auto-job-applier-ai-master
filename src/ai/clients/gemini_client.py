#  Copyright (c) 2026 Ajinkya Kardile. All rights reserved.
#
#  This work is licensed under the terms of the MIT license.
#  For a copy, see <https://opensource.org/licenses/MIT>.

# src/ai/clients/gemini_client.py
import json
import os
import warnings
warnings.filterwarnings("ignore", category=UserWarning)
import google.generativeai as genai

from config.personal import personal_data
from config.questions import questions_data
from config.secrets import secrets_data
from src.ai.prompts import extract_skills_prompt, ai_answer_prompt
from src.utils.logger import logger


class GeminiClient:
    def __init__(self):
        logger.info("Initializing Gemini Client...")

        self.model = None
        self.safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ]

        self.resume_text = self._extract_resume_text()

        api_key = secrets_data.llm_api_key
        if api_key and "YOUR_API_KEY" not in api_key:
            try:
                genai.configure(api_key=api_key)
                self.model = genai.GenerativeModel(secrets_data.llm_model)
                logger.info("---- SUCCESSFULLY CONFIGURED GEMINI ONLINE CLIENT! ----")
                logger.info(f"Using Model: {secrets_data.llm_model}")
            except Exception as e:
                logger.warning(f"Could not configure online Gemini model ({e}). Continuing in Local Fast-Answer mode.")
        else:
            logger.info("---- GEMINI LOCAL FAST-ANSWER MODE ACTIVE (0 Tokens / Offline Rules) ----")

    def _extract_resume_text(self) -> str:
        """Extracts text content from resume PDF if present."""
        resume_path = questions_data.default_resume_path
        if not os.path.exists(resume_path):
            alt_path = os.path.join(os.getcwd(), "resume", "resume.pdf")
            if os.path.exists(alt_path):
                resume_path = alt_path

        if os.path.exists(resume_path):
            try:
                import pypdf
                reader = pypdf.PdfReader(resume_path)
                text = "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
                if text.strip():
                    logger.info(f"Extracted {len(text)} chars from resume: {resume_path}")
                    return text.strip()
            except Exception as e:
                logger.warning(f"Could not extract text from PDF resume '{resume_path}': {e}")
        return ""

    def set_resume_path(self, path: str):
        """Updates the active resume text for Gemini evaluation based on the target job's domain."""
        if path and os.path.exists(path):
            try:
                import pypdf
                reader = pypdf.PdfReader(path)
                text = "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
                if text.strip():
                    self.resume_text = text.strip()
                    logger.info(f"Gemini updated resume context ({len(text)} chars) from: {os.path.basename(path)}")
            except Exception as e:
                logger.warning(f"Could not extract text from PDF resume '{path}': {e}")

    def _get_user_context(self) -> str:
        """Constructs rich user context for Gemini prompts."""
        context_parts = [
            f"Candidate Name: {personal_data.first_name} {personal_data.last_name}",
            f"Location: {personal_data.current_city}, {personal_data.country}",
            f"Headline: {questions_data.linkedin_headline}",
            f"Summary: {questions_data.linkedin_summary}",
            f"Years of Experience: {questions_data.years_of_experience}",
            f"Background Info: {questions_data.user_information_all}",
            f"Target Salary: R$ {questions_data.desired_salary}/month (or equivalent)",
            f"Notice Period: {questions_data.notice_period} days",
            f"Work Preference: Remote",
            f"English Level: Fluent (TOEFL Certified)",
            f"Spanish Level: Advanced",
            f"Driver License (CNH B): Yes",
            f"Field of Degree: Engenharia Química (Chemical Engineering - UFSCar) + Gestão de Projetos (USP/Esalq)",
            f"Key Tech Skills: React, TypeScript, Supabase (PostgreSQL, Edge Functions), Python, LLMs (Gemini, Claude, OpenAI), Power BI (DAX), PDCA, E-commerce & Marketplaces"
        ]
        if self.resume_text:
            context_parts.append(f"\n--- FULL RESUME TEXT ---\n{self.resume_text}")

        return "\n".join(context_parts)

    def extract_skills(self, job_description: str) -> dict | str:
        if not self.model:
            return "Skipped (Offline Mode)"
        logger.info("-- EXTRACTING SKILLS FROM JOB DESCRIPTION [Gemini]")
        prompt = extract_skills_prompt.format(
            job_description) + "\n\nImportant: Respond with ONLY valid JSON, no markdown formatting."

        try:
            response = self.model.generate_content(prompt, safety_settings=self.safety_settings)

            if not response.parts:
                raise ValueError("Response was blocked by safety filters.")

            result = response.text

            # Clean Markdown if Gemini returns it despite instructions
            if result.startswith("```json"):
                result = result[7:]
            if result.endswith("```"):
                result = result[:-3]

            try:
                return json.loads(result.strip())
            except json.JSONDecodeError:
                return result.strip()

        except Exception as e:
            logger.error(f"Gemini skills extraction failed: {e}")
            return "Error extracting skills"

    def evaluate_job_relevance(self, job_title: str, job_description: str) -> bool:
        """Evaluates whether the job is relevant to AI, Software, Product, Data, E-commerce or Engineering."""
        if not self.model:
            return True
        prompt = f"""
Given the candidate's background as an AI Product Builder & E-commerce/Data Supervisor (with full stack skills: React, TypeScript, Supabase, Python, LLMs and engineering background), evaluate if the following job is relevant.
Job Title: {job_title}
Job Description Snippet: {job_description[:1000]}

Respond ONLY with "YES" if it is relevant to:
- Artificial Intelligence, AI Engineering, LLMs, Machine Learning, Data Science, Data Engineering, Analytics
- Software Engineering, Full Stack, Frontend, Backend, React, Python, Web Development
- Product Management, Product Owner, Tech PM
- E-commerce, Marketplace, Digital Operations, Business Intelligence
- Engineering (Process, Operations, Industrial, Planning)

Respond ONLY with "NO" if it is completely unrelated (e.g., Nurse, Medical Doctor, Civil Site Mason, Truck Driver, Security Guard, Accounting Bookkeeper, etc.).
"""
        try:
            response = self.model.generate_content(prompt, safety_settings=self.safety_settings)
            res = response.text.strip().upper()
            return "YES" in res
        except Exception as e:
            logger.warning(f"Failed to evaluate job relevance with Gemini: {e}")
            return True

    def _try_local_fast_answer(self, question: str, question_type: str, options: list | None = None) -> str | None:
        """Local pattern matcher to answer common form questions without API calls (0 tokens)."""
        q_lower = question.lower()

        # =========================================================================
        # 1. Numeric Experience, Duration, Certifications & Counts
        # =========================================================================
        if any(term in q_lower for term in ['certificados', 'certificado', 'certificações', 'certificacoes', 'certificação', 'certificacao', 'certifications', 'certification']):
            if options:
                for opt in options:
                    if any(num in opt for num in ['2', '1', '3', 'Sim', 'Yes']):
                        return opt
                return options[0]
            return "2"

        if any(term in q_lower for term in [
            'quantos anos', 'anos de experiência', 'anos de experiencia', 'tempo de experiência',
            'tempo de experiencia', 'quanto tempo', 'tempo atua', 'tempo você trabalha',
            'tempo voce trabalha', 'tempo de atuação', 'tempo de atuacao', 'how many years',
            'years of experience', 'years do you have', 'how long have you', 'anos você possui',
            'anos você tem', 'anos voce tem', 'anos tem', 'quantos', 'quantas', 'how many',
            'qual a quantidade', 'número de', 'numero de', 'quantidade de'
        ]):
            base_years = questions_data.years_of_experience
            extra_year = 1 if questions_data.additional_months_of_experience >= 6 else 0
            exp_str = str(base_years + extra_year)
            if question_type in ['text', 'textarea'] or not options:
                return exp_str
            elif options:
                for opt in options:
                    if exp_str in opt or any(n in opt for n in ['3', '4', '2', '5', '3-5', '3 a 5', '2-4']):
                        return opt
                return options[0]

        # =========================================================================
        # 2. Salary / Expectativa Salarial / Pretensão / Valor PJ & CLT
        # =========================================================================
        if any(term in q_lower for term in [
            'expectativa salarial', 'expectativa de valor', 'pretensão salarial', 'pretensao salarial',
            'remuneração', 'remuneracao', 'salary', 'salário', 'salario', 'salarial', 'modelo clt',
            'valor clt', 'quanto pretende', 'pretensão para contratação', 'pretensao para contratacao',
            'expected annual salary', 'desired salary', 'hourly rate', 'valor hora', 'valor/hora'
        ]):
            if any(term in q_lower for term in ['valor hora', 'valor/hora', 'por hora', 'taxa horária', 'hourly']):
                return "50"
            if options:
                for opt in options:
                    if any(num in opt for num in ['8000', '8.000', '7000', '9000', '8k']):
                        return opt
                return options[0]
            return "8000"

        # =========================================================================
        # 3. Negative Restrictions (PCD, Visas, Relatives, Prior Employment)
        # =========================================================================
        # Relatives / Parentes
        if any(term in q_lower for term in ['parente', 'parentes', 'family member', 'family members', 'relatives', 'amigo próximo', 'amigo proximo', 'close friend']):
            if options:
                for opt in options:
                    if any(no_term in opt.lower() for no_term in ['não', 'nao', 'no', 'none', 'nenhum']):
                        return opt
            return "No" if "relat" in q_lower or "friend" in q_lower else "Não"

        # Prior employment
        if any(term in q_lower for term in ['já trabalhou', 'ja trabalhou', 'trabalhou anteriormente', 'previously applied', 'applied before', 'worked at this company']):
            if options:
                for opt in options:
                    if any(no_term in opt.lower() for no_term in ['não', 'nao', 'no']):
                        return opt
            return "No" if "previously" in q_lower or "worked" in q_lower else "Não"

        # Disability / PCD
        if any(term in q_lower for term in ['deficiência', 'deficiencia', 'pcd', 'disability', 'handicapped']):
            if any(term in q_lower for term in ['qual o tipo', 'qual sua deficiência', 'qual sua deficiencia', 'tipo de deficiência', 'type of disability']):
                if options:
                    for opt in options:
                        if any(n in opt.lower() for n in ['não se aplica', 'nao se aplica', 'not applicable', 'n/a', 'none', 'nenhuma', 'não sou pcd']):
                            return opt
                return "Not applicable" if "type" in q_lower else "Não se aplica"
            if options:
                for opt in options:
                    if any(no_term in opt.lower() for no_term in ['não', 'nao', 'no', 'não sou pcd', 'i do not have a disability']):
                        return opt
            return "No" if "disabilit" in q_lower else "Não"

        # Visa / Sponsorship
        if any(term in q_lower for term in ['visa', 'patrocínio', 'patrocinio', 'sponsorship', 'require sponsorship', 'work visa']):
            if options:
                for opt in options:
                    if 'não' in opt.lower() or 'no' in opt.lower():
                        return opt
            return "No" if "sponsor" in q_lower or "visa" in q_lower else "Não"

        # =========================================================================
        # 4. Language Proficiency (English, German, Spanish, etc.)
        # =========================================================================
        if any(term in q_lower for term in ['inglês', 'ingles', 'english', 'idioma', 'language', 'alemão', 'alemao', 'german', 'espanhol', 'spanish']):
            if options:
                for prof in ['nativo ou bilíngue', 'native or bilingual', 'fluente', 'fluent', 'avançado', 'advanced', 'professional', 'full professional', 'b2', 'c1', 'c2', 'sim', 'yes']:
                    for opt in options:
                        if prof in opt.lower():
                            return opt
                return options[0]
            return "Fluente" if "inglês" in q_lower or "ingles" in q_lower else "Native or bilingual"

        # =========================================================================
        # 5. Driver License / CNH
        # =========================================================================
        if any(term in q_lower for term in ['cnh', 'carteira nacional de habilitação', 'carteira de motorista', 'driver license', 'habilitação', 'habilitacao']):
            if options:
                for opt in options:
                    if any(yes_term in opt.lower() for yes_term in ['sim', 'yes', 'cnh b', 'categoria b']):
                        return opt
            return "Sim"

        # =========================================================================
        # 6. Affirmative Skill, Tool, API, Certification & Availability Confirmations
        # =========================================================================
        if any(term in q_lower for term in [
            'desenvolveu', 'consegue desenvolver', 'possui experiência', 'possui experiencia',
            'tem experiência', 'tem experiencia', 'possui interesse', 'tem interesse',
            'possui conhecimento', 'tem conhecimento', 'certificação', 'certificacao',
            'certification', 'certified', 'atuar como clt', 'atuar como pj', 'able to work',
            'work as pj', 'work as clt', 'remoto', 'remote', 'início imediato', 'inicio imediato',
            'trabalha com', 'trabalhou com', 'worked with', 'have you worked', 'do you have experience',
            'are you able', 'willing to', 'disponibilidade'
        ]):
            if options:
                for opt in options:
                    if any(yes_term in opt.lower() for yes_term in ['sim', 'yes', 'tenho', 'possuo', 'concordo', 'agree', 'true', 'i do', 'i have']):
                        return opt
            return "Yes" if any(w in q_lower for w in ['have', 'do you', 'are you', 'able', 'remote']) else "Sim"

        # =========================================================================
        # 7. Education / Degree
        # =========================================================================
        if any(term in q_lower for term in ['engenheiro', 'engenharia', 'superior completo', 'graduação', 'graduacao', 'bacharelado', 'ensino superior', 'pos-graduação', 'pós-graduação', 'mba']):
            if options:
                for opt in options:
                    if 'sim' in opt.lower() or 'yes' in opt.lower() or 'completo' in opt.lower():
                        return opt
            return "Sim"

        # =========================================================================
        # 8. Demographics & Accessibility
        # =========================================================================
        if any(term in q_lower for term in ['acessibilidade', 'accessibility']):
            if options:
                for opt in options:
                    if any(no_need in opt.lower() for no_need in ['não necessito', 'nao necessito', 'não preciso', 'do not require', 'nenhuma', 'não', 'no']):
                        return opt
            return "Não necessito de nenhuma acessibilidade"

        if any(term in q_lower for term in ['identidade de gênero', 'identidade de genero', 'gender identity', 'gênero?', 'genero?', 'gender?', 'sexo?']):
            if options:
                for opt in options:
                    if any(m in opt.lower() for m in ['cisgender man', 'homem cisgênero', 'homem cis', 'homem', 'man', 'masculino', 'male']):
                        return opt
            return "Homem Cisgênero"

        if any(term in q_lower for term in ['cor/raça', 'cor ou raça', 'autodeclara sua cor', 'color/race', 'etnia', 'ethnicity', 'raça', 'raca', 'race']):
            if options:
                for opt in options:
                    if any(w in opt.lower() for w in ['white', 'branca', 'branco']):
                        return opt
            return "Branca"

        if any(term in q_lower for term in ['name of the company where you work', 'empresa em que você trabalha', 'empresa atual', 'current company']):
            return "The Duracell Company"

        return None

    def answer_question(self, question: str, question_type: str, job_description: str,
                        options: list | None = None) -> str:
        # Check local rule engine first (0 tokens)
        local_ans = self._try_local_fast_answer(question, question_type, options)
        if local_ans:
            logger.info(f"-- [LOCAL FAST-ANSWER (0 tokens)] '{question}' ==> '{local_ans}'")
            return local_ans

        if not self.model:
            return ""

        logger.info(f"-- ANSWERING QUESTION using AI: {question}")

        user_info_str = self._get_user_context()
        prompt = ai_answer_prompt.format(user_info_str, question)

        # Inject Options Logic
        if options and (question_type in ['select', 'radio', 'single_select', 'multiple_select']):
            options_str = "OPTIONS:\n" + "\n".join([f"- {opt}" for opt in options])
            prompt += f"\n\n{options_str}"
            if question_type in ['select', 'radio', 'single_select']:
                prompt += "\n\nPlease select exactly ONE option from the list above. Return ONLY the exact text of the option."
            else:
                prompt += "\n\nYou may select MULTIPLE options from the list above if appropriate."

        if job_description and job_description != "Unknown":
            prompt += f"\n\nJOB DESCRIPTION:\n{job_description[:1500]}"

        try:
            response = self.model.generate_content(prompt, safety_settings=self.safety_settings)
            if not response.parts:
                raise ValueError("Response blocked by Gemini safety filters.")

            answer = response.text.strip()
            logger.debug(f"AI Response: {answer}")
            return answer
        except Exception as e:
            logger.error(f"Gemini failed to answer question '{question}': {e}")
            return ""

    def close(self):
        # Gemini client via google.generativeai does not require an explicit close
        pass


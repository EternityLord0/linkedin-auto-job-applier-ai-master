#  Copyright (c) 2026 Ajinkya Kardile. All rights reserved.
#
#  This work is licensed under the terms of the MIT license.
#  For a copy, see <https://opensource.org/licenses/MIT>.

# src/ai/clients/gemini_client.py
import json
import os

import google.generativeai as genai

from config.personal import personal_data
from config.questions import questions_data
from config.secrets import secrets_data
from src.ai.prompts import extract_skills_prompt, ai_answer_prompt
from src.utils.logger import logger


class GeminiClient:
    def __init__(self):
        logger.info("Initializing Gemini Client...")

        if not secrets_data.llm_api_key or "YOUR_API_KEY" in secrets_data.llm_api_key:
            raise ValueError("Gemini API key is not set. Please configure it in config/secrets.py")

        genai.configure(api_key=secrets_data.llm_api_key)
        self.model = genai.GenerativeModel(secrets_data.llm_model)

        # Define relaxed safety settings for job applications to prevent false positives
        self.safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ]

        self.resume_text = self._extract_resume_text()

        logger.info("---- SUCCESSFULLY CONFIGURED GEMINI CLIENT! ----")
        logger.info(f"Using Model: {secrets_data.llm_model}")

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
            f"Driver License (CNH B): Yes",
            f"Willingness to Travel: Yes",
            f"Field of Degree: Engenharia Química (Chemical Engineering)",
            f"Commercial / Technical Sales Experience: Yes"
        ]
        if self.resume_text:
            context_parts.append(f"\n--- FULL RESUME TEXT ---\n{self.resume_text}")

        return "\n".join(context_parts)

    def extract_skills(self, job_description: str) -> dict | str:
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
        """Evaluates whether the job is relevant to Chemical Engineering or Commercial/Technical Sales."""
        prompt = f"""
Given the candidate's background as a Chemical Engineer with Commercial/Technical Sales experience, evaluate if the following job is relevant.
Job Title: {job_title}
Job Description Snippet: {job_description[:1000]}

Respond ONLY with "YES" if it is relevant to Chemical Engineering, Process Engineering, Technical Sales, Commercial Management, or Industrial Sales.
Respond ONLY with "NO" if it is completely unrelated (e.g., Software Development, Civil Construction Site Manager, Nurse, Accounting, etc.).
"""
        try:
            response = self.model.generate_content(prompt, safety_settings=self.safety_settings)
            res = response.text.strip().upper()
            return "YES" in res
        except Exception as e:
            logger.warning(f"Failed to evaluate job relevance with Gemini: {e}")
            return True

    def _try_local_fast_answer(self, question: str, question_type: str, options: list = None) -> str | None:
        """Local pattern matcher to answer common form questions without API calls (0 tokens)."""
        q_lower = question.lower()

        # 1. Driver License / CNH
        if any(term in q_lower for term in ['cnh', 'carteira nacional de habilitação', 'carteira de motorista', 'driver license']):
            if options:
                for opt in options:
                    if any(yes_term in opt.lower() for yes_term in ['sim', 'yes', 'cnh b', 'categoria b']):
                        return opt
            return "Sim"

        # 2. Availability / Immediate Start / Travel
        if any(term in q_lower for term in ['início imediato', 'inicio imediato', 'disponibilidade para início', 'disponibilidade de início']):
            if options:
                for opt in options:
                    if 'sim' in opt.lower() or 'yes' in opt.lower() or 'imediato' in opt.lower():
                        return opt
            return "Sim"

        if any(term in q_lower for term in ['viagem', 'viagens', 'deslocar', 'deslocamento', 'willingness to travel', 'viajar', 'disponibilidade para viajar']):
            if options:
                for opt in options:
                    if 'sim' in opt.lower() or 'yes' in opt.lower():
                        return opt
            return "Sim"

        # 3. Freelancer / PJ / Contract
        if any(term in q_lower for term in ['freelancer', 'autônomo', 'autonomo', 'pessoa jurídica', 'pj']):
            if options:
                for opt in options:
                    if 'sim' in opt.lower() or 'yes' in opt.lower():
                        return opt
            return "Sim"

        # 4. Visa / Work Authorization
        if any(term in q_lower for term in ['visa', 'patrocínio', 'patrocinio', 'sponsorship']):
            if options:
                for opt in options:
                    if 'não' in opt.lower() or 'no' in opt.lower():
                        return opt
            return "Não"

        # 5. Salary / Remuneração
        if any(term in q_lower for term in ['pretensão salarial', 'pretensao salarial', 'salário desejado', 'salario desejado']):
            return str(questions_data.desired_salary)

        # 6. Education / Degree in Chemical Engineering / Chemistry / Pharmacy / Related areas
        if any(term in q_lower for term in [
            'engenheiro químico', 'engenheiro quimico', 'técnico em química', 'tecnico em quimica',
            'engenharia química', 'engenharia quimica', 'química', 'quimica', 'farmácia', 'farmacia',
            'graduação', 'graduacao', 'ensino superior', 'superior completo', 'bacharelado'
        ]):
            if options:
                for opt in options:
                    if 'sim' in opt.lower() or 'yes' in opt.lower():
                        return opt
            return "Sim"

        return None

    def answer_question(self, question: str, question_type: str, job_description: str,
                        options: list = None) -> str:
        # Check local rule engine first (0 tokens)
        local_ans = self._try_local_fast_answer(question, question_type, options)
        if local_ans:
            logger.info(f"-- [LOCAL FAST-ANSWER (0 tokens)] '{question}' ==> '{local_ans}'")
            return local_ans

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


#  Copyright (c) 2026 Ajinkya Kardile. All rights reserved.
#
#  This work is licensed under the terms of the MIT license.
#  For a copy, see <https://opensource.org/licenses/MIT>.

# src/core/question_handlers/radio_handler.py

from selenium.webdriver.common.by import By

from config.personal import personal_data
from config.questions import questions_data
from config.settings import settings_data
from src.core.question_handlers.base_handler import BaseQuestionHandler
from src.data.question_cache import question_cache
from src.utils.logger import logger


class RadioHandler(BaseQuestionHandler):
    def __init__(self, scraper, ai_manager=None):
        super().__init__(scraper,ai_manager)
        self.ai_manager = ai_manager

    def can_handle(self, question_element):
        return self.scraper.interactor.try_xpath(
            './/fieldset[@data-test-form-builder-radio-button-form-component="true"]',
            click=False,
            element=question_element
        )

    @staticmethod
    def normalize_text(text: str) -> str:
        """
        Normalize text for safer fuzzy matching.
        Removes punctuation and lowercases.
        """
        if not text:
            return ""

        return ''.join(
            c.lower()
            for c in text.strip()
            if c.isalnum() or c.isspace()
        ).strip()

    def safe_click_label(self, label_element):
        """
        Safely click a radio label element.
        """
        try:
            self.scraper.actions.move_to_element(label_element).click().perform()
            return True
        except Exception as e:
            logger.warning(f"Failed clicking radio label: {e}")
            return False

    def handle(self, question_element, job_description):
        radio_fieldset = self.scraper.interactor.try_xpath(
            './/fieldset[@data-test-form-builder-radio-button-form-component="true"]',
            click=False,
            element=question_element
        )

        label_element = self.scraper.interactor.try_xpath(
            './/span[@data-test-form-builder-radio-button-form-component__title]',
            click=False,
            element=radio_fieldset
        )

        try:
            hidden = label_element.find_element(By.CLASS_NAME, "visually-hidden")
            label_text = hidden.text if hidden else label_element.text
        except Exception:
            label_text = label_element.text if label_element else "Unknown"

        label_text = label_text.strip()
        label_lower = label_text.lower()

        options = radio_fieldset.find_elements(By.TAG_NAME, 'input')

        option_data = []
        prev_answer = None

        # Build option metadata
        for option in options:
            opt_id = option.get_attribute("id")

            opt_label = self.scraper.interactor.try_xpath(
                f'.//label[@for="{opt_id}"]',
                click=False,
                element=radio_fieldset
            )

            label_str = opt_label.text.strip() if opt_label else "Unknown"

            option_data.append({
                "input": option,
                "label": opt_label,
                "text": label_str
            })

            if option.is_selected():
                prev_answer = label_str

        options_labels = [opt["text"] for opt in option_data]

        logger.info(f"Radio Question: {label_text}")
        logger.info(f"Options: {options_labels}")

        answer = ""

        # Skip if already answered and overwrite disabled
        if not settings_data.overwrite_previous_answers and prev_answer:
            return (label_text, prev_answer, "radio")

        # 0. Check Question Cache (0 Tokens & Instant)
        cached_opt = question_cache.get_answer(label_text, options_labels)
        if cached_opt:
            answer = cached_opt

        # ==========================================================
        # Deterministic Rules (PT & EN)
        # ==========================================================

        # 1. Negative Restrictions (PCD, Visas, Relatives, Prior Employment)
        if any(term in label_lower for term in ['disability', 'handicapped', 'deficiência', 'deficiencia', 'pcd']):
            answer = personal_data.disability_status

        elif any(term in label_lower for term in ['sponsorship', 'visa', 'visto', 'patrocínio', 'patrocinio']):
            answer = questions_data.require_visa

        elif any(term in label_lower for term in ['relationship', 'relatives', 'parentes', 'family members', 'parente']):
            answer = "Não" if "parent" in label_lower or "defic" in label_lower else "No"

        elif any(term in label_lower for term in ['previously applied', 'applied before', 'já trabalhou', 'ja trabalhou', 'worked at']):
            answer = "Não" if "já" in label_lower or "trabalhou" in label_lower else "No"

        # 2. Driver License / CNH
        elif any(term in label_lower for term in ['cnh', 'habilitação', 'habilitacao', 'carteira de motorista', 'driver license']):
            answer = "Sim"

        # 3. Work Authorization & Citizenship
        elif any(word in label_lower for word in ['authorized', 'legally authorized', 'eligible to work', 'work authorization', 'autorizado a trabalhar']):
            answer = "Sim" if "autorizado" in label_lower or "trabalhar" in label_lower else "Yes"

        elif 'citizenship' in label_lower or 'employment eligibility' in label_lower:
            answer = questions_data.us_citizenship

        elif 'veteran' in label_lower or 'protected veteran' in label_lower:
            answer = personal_data.veteran_status

        # 4. Work Models / Availability (PJ, CLT, Remote, Relocation, Immediate Start, Residence, Setup)
        elif any(word in label_lower for word in ['live in brazil', 'reside no brasil', 'mora no brasil', 'reside in brazil', 'localizado no brasil', 'own computer', 'work setup', 'setup', 'computador próprio', 'computador proprio', 'equipamento']):
            answer = "Sim" if any(w in label_lower for w in ['brasil', 'mora', 'reside', 'computador', 'equipamento']) else "Yes"

        elif any(word in label_lower for word in ['clt', 'pj', 'pessoa jurídica', 'pessoa juridica', 'remoto', 'remote', 'híbrido', 'hibrido', 'disponibilidade', 'início imediato', 'inicio imediato', 'full-time', 'tempo integral']):
            answer = "Sim" if any(w in label_lower for w in ['clt', 'pj', 'remoto', 'disponibilidade', 'início']) else "Yes"

        elif any(word in label_lower for word in ['relocate', 'relocation', 'mudança', 'mudanca']):
            answer = getattr(questions_data, "open_to_relocate", "Yes")

        elif any(word in label_lower for word in ['background check', 'drug test', 'antecedentes']):
            answer = "Sim" if "antecedentes" in label_lower else "Yes"

        elif any(word in label_lower for word in ['nda', 'confidentiality', 'non compete', 'non-compete', 'sigilo']):
            answer = "Sim" if "sigilo" in label_lower else "Yes"

        # 5. Skills & Experience Confirmation ("Você tem experiência com...", "Desenvolveu...", "AI tools", "English", etc.)
        elif any(word in label_lower for word in ['experiência', 'experiencia', 'experience', 'conhecimento', 'desenvolveu', 'atuou', 'trabalha com', 'have you', 'do you have', 'proficiência', 'proficiencia', 'ai tools', 'chatgpt', 'claude', 'copilot', 'english', 'inglês', 'ingles', 'pipelines', 'sql', 'python', 'analytics', 'resume in english', 'cv in english', 'currículo em inglês', 'curriculo em ingles']):
            answer = "Sim" if any(w in label_lower for w in ['experiência', 'experiencia', 'conhecimento', 'desenvolveu', 'atuou', 'inglês', 'ingles']) else "Yes"

        selected = False

        # ==========================================================
        # Exact Match
        # ==========================================================

        if answer:
            normalized_answer = self.normalize_text(answer)

            for option in option_data:
                normalized_option = self.normalize_text(option["text"])

                if normalized_answer == normalized_option:
                    if self.safe_click_label(option["label"]):
                        answer = option["text"]
                        selected = True
                        break

        # ==========================================================
        # Fuzzy Match
        # ==========================================================

        if not selected and answer:
            normalized_answer = self.normalize_text(answer)

            for option in option_data:
                normalized_option = self.normalize_text(option["text"])

                if (
                    normalized_answer in normalized_option
                    or normalized_option in normalized_answer
                ):
                    if self.safe_click_label(option["label"]):
                        answer = option["text"]
                        selected = True
                        break

        # ==========================================================
        # AI Fallback
        # ==========================================================

        if not selected and self.ai_manager:
            try:
                logger.info(f"Trying AI for radio question: {label_text}")

                ai_answer = self.ai_manager.get_answer(
                    question=label_text,
                    question_type="radio",
                    job_description=job_description,
                    options=options_labels
                )

                logger.info(f"AI suggested: {ai_answer}")

                if ai_answer:
                    normalized_ai = self.normalize_text(ai_answer)

                    # Exact AI Match
                    for option in option_data:
                        normalized_option = self.normalize_text(option["text"])

                        if normalized_ai == normalized_option:
                            if self.safe_click_label(option["label"]):
                                answer = option["text"]
                                selected = True
                                break

                    # Fuzzy AI Match
                    if not selected:
                        for option in option_data:
                            normalized_option = self.normalize_text(option["text"])

                            if (
                                normalized_ai in normalized_option
                                or normalized_option in normalized_ai
                            ):
                                if self.safe_click_label(option["label"]):
                                    answer = option["text"]
                                    selected = True
                                    break

            except Exception as e:
                logger.error(f"AI radio answering failed: {e}")

        # ==========================================================
        # Smart Heuristic Fallback (Affirmative vs Negative)
        # ==========================================================

        if not selected:
            # If question is about skills, experience, tools, availability -> Affirmative
            is_skill_or_avail = any(term in label_lower for term in [
                'experiência', 'experiencia', 'experience', 'skill', 'conhecimento',
                'desenvolveu', 'trabalhou', 'trabalha', 'api', 'python', 'sql', 'react',
                'aws', 'databricks', 'cloud', 'clt', 'pj', 'remoto', 'disponibilidade',
                'inglês', 'ingles', 'english', 'cnh', 'graduação', 'graduacao'
            ])

            if is_skill_or_avail:
                affirmative_options = ["sim", "yes", "tenho", "possuo", "concordo", "agree", "true", "i do", "i have", "fluente", "avançado", "nativo"]
                for aff in affirmative_options:
                    for option in option_data:
                        if aff in option["text"].lower():
                            if self.safe_click_label(option["label"]):
                                answer = option["text"]
                                selected = True
                                logger.info(f"Smart affirmative heuristic selected: '{answer}' for question: '{label_text}'")
                                break
                    if selected:
                        break

            # If question is about restrictions (disability, sponsorship, relatives) -> Negative
            if not selected:
                is_restriction = any(term in label_lower for term in [
                    'deficiência', 'deficiencia', 'pcd', 'disability', 'sponsorship',
                    'visto', 'visa', 'relatives', 'parentes', 'processo'
                ])
                if is_restriction:
                    negative_options = ["não", "nao", "no", "não se aplica", "nao se aplica", "not applicable", "decline", "prefer not to say"]
                    for neg in negative_options:
                        for option in option_data:
                            if neg in option["text"].lower():
                                if self.safe_click_label(option["label"]):
                                    answer = option["text"]
                                    selected = True
                                    logger.info(f"Smart negative heuristic selected: '{answer}' for question: '{label_text}'")
                                    break
                        if selected:
                            break

        # ==========================================================
        # Absolute Final Fallback
        # ==========================================================

        if not selected and option_data:
            logger.warning(
                f"Using final fallback option for question: '{label_text}'"
            )

            try:
                self.safe_click_label(option_data[0]["label"])
                answer = option_data[0]["text"]
            except Exception as e:
                logger.error(f"Final fallback failed: {e}")

        # ==========================================================
        # Re-check Selected Answer
        # ==========================================================

        final_answer = answer if answer else "Unknown"

        for option in option_data:
            try:
                inp_selected = option["input"].is_selected()
                attr_checked = option["input"].get_attribute("checked") in ["true", True, "checked"]
                label_checked = option["label"].get_attribute("aria-checked") == "true" or "checked" in (option["label"].get_attribute("class") or "").lower()
                if inp_selected or attr_checked or label_checked:
                    final_answer = option["text"]
                    break
            except Exception:
                continue

        if final_answer and final_answer != "Unknown":
            question_cache.save_answer(label_text, final_answer)

        logger.info(
            f"Answered Radio Question -> "
            f"Question: '{label_text}' | "
            f"Answer: '{final_answer}'"
        )

        return (label_text, final_answer, "radio")
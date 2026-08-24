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

        # ==========================================================
        # Deterministic Rules
        # ==========================================================

        if 'citizenship' in label_lower or 'employment eligibility' in label_lower:
            answer = questions_data.us_citizenship

        elif 'veteran' in label_lower or 'protected veteran' in label_lower:
            answer = personal_data.veteran_status

        elif 'disability' in label_lower or 'handicapped' in label_lower:
            answer = personal_data.disability_status

        elif 'sponsorship' in label_lower or 'visa' in label_lower:
            answer = questions_data.require_visa

        elif 'relationship' in label_lower:
            answer = "No"

        elif 'previously applied' in label_lower or 'applied before' in label_lower:
            answer = "No"

        elif any(word in label_lower for word in [
            'authorized',
            'legally authorized',
            'eligible to work',
            'work authorization'
        ]):
            answer = "Yes"

        elif any(word in label_lower for word in [
            'relocate',
            'relocation'
        ]):
            answer = getattr(questions_data, "open_to_relocate", "Yes")

        elif any(word in label_lower for word in [
            'remote',
            'hybrid',
            'onsite',
            'on-site',
            'work model'
        ]):
            answer = getattr(questions_data, "work_preference", "")

        elif any(word in label_lower for word in [
            'background check',
            'drug test'
        ]):
            answer = "Yes"

        elif any(word in label_lower for word in [
            'nda',
            'confidentiality',
            'non compete',
            'non-compete'
        ]):
            answer = "Yes"

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
        # Safe Fallback
        # ==========================================================

        if not selected:
            logger.warning(
                f"No confident answer found for radio question: '{label_text}'"
            )

            safe_options = [
                "No",
                "Decline",
                "Prefer not to say",
                "Prefer not to answer",
                "I do not wish to answer"
            ]

            for safe in safe_options:
                normalized_safe = self.normalize_text(safe)

                for option in option_data:
                    normalized_option = self.normalize_text(option["text"])

                    if normalized_safe in normalized_option:
                        if self.safe_click_label(option["label"]):
                            answer = option["text"]
                            selected = True
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

        final_answer = "Unknown"

        for option in option_data:
            try:
                if option["input"].is_selected():
                    final_answer = option["text"]
                    break
            except Exception:
                continue

        logger.info(
            f"Answered Radio Question -> "
            f"Question: '{label_text}' | "
            f"Answer: '{final_answer}'"
        )

        return (label_text, final_answer, "radio")
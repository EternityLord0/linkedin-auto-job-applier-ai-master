#  Copyright (c) 2026 Ajinkya Kardile. All rights reserved.
#
#  This work is licensed under the terms of the MIT license.
#  For a copy, see <https://opensource.org/licenses/MIT>.

# src/core/job_applier.py
import os
import time

import pyautogui
from selenium.webdriver.common.by import By

from config.questions import questions_data
from config.settings import settings_data
from src.core.question_handlers.checkbox_handler import CheckboxHandler
from src.core.question_handlers.radio_handler import RadioHandler
from src.core.question_handlers.select_handler import SelectHandler
from src.core.question_handlers.text_handler import TextHandler
from src.utils.logger import logger


class JobApplier:
    def __init__(self, scraper, ai_manager, csv_manager):
        self.scraper = scraper
        self.ai = ai_manager
        self.csv = csv_manager
        self.pause_before_submit = settings_data.pause_before_submit

        self.handlers = [
            SelectHandler(scraper, ai_manager),
            RadioHandler(scraper, ai_manager),
            TextHandler(scraper, ai_manager),
            CheckboxHandler(scraper, ai_manager)
        ]

    def execute_easy_apply_flow(self, job_id, job_description, resume_path=None):
        """Navigates through the Easy Apply modal pages."""
        try:
            modal = self.scraper.interactor.try_xpath('//div[contains(@class, "jobs-easy-apply-modal")] | //div[contains(@class, "easy-apply-modal")] | //div[contains(@class, "jobs-easy-apply-content")] | //div[contains(@id, "artdeco-modal")] | //div[@role="dialog"]', click=False)
            if not modal:
                logger.warning("Could not find Easy Apply modal dialog element. Aborting application flow.")
                return False

            for next_text in ["Next", "Avançar", "Próximo", "Continuar", "Seguinte"]:
                if self.scraper.interactor.wait_span_click(next_text, timeout=0.8):
                    break

            errored = ""
            questions_list = set()
            next_button = True
            next_counter = 0
            uploaded = False
            target_resume = resume_path if (resume_path and os.path.exists(resume_path)) else questions_data.default_resume_path
            while next_button:
                next_counter += 1

                # If stuck repeating the same step, attempt active auto-recovery on error fields
                if next_counter > 3:
                    try:
                        error_feedbacks = modal.find_elements(By.XPATH, ".//*[contains(@class, 'artdeco-inline-feedback--error') or contains(@class, 'error') or @aria-invalid='true']")
                        if error_feedbacks:
                            logger.warning(f"Detected {len(error_feedbacks)} form validation errors. Applying auto-recovery...")
                            # Re-run all handlers with force to fix the invalid fields
                            for handler in self.handlers:
                                for q_el in self._get_question_elements(modal):
                                    if handler.can_handle(q_el):
                                        try:
                                            handler.handle(q_el, job_description)
                                        except Exception:
                                            pass
                    except Exception as e:
                        logger.debug(f"Error recovery attempt: {e}")

                if next_counter > 7:
                    logger.error("Form could not progress past current page after 7 attempts. Safely skipping this application.")
                    if questions_list:
                        logger.error(f"Questions on stuck page: {questions_list}")
                    self.scraper.interactor.save_screenshot(job_id, "Failed at questions")
                    errored = "stuck"
                    return False

                # 1. Answer questions on the current page
                new_questions = self.answer_questions(modal, job_description)
                questions_list.update(new_questions)

                # Safety sweep: ensure no visible input field is left blank on the current step
                try:
                    empty_inputs = modal.find_elements(By.XPATH, ".//input[(@type='text' or @type='number' or not(@type)) and (@value='' or not(@value))]")
                    for empty_inp in empty_inputs:
                        if empty_inp.is_displayed():
                            val = "4" if empty_inp.get_attribute("type") == "number" else "Sim"
                            try:
                                empty_inp.click()
                                empty_inp.send_keys(val)
                            except Exception:
                                pass
                except Exception:
                    pass

                # 2. Upload resume if prompted
                if settings_data.uploadNewResume and not uploaded:
                    uploaded, _ = self._upload_resume(modal, target_resume)

                # 3. Navigate forward (Try Review first, then Next)
                review_btn = False
                for rev_text in ["Review", "Revisar", "Examinar", "Verificar"]:
                    if self.scraper.interactor.wait_span_click(rev_text, timeout=1, click=True):
                        review_btn = True
                        break

                if review_btn:
                    next_button = False  # Successfully clicked Review, end loop
                else:
                    next_btn = False
                    for nxt_text in ["Next", "Avançar", "Próximo", "Seguinte", "Continuar"]:
                        if self.scraper.interactor.wait_span_click(nxt_text, timeout=1, click=True):
                            next_btn = True
                            break
                    if not next_btn:
                        next_button = False  # Neither Review nor Next found, end loop

                self.scraper.interactor.sleep_buffer(1, 2)

            # 4. Final Screen Actions & Scroll to Bottom
            self._handle_follow_company(modal, settings_data.follow_companies)
            try:
                # Scroll modal content to bottom so submit button and disclosures become interactable
                scrollable_areas = modal.find_elements(By.XPATH, ".//div[contains(@class, 'jobs-easy-apply-modal__content') or contains(@class, 'artdeco-modal__content') or contains(@tabindex, '0')]")
                for area in scrollable_areas:
                    self.scraper.driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight;", area)
                time.sleep(1.0)
            except Exception:
                pass

            # --------
            if errored != "stuck" and self.pause_before_submit:
                decision = pyautogui.confirm(
                    '1. Please verify your information.\n2. If you edited something, please return to this final screen.\n3. DO NOT CLICK "Submit Application".\n\n\n\n\nYou can turn off "Pause before submit" setting in config.py\nTo TEMPORARILY disable pausing, click "Disable Pause"',
                    "Confirm your information", ["Enable Auto-Submit", "Discard Application", "Submit Application"])
                if decision == "Discard Application": raise Exception("Job application discarded by user!")
                self.pause_before_submit = False if "Enable Auto-Submit" == decision else True

            ## 5. Submit Application (Multi-strategy detection for PT & EN)
            submit_btn = False
            submit_labels = [
                "Submit application", "Submit", "Enviar candidatura", "Enviar",
                "Enviar inscrição", "Concluir candidatura", "Concluir inscrição",
                "Avançar para a candidatura", "Candidatar-se", "Fazer candidatura"
            ]

            # Strategy A: Span text matching
            for label in submit_labels:
                if self.scraper.interactor.wait_span_click(label, timeout=2.0, scroll_top=False):
                    submit_btn = True
                    logger.info(f"Successfully clicked submit button via span: '{label}'")
                    break

            # Strategy B: Button by aria-label
            if not submit_btn:
                try:
                    aria_buttons = modal.find_elements(
                        By.XPATH,
                        ".//button[contains(@aria-label, 'Submit') or contains(@aria-label, 'Enviar') or contains(@aria-label, 'Concluir') or contains(@aria-label, 'candidatura')]"
                    )
                    for btn in aria_buttons:
                        if btn.is_displayed():
                            self.scraper.driver.execute_script("arguments[0].click();", btn)
                            submit_btn = True
                            logger.info(f"Clicked submit button via aria-label: '{btn.get_attribute('aria-label')}'")
                            break
                except Exception as e:
                    logger.debug(f"Aria-label submit check: {e}")

            # Strategy C: Primary action buttons in modal footer / actionbar
            if not submit_btn:
                try:
                    footer_buttons = modal.find_elements(
                        By.XPATH,
                        ".//div[contains(@class, 'artdeco-modal__actionbar')]//button | .//div[contains(@class, 'display-flex justify-flex-end')]//button | .//footer//button | .//button[contains(@class, 'artdeco-button--primary')]"
                    )
                    for btn in footer_buttons:
                        btn_txt = btn.text.strip().lower()
                        btn_aria = (btn.get_attribute("aria-label") or "").lower()
                        combined = btn_txt + " " + btn_aria
                        if any(term in combined for term in ['submit', 'enviar', 'concluir', 'candidat', 'inscrição', 'inscricao', 'aplicar']):
                            self.scraper.driver.execute_script("arguments[0].click();", btn)
                            submit_btn = True
                            logger.info(f"Clicked primary submit button via actionbar/footer: '{btn_txt or btn_aria}'")
                            break
                except Exception as e:
                    logger.debug(f"Actionbar primary button check: {e}")

            if submit_btn or (errored != "stuck" and self.pause_before_submit and "Yes" in pyautogui.confirm(
                    "You submitted the application, didn't you ??", "Failed to find Submit Application!",
                    ["Yes", "No"])):
                time.sleep(2.0)
                self._handle_post_submit_popup()
                for done_text in ["Done", "Concluído", "Concluir", "Fechar", "Dismiss"]:
                    self.scraper.interactor.wait_span_click(done_text, timeout=1.5)
                return questions_list
            else:
                logger.warning("Since Submit Application failed, discarding the job application...")
            return False

        except Exception as e:
            logger.error(f"Error during Easy Apply flow: {e}")
            return False

    def answer_questions(self, modal, job_description):
        from selenium.common.exceptions import StaleElementReferenceException
        questions_list = set()
        num_questions = len(modal.find_elements(By.XPATH, ".//div[@data-test-form-element]"))
        for i in range(num_questions):
            try:
                current_questions = modal.find_elements(By.XPATH, ".//div[@data-test-form-element]")
                if i >= len(current_questions):
                    break
                question = current_questions[i]

                handled = False
                for handler in self.handlers:
                    if handler.can_handle(question):
                        label, answer, q_type = handler.handle(question, job_description)
                        logger.info(f'Question: {label} ==> {answer}')
                        questions_list.add((label, answer, q_type))
                        handled = True
                        break

                if not handled:
                    logger.warning(f"Encountered an unknown question type at index {i}! Skipping.")

            except StaleElementReferenceException:
                logger.warning(f"Question at index {i} went stale. LinkedIn re-rendered the DOM. Retrying or skipping.")
                continue  # Safely continue to the next question instead of crashing
            except Exception as e:
                logger.error(f"Unexpected error answering question at index {i}: {e}")

        return questions_list

    def _upload_resume(self, modal, resume_path: str) -> tuple[bool, str]:
        import os
        import time
        from selenium.webdriver.common.by import By

        try:
            # 1. Check if a resume is already uploaded or pre-selected
            # LinkedIn renders a "Remove" button or a "ui-attachment" card when a document is active.
            existing_resume = modal.find_elements(
                By.XPATH,
                ".//button[contains(@aria-label, 'Remove')] | .//div[contains(@class, 'ui-attachment')]"
            )

            # Check if a previously saved resume radio button is selected
            selected_radio = modal.find_elements(
                By.XPATH,
                ".//input[@type='radio' and @checked]"
            )

            if existing_resume or selected_radio:
                logger.info("A resume is already attached or pre-selected. Skipping upload.")
                return True, "Previous resume"

            # 2. If no resume is present, attempt to upload
            file_input = modal.find_elements(By.XPATH, ".//input[@type='file']")

            if file_input:
                file_input[0].send_keys(os.path.abspath(resume_path))
                logger.info(f"Successfully uploaded new resume from: {resume_path}")

                # Give LinkedIn's backend a moment to process the file upload
                time.sleep(1.5)
                return True, "Uploaded new resume"
            else:
                logger.debug("No file input found. Resume upload might not be required on this page.")
                return False, "No file input"

        except Exception as e:
            logger.error(f"Error during resume upload check: {e}")
            return False, "Error during upload"

    def _handle_follow_company(self, modal, follow_preference: bool):
        try:
            follow_checkbox = modal.find_element(By.XPATH,
                                                 ".//input[@id='follow-company-checkbox' and @type='checkbox']")
            if follow_checkbox.is_selected() != follow_preference:
                label = modal.find_element(By.XPATH, ".//label[@for='follow-company-checkbox']")
                self.scraper.interactor.scroll_to_view(label)
                # Safely attempt to click the label without throwing exceptions
                try:
                    self.scraper.interactor.human_click(label)
                except:
                    pass
        except:
            pass

    def _handle_post_submit_popup(self):
        """
        Handles LinkedIn post-submit popups like:
        - Update profile
        - Not now
        - Done
        - Dismiss
        """

        import time
        from selenium.webdriver.common.by import By

        try:
            time.sleep(2)

            popup_buttons = self.scraper.driver.find_elements(By.TAG_NAME, "button")

            for btn in popup_buttons:
                try:
                    text = btn.text.strip().lower()

                    if text in [
                        "not now",
                        "done",
                        "dismiss",
                        "skip"
                    ]:
                        logger.info(f"Clicking post-submit popup button: {text}")

                        self.scraper.driver.execute_script(
                            "arguments[0].click();",
                            btn
                        )

                        time.sleep(1.5)
                        return True

                except Exception:
                    continue

            # Fallback close button (X)
            close_buttons = self.scraper.driver.find_elements(
                By.XPATH,
                "//button[contains(@aria-label,'Dismiss')]"
            )

            if close_buttons:
                logger.info("Closing popup using dismiss button")

                self.scraper.driver.execute_script(
                    "arguments[0].click();",
                    close_buttons[0]
                )

                time.sleep(1.5)
                return True

        except Exception as e:
            logger.warning(f"Failed handling post-submit popup: {e}")

        return False
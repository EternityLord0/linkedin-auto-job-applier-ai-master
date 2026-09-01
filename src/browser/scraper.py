#  Copyright (c) 2026 Ajinkya Kardile. All rights reserved.
#
#  This work is licensed under the terms of the MIT license.
#  For a copy, see <https://opensource.org/licenses/MIT>.

# src/browser/scraper.py
import re
import time

import pyautogui
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC

# Import configurations used for filtering and blacklisting
from config.search import search_data
from config.settings import settings_data
from src.browser.interactors import DOMInteractor
from src.utils.logger import logger


class LinkedInScraper:
    def __init__(self, driver, actions, wait):
        self.driver = driver
        self.actions = actions
        self.wait = wait
        self.interactor = DOMInteractor(driver, actions, wait)

        # Regex for extracting experience from job descriptions
        self.re_experience = re.compile(
            r'(\d+)\s*(?:\+|(?:-|to|–)\s*\d+)?\s*year[s]?',
            re.IGNORECASE
        )

    def is_logged_in(self) -> bool:
        try:
            if "feed" in self.driver.current_url:
                return True
            # Check for profile photo / Me icon in top nav
            me_icon = self.driver.find_elements(By.XPATH, "//img[contains(@class, 'global-nav__me-photo') or contains(@class, 'nav__artdeco-toggle') or contains(@alt, 'Foto do perfil') or contains(@alt, 'Profile photo')] | //button[contains(@class, 'global-nav__primary-link-me')]")
            if me_icon:
                return True
            # Check for guest/login buttons (PT/EN)
            not_logged_in = self.driver.find_elements(By.XPATH, "//a[contains(text(), 'Entrar') or contains(text(), 'Sign in') or contains(text(), 'Cadastre-se') or contains(text(), 'Join now')] | //button[@type='submit' and (contains(text(), 'Sign in') or contains(text(), 'Entrar') or contains(text(), 'Entra'))]")
            if not_logged_in:
                return False
            return False
        except Exception:
            return False

    def login(self, username, password):
        import pymsgbox
        try:
            if not username or not password:
                pymsgbox.alert(
                    "Usuário/senha não configurados em secrets.py. Faça o login manualmente no Chrome!",
                    "Login Manualmente", "Okay")
                self.manual_login_retry()
            else:
                if not self.is_logged_in():
                    self.auto_login(username, password)
                if not self.is_logged_in():
                    logger.warning("Auto-login pendente (Captcha ou 2FA). Aguardando login manual...")
                    self.manual_login_retry()
        except Exception as e:
            logger.error(f"Erro durante verificação de login: {e}")
            self.manual_login_retry()

    def auto_login(self, username, password):
        self.driver.get("https://www.linkedin.com/login")
        try:
            self.interactor.sleep_buffer(2, 3)
            self.interactor.text_input_by_id("username", username)
            self.interactor.text_input_by_id("password", password)

            submit_buttons = self.driver.find_elements(By.XPATH, '//button[@type="submit" and (contains(text(), "Sign in") or contains(text(), "Entrar") or contains(text(), "Entra"))]')
            if submit_buttons:
                submit_buttons[0].click()
            else:
                self.driver.find_element(By.XPATH, '//button[@type="submit"]').click()

            self.interactor.sleep_buffer(3, 5)

            if "feed" in self.driver.current_url or self.is_logged_in():
                logger.info("Login realizado com sucesso!")
            else:
                logger.warning("Verificação automática pós-login pendente.")
        except Exception as e:
            logger.error(f"Falha ao realizar auto-login: {e}")

    def manual_login_retry(self, retries=5):
        import pymsgbox
        count = 0
        while not self.is_logged_in():
            logger.warning("Navegador não está logado no LinkedIn!")
            button = "Confirmar Login"
            message = 'Por favor, faça o login na sua conta do LinkedIn no navegador aberto.\nQuando concluir, clique no botão "{}" abaixo para o robô iniciar as candidaturas!'.format(button)
            if count > retries:
                button = "Continuar"
                message = 'Se você já se conectou ao LinkedIn no Chrome, clique em "{}" para iniciar.'.format(button)
            count += 1
            res = pymsgbox.alert(message, "Login Necessário (LinkedIn)", button)
            if res and count > retries:
                return

    def apply_filters(self):
        """Applies location and job preferences from config."""
        # 1. Location
        if search_data.search_location.strip():
            logger.info(f"Setting location: {search_data.search_location}")
            try:
                loc_input = self.interactor.try_xpath(
                    ".//input[@aria-label='City, state, or zip code' or contains(@aria-label, 'Cidade') or contains(@aria-label, 'Estado') or contains(@aria-label, 'local') and not(@disabled)]", click=False)
                if loc_input and hasattr(loc_input, 'send_keys'):
                    loc_input.send_keys(Keys.CONTROL + "a")
                    loc_input.send_keys(search_data.search_location.strip())
                    time.sleep(2)
                    loc_input.send_keys(Keys.DOWN)
                    loc_input.send_keys(Keys.ENTER)
            except Exception as e:
                logger.warning("Failed to update search location.")

        # 2. Open All Filters
        try:
            filter_btn = self.interactor.try_xpath(
                '//button[normalize-space()="All filters" or normalize-space()="Todos os filtros" or contains(., "Todos os filtros") or contains(., "All filters")]',
                click=True
            )
            self.interactor.sleep_buffer(1, 3)

            # Date Posted filter matching both English and Portuguese labels
            if search_data.date_posted:
                date_options = []
                if search_data.date_posted in ["Past week", "Última semana", "Na última semana"]:
                    date_options = ["Na última semana", "Última semana", "Past week"]
                elif search_data.date_posted in ["Past 24 hours", "Nas últimas 24 horas", "Últimas 24 horas"]:
                    date_options = ["Nas últimas 24 horas", "Últimas 24 horas", "Past 24 hours"]
                elif search_data.date_posted in ["Past month", "No último mês", "Último mês"]:
                    date_options = ["No último mês", "Último mês", "Past month"]
                else:
                    date_options = [search_data.date_posted]

                clicked_date = False
                for opt in date_options:
                    if self.interactor.wait_span_click(opt, timeout=2, scroll=True):
                        logger.info(f"Successfully applied Date Posted filter: '{opt}'")
                        clicked_date = True
                        break
                if not clicked_date:
                    logger.warning(f"Could not find span for Date Posted filter: '{search_data.date_posted}'")

            # Multi-selects (Workplace mapping for PT/EN)
            onsite_map = {
                "Remote": ["Remoto", "Remote"],
                "Hybrid": ["Híbrido", "Hybrid"],
                "On-site": ["Presencial", "On-site"],
            }
            onsite_items = []
            for item in search_data.on_site:
                onsite_items.extend(onsite_map.get(item, [item]))

            for text in (search_data.experience_level + search_data.job_type
                         + onsite_items + search_data.location
                         + search_data.job_titles + search_data.benefits + search_data.commitments):
                self.interactor.wait_span_click(text, timeout=1.5, scroll=True)

            for company in search_data.companies:
                self.interactor.span_search_click("Add a company", company)
                self.interactor.span_search_click("Adicionar uma empresa", company)

            for industry in search_data.industry:
                self.interactor.span_search_click("Add an industry", industry)
                self.interactor.span_search_click("Adicionar um setor", industry)

            for job in search_data.job_function:
                self.interactor.span_search_click("Add a job function", job)
                self.interactor.span_search_click("Adicionar uma função", job)

            # Easy Apply Toggle
            if search_data.easy_apply_only:
                if not self.enable_easy_apply_filter():
                    self.interactor.toggle_button_click("Easy Apply")
                    self.interactor.toggle_button_click("Candidatura simplificada")
                    self.interactor.toggle_button_click("LinkedIn Apply")
            if search_data.under_10_applicants:
                self.interactor.toggle_button_click("Under 10 applicants")
                self.interactor.toggle_button_click("Menos de 10 candidaturas")
            if search_data.in_your_network:
                self.interactor.toggle_button_click("In your network")
                self.interactor.toggle_button_click("Na sua rede")
            if search_data.fair_chance_employer:
                self.interactor.toggle_button_click("Fair Chance Employer")

            # Show Results
            show_results = self.interactor.try_xpath(
                '//button[contains(translate(@aria-label, "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"), "apply current filters to show") or contains(translate(@aria-label, "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"), "exibir") or contains(translate(@aria-label, "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"), "mostrar") or contains(translate(@aria-label, "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"), "ver")]',
                click=True
            )
            self.interactor.sleep_buffer(2, 3)
        except Exception as e:
            logger.error(f"Failed to apply some filters: {e}")

    def enable_easy_apply_filter(self) -> bool:
        """Finds and turns ON the Easy Apply / Candidatura simplificada toggle switch."""
        xpaths = [
            "//span[contains(text(), 'Candidatura simplificada') or contains(text(), 'Easy Apply')]/ancestor::div[contains(@class, 'filter') or contains(@class, 'search') or contains(@class, 'artdeco') or contains(@class, 'flex') or contains(@class, 'form')]//button",
            "//span[contains(text(), 'Candidatura simplificada') or contains(text(), 'Easy Apply')]/ancestor::div[contains(@class, 'filter') or contains(@class, 'search') or contains(@class, 'artdeco') or contains(@class, 'flex') or contains(@class, 'form')]//input",
            "//span[contains(text(), 'Candidatura simplificada') or contains(text(), 'Easy Apply')]/following::button[1]",
            "//span[contains(text(), 'Candidatura simplificada') or contains(text(), 'Easy Apply')]/following::input[@role='switch'][1]",
            "//h3[contains(., 'Candidatura simplificada') or contains(., 'Easy Apply')]/following::button[1]",
            "//label[contains(., 'Candidatura simplificada') or contains(., 'Easy Apply')]",
            "//button[contains(@aria-label, 'Candidatura simplificada') or contains(@aria-label, 'Easy Apply')]"
        ]
        for xpath in xpaths:
            try:
                elements = self.driver.find_elements(By.XPATH, xpath)
                for el in elements:
                    if el.is_displayed():
                        self.interactor.scroll_to_view(el)
                        self.interactor.human_click(el)
                        logger.info("Successfully toggled 'Candidatura simplificada' filter!")
                        return True
            except Exception:
                continue
        return False

    def get_page_info(self):
        """Returns the pagination element and current page number."""
        try:
            classes = ["jobs-search-pagination__pages", "artdeco-pagination", "artdeco-pagination__pages"]
            pagination_element = None
            for c in classes:
                elements = self.driver.find_elements(By.CLASS_NAME, c)
                if elements:
                    pagination_element = elements[0]
                    break

            current_page = 1
            if pagination_element:
                active_pages = pagination_element.find_elements(By.XPATH, ".//li[contains(@class, 'active')]")
                if active_pages:
                    current_page = int(active_pages[0].text.strip())

            return pagination_element, current_page

        except Exception as e:
            logger.error(f"Safely caught error fetching pagination info: {e}")
            return None, 1

    def go_to_next_page(self, pagination_element, current_page) -> bool:
        """Navigates to the next page of job results safely."""
        try:
            next_button_xpath = f".//button[@aria-label='Page {current_page + 1}' or @aria-label='Página {current_page + 1}']"
            next_buttons = pagination_element.find_elements(By.XPATH, next_button_xpath)
            if not next_buttons:
                logger.info(f"No button found for Page {current_page + 1}. Reached the end of search results.")
                return False  # Returns False so the bot knows to move to the next search term
            next_btn = next_buttons[0]
            self.interactor.scroll_to_view(next_btn)
            try:
                self.interactor.human_click(next_btn)
            except Exception:
                self.driver.execute_script("arguments[0].click();", next_btn)
            self.interactor.sleep_buffer(2.0, 4.0)  # Let the next page load
            return True

        except Exception as e:
            logger.error(f"Safely caught error navigating to page {current_page + 1}: {e}")
            return False

    def get_job_listings_on_page(self):
        """Waits for and returns all job list elements on the current page."""
        try:
            self.wait.until(EC.presence_of_all_elements_located((By.XPATH, "//li[@data-occludable-job-id]")))
            return self.driver.find_elements(By.XPATH, "//li[@data-occludable-job-id]")
        except Exception:
            return []

    def extract_job_card_details(self, job_element) -> dict:
        """Parses the text from a job card listing in the left pane."""
        try:
            job_details_button = job_element.find_element(By.TAG_NAME, 'a')
            self.interactor.scroll_to_view(job_details_button, top=True)
            job_id = job_element.get_attribute('data-occludable-job-id')
        except Exception:
            return {"job_id": "", "title": "Unknown", "company": "Unknown", "work_location": "", "work_style": "Unknown", "element_button": None}

        title = job_details_button.text.split("\n")[0].strip()
        company = "Unknown"
        work_location = ""
        work_style = "Unknown"

        try:
            full_card_text = job_element.text
            lines = [l.strip() for l in full_card_text.split("\n") if l.strip()]

            if len(lines) >= 2 and title in lines[0]:
                company = lines[1]

            raw_details = ""
            try:
                raw_details = job_element.find_element(By.CLASS_NAME, 'artdeco-entity-lockup__subtitle').text
            except Exception:
                if len(lines) > 2:
                    raw_details = lines[2]
                else:
                    raw_details = full_card_text

            if '(' in raw_details and ')' in raw_details:
                start = raw_details.rfind('(')
                end = raw_details.rfind(')')
                work_style = raw_details[start + 1:end].strip()
                work_location_raw = raw_details[:start].strip()
                if '·' in work_location_raw:
                    work_location = work_location_raw.split('·')[-1].strip()
                else:
                    work_location = work_location_raw
            else:
                raw_lower = raw_details.lower()
                if 'remot' in raw_lower or 'home office' in raw_lower:
                    work_style = "Remote"
                elif 'híbrid' in raw_lower or 'hibrid' in raw_lower or 'hybrid' in raw_lower:
                    work_style = "Hybrid"
                elif 'presencial' in raw_lower or 'on-site' in raw_lower:
                    work_style = "On-site"

                if '·' in raw_details:
                    work_location = raw_details.split('·')[-1].strip()
                else:
                    work_location = raw_details

        except Exception as e:
            logger.debug(f"Could not parse all job card details: {e}")

        return {
            "job_id": job_id,
            "title": title,
            "company": company,
            "work_location": work_location,
            "work_style": work_style,
            "element_button": job_details_button
        }

    def click_job_card(self, job_element):
        """Clicks the job card to load details in the right pane."""
        try:
            btn = job_element.find_element(By.TAG_NAME, 'a')
            btn.click()
            self.interactor.sleep_buffer(2, 3)
        except:
            pass

    def get_job_description_and_check_blacklist(self) -> tuple[str, str | None]:
        """
        Reads the right pane. Checks about company and job description for blacklisted words.
        Returns: (job_description, skip_reason). If skip_reason is None, it is safe to apply.
        """
        try:
            # Check About Company safely
            try:
                about_company_org = self.driver.find_element(By.CLASS_NAME, "jobs-company__box").text.lower()
                skip_company_check = any(
                    word.lower() in about_company_org for word in search_data.about_company_good_words)

                if not skip_company_check:
                    for word in search_data.about_company_bad_words:
                        if word.lower() in about_company_org:
                            return "", f"Blacklisted company word found: {word}"
            except Exception:
                pass  # Company box doesn't always exist

            try:
                # Try the newest layout first
                job_desc_element = self.driver.find_element(By.ID, "job-details")
            except:
                try:
                    job_desc_element = self.driver.find_element(By.CLASS_NAME, "jobs-description-content__text")
                except:
                    job_desc_element = self.driver.find_element(By.CLASS_NAME, "jobs-box__html-content")

            # --- ADDED: Simulate Human Reading by scrolling ---
            try:
                # Pause to read the top, scroll to the bottom, pause, then scroll back up
                self.interactor.sleep_buffer(0.5, 1.0)
                self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'end'});",
                                           job_desc_element)
                self.interactor.sleep_buffer(1.5, 3.0)
                self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'start'});",
                                           job_desc_element)
                self.interactor.sleep_buffer(0.5, 1.0)
            except Exception as e:
                logger.debug(f"Minor issue smoothly scrolling the job description (Safe to ignore): {e}")
            # --------------------------------------------------

            # .text truncates hidden text. .get_attribute("textContent") gets everything.
            job_desc = job_desc_element.get_attribute("textContent")
            if not job_desc:
                job_desc = job_desc_element.text

            job_desc_lower = job_desc.lower()

            for word in search_data.job_desc_bad_words:
                if word.lower() in job_desc_lower:
                    return job_desc, f"Blacklisted job word found: {word}"

            if not search_data.security_clearance and any(
                    w in job_desc_lower for w in ['polygraph', 'clearance', 'secret']):
                return job_desc, "Requires security clearance"

            # Check Experience Requirements safely (PT & EN)
            re_req_experience = re.compile(
                r'(?:m[íi]nimo\s+(?:de\s+)?|at\s+least\s+|minimum\s+(?:of\s+)?|experi[êe]ncia\s+(?:m[íi]nima\s+)?(?:de\s+)?|experience\s*(?:of\s*)?:?\s*|requir(?:es?|ed)\s*(?:of\s*)?:?\s*)'
                r'(\d{1,2})\s*(?:\+|(?:-|a|to|–)\s*\d{1,2})?\s*(?:year|ano)s?',
                re.IGNORECASE
            )
            re_direct_experience = re.compile(
                r'(\d{1,2})\s*(?:\+|(?:-|a|to|–)\s*\d{1,2})?\s*(?:year|ano)s?\s*(?:de\s+experi[êe]ncia|of\s+experience|de\s+atua[çc][ãa]o)',
                re.IGNORECASE
            )

            # Filter out general company market presence mentions (e.g. "10 anos de mercado")
            cleaned_desc_lines = []
            for line in job_desc.split('\n'):
                line_lower = line.lower()
                if any(skip_term in line_lower for skip_term in [
                    'de mercado', 'no mercado', 'in the market', 'in business', 'fundada',
                    'founded', 'história', 'history', 'anos de vida', 'years of history'
                ]):
                    continue
                cleaned_desc_lines.append(line)
            targeted_text = "\n".join(cleaned_desc_lines)

            matches = re_req_experience.findall(targeted_text) + re_direct_experience.findall(targeted_text)
            if matches:
                exp_values = [
                    int(m)
                    for m in matches
                    if 0 < int(m) <= 12
                ]
                if exp_values:
                    # Use min required experience found in requirement clauses
                    req_exp = min(exp_values)
                    masters_bonus = (
                        2
                        if search_data.did_masters
                           and 'master' in job_desc.lower()
                        else 0
                    )
                    allowed_exp = (
                            search_data.current_experience
                            + masters_bonus
                    )
                    if (
                            search_data.current_experience > -1
                            and req_exp > allowed_exp
                    ):
                        return (
                            job_desc,
                            f"Required experience ({req_exp}) exceeds current ({allowed_exp})"
                        )

            return job_desc, None

        except Exception as e:
            logger.debug(f"Failed to extract full job description: {e}")
            return "Unknown", None

    def _handle_safety_reminder(self):
        """Checks for and dismisses the LinkedIn safety reminder popup."""
        try:
            continue_btn = self.driver.find_elements(By.XPATH, "//button[contains(., 'Continue applying') or contains(., 'Continuar candidatando')]")
            if continue_btn:
                logger.info("Safety reminder popup detected! Clicking 'Continue applying'...")
                # Force click via JS to bypass any overlapping elements
                self.driver.execute_script("arguments[0].click();", continue_btn[0])
                self.interactor.sleep_buffer(1.5, 2.5) # Give the next modal time to load
        except Exception as e:
            logger.debug(f"Safe to ignore: Error checking for safety reminder: {e}")

    def click_apply_button(self) -> bool:
        """
        Attempts to click the apply button.
        Returns True if it's an Easy Apply (modal opens).
        Returns False if it's an External Apply (new tab opens).
        """
        is_easy_apply = self.interactor.try_xpath(
            ".//button[contains(@class,'jobs-apply-button') and (contains(@aria-label, 'Easy') or contains(@aria-label, 'simplificada') or contains(@aria-label, 'Candidatura'))]")

        # Let the UI settle for a moment
        self.interactor.sleep_buffer(1, 2)

        # --- FIX: Check for the safety reminder after clicking Easy Apply ---
        self._handle_safety_reminder()

        if not is_easy_apply:
            try:
                apply_btn = self.driver.find_element(By.XPATH, ".//button[contains(@class,'jobs-apply-button')]")
                tabs_before = len(self.driver.window_handles)
                apply_btn.click()
                self.interactor.sleep_buffer(1, 2)

                # --- FIX: Check for the safety reminder after clicking External Apply ---
                self._handle_safety_reminder()

                if len(self.driver.window_handles) > tabs_before:
                    return False  # External Apply

                # Check if modal opened
                try:
                    modal_element = self.interactor.try_xpath('//div[contains(@class, "jobs-easy-apply-modal")] | //div[contains(@class, "easy-apply-modal")] | //div[contains(@class, "jobs-easy-apply-content")] | //div[contains(@id, "artdeco-modal")] | //div[@role="dialog"]', click=False)
                    if modal_element:
                        return True
                    else:
                        self.discard_application()
                        return False
                except:
                    self.discard_application()
                    return False
            except:
                return False

        return bool(is_easy_apply)

    def handle_external_apply(self):
        """Handles closing the external application tab if a new one opened."""
        windows = self.driver.window_handles
        if len(windows) > 1:
            self.driver.switch_to.window(windows[-1])
            if settings_data.close_tabs:
                self.driver.close()
            self.driver.switch_to.window(windows[0])

    def is_already_applied(self, job_element) -> bool:
        """Safely checks if a job is already applied to without throwing exceptions."""
        try:
            footer_states = job_element.find_elements(By.CLASS_NAME, "job-card-container__footer-job-state")
            if footer_states and any(term in footer_states[0].text for term in ["Applied", "Candidatura enviada", "Candidatado", "Inscrito", "Candidatou-se"]):
                return True

            card_applied = job_element.find_elements(By.XPATH, ".//*[contains(@class, 'jobs-s-apply__application-link') or contains(text(), 'Candidatura enviada') or contains(text(), 'Applied')]")
            if card_applied:
                return True
            return False

        except Exception as e:
            logger.debug(f"is_already_applied check failed safely: {e}")
            return False

    def discard_application(self):
        """Safely and relentlessly closes the Easy Apply modal and confirms the discard."""
        from selenium.webdriver.common.by import By
        from selenium.webdriver.common.keys import Keys
        import time

        logger.info("Attempting to discard the application...")

        max_attempts = 3
        attempt = 0

        while attempt < max_attempts:
            try:
                # 1. Check if the modal is even open. If not, we are done!
                modal = self.driver.find_elements(By.XPATH, '//div[contains(@class, "jobs-easy-apply-modal")] | //div[contains(@class, "easy-apply-modal")] | //div[contains(@id, "artdeco-modal")] | //div[@role="dialog"]')
                if not modal:
                    logger.info("Application modal is completely closed.")
                    return

                # 2. Try to click the "X" (Dismiss / Descartar / Fechar) button
                close_btn_xpaths = [
                    "//button[contains(@data-test-modal-close-btn, '')]",
                    "//button[contains(@aria-label, 'Dismiss') or contains(@aria-label, 'Descartar') or contains(@aria-label, 'Fechar') or contains(@aria-label, 'Close')]",
                    "//li-icon[@type='cancel-icon']/parent::button",
                    "//button[contains(@class, 'artdeco-modal__dismiss')]"
                ]

                close_clicked = False
                for xpath in close_btn_xpaths:
                    close_btn = self.driver.find_elements(By.XPATH, xpath)
                    if close_btn:
                        try:
                            # Force click via JS to bypass any overlapping tooltips
                            self.driver.execute_script("arguments[0].click();", close_btn[0])
                            close_clicked = True
                            break
                        except Exception:
                            pass

                # Fallback to ESCAPE if no "X" button worked
                if not close_clicked:
                    self.actions.send_keys(Keys.ESCAPE).perform()

                # Wait for the confirmation dialog animation to finish
                time.sleep(1.5)

                # 3. Try to click the "Discard" / "Descartar" confirmation button
                discard_confirm_xpaths = [
                    "//button[@data-control-name='discard_application_confirm_btn']",
                    "//button[@data-test-dialog-primary-btn]",
                    "//button[contains(@class, 'artdeco-modal__confirm-dialog-btn') and (contains(., 'Discard') or contains(., 'Descartar') or contains(., 'Fechar'))]",
                    "//span[text()='Discard' or text()='Descartar' or text()='Fechar']/parent::button",
                    "//button[contains(., 'Discard') or contains(., 'Descartar')]"
                ]

                for xpath in discard_confirm_xpaths:
                    discard_btn = self.driver.find_elements(By.XPATH, xpath)
                    if discard_btn:
                        try:
                            # Force click the discard confirmation
                            self.driver.execute_script("arguments[0].click();", discard_btn[0])
                            time.sleep(1.5)  # Wait for it to close
                            break
                        except Exception:
                            pass

                attempt += 1

            except Exception as e:
                logger.debug(f"Discard attempt {attempt} encountered an issue: {e}")
                attempt += 1
                time.sleep(1)

        # Final check to see if it closed after all attempts
        if self.driver.find_elements(By.XPATH, '//div[contains(@class, "jobs-easy-apply-modal")] | //div[contains(@class, "easy-apply-modal")]'):
            logger.warning("Failed to discard application after 3 attempts. It might be stuck.")
        else:
            logger.info("Application modal is completely closed.")

#  Copyright (c) 2026 Ajinkya Kardile. All rights reserved.
#
#  This work is licensed under the terms of the MIT license.
#  For a copy, see <https://opensource.org/licenses/MIT>.

# src/core/bot_engine.py
import time
from datetime import datetime

import pyautogui
from selenium.common.exceptions import NoSuchWindowException, WebDriverException

from config.search import search_data
from config.settings import settings_data
from src.core.job_applier import JobApplier
from src.utils.logger import logger
from src.utils.resume_selector import select_resume_path


class BotEngine:
    def __init__(self, scraper, ai_manager, csv_manager):
        self.scraper = scraper
        self.ai = ai_manager
        self.csv = csv_manager
        self.job_applier = JobApplier(scraper, ai_manager, csv_manager)

        # Tracking Metrics
        self.total_runs = 1
        self.easy_applied_count = 0
        self.external_jobs_count = 0
        self.failed_count = 0
        self.skip_count = 0
        self.daily_limit_reached = False

        # State
        self.applied_jobs = self.csv.get_applied_job_ids()
        self.rejected_jobs = set()
        self.blacklisted_companies = set()

        # temp setting
        self.pause_after_filters = settings_data.pause_after_filters

    def start(self):
        """The main entry point for the bot execution."""
        logger.info(f"Starting LinkedIn Auto Applier. Cycle {self.total_runs}")

        try:
            self._run_cycle()

            while settings_data.run_non_stop:
                if self.daily_limit_reached:
                    logger.warning("Daily limit reached. Stopping continuous run.")
                    break

                # Cycle logic from original script
                if settings_data.cycle_date_posted:
                    self._cycle_date_settings()
                if settings_data.alternate_sortby:
                    search_data.sort_by = "Most recent" if search_data.sort_by == "Most relevant" else "Most relevant"
                    self._run_cycle()
                    search_data.sort_by = "Most recent" if search_data.sort_by == "Most relevant" else "Most relevant"

                self._run_cycle()

        except (NoSuchWindowException, WebDriverException):
            logger.error("Browser closed or session invalid. Exiting.", exc_info=True)
        except Exception:
            logger.critical("Fatal error in main execution loop.", exc_info=True)
        finally:
            self.print_summary()

    def _run_cycle(self):
        """Executes one complete search and apply cycle."""
        if self.daily_limit_reached:
            return

        logger.info("==================================================")
        logger.info(f"Date and Time: {datetime.now()}")
        logger.info(f"Cycle number: {self.total_runs}")

        # Iterate over all search terms
        search_terms = search_data.search_terms
        if search_data.randomize_search_order:
            import random
            random.shuffle(search_terms)

        for term in search_terms:
            if self.daily_limit_reached:
                break
            self._process_search_term(term)

        self.total_runs += 1

        if not self.daily_limit_reached:
            logger.info("Sleeping for 5 minutes before next phase...")
            time.sleep(300)

    def _process_search_term(self, search_term: str):
        """Searches for a specific term using direct URL parameters for maximum precision."""
        import urllib.parse

        encoded_term = urllib.parse.quote(search_term)

        # Build target search URLs for:
        # 1. Remote jobs across Brazil (f_WT=2, f_AL=true, f_TPR=r604800)
        # 2. On-site/Hybrid jobs within 160km of SJRP (location=SJRP, distance=100, f_WT=1,3, f_AL=true, f_TPR=r604800)
        search_urls = [
            (
                f"https://www.linkedin.com/jobs/search/?keywords={encoded_term}&location=Brasil&f_WT=2&f_AL=true&f_TPR=r604800",
                "Remoto (Brasil todo)"
            ),
            (
                f"https://www.linkedin.com/jobs/search/?keywords={encoded_term}&location=S%C3%A3o%20Jos%C3%A9%20do%20Rio%20Preto%2C%20S%C3%A3o%20Paulo%2C%20Brasil&distance=100&f_WT=1%2C3&f_AL=true&f_TPR=r604800",
                "Presencial/Híbrido (até 160km SJRP)"
            )
        ]

        for url, mode_label in search_urls:
            if self.daily_limit_reached:
                break

            logger.info(f"Searching for: '{search_term}' [{mode_label}]")
            self.scraper.driver.get(url)
            self.scraper.interactor.sleep_buffer(2, 4)

            # URL already contains exact location, work style, Easy Apply, and Date Posted parameters
            if self.pause_after_filters and "Turn off Pause after search" == pymsgbox.confirm(
                    "These are your configured search results and filter. It is safe to change them while this dialog is open, any changes later could result in errors and skipping this search run.",
                    "Please check your results", ("Turn off Pause after search", "Look's good, Continue")):
                self.pause_after_filters = False

            current_count = 0
            while current_count < search_data.switch_number:
                initial_job_listings = self.scraper.get_job_listings_on_page()
                num_jobs_on_page = len(initial_job_listings)

                if num_jobs_on_page == 0:
                    logger.info(f"No job listings found on page for '{search_term}' [{mode_label}].")
                    break

                pagination_element, current_page = self.scraper.get_page_info()

                for i in range(num_jobs_on_page):
                    if current_count >= search_data.switch_number or self.daily_limit_reached:
                        break
                    if settings_data.keep_screen_awake:
                        pyautogui.press('shiftright')

                    try:
                        current_job_listings = self.scraper.get_job_listings_on_page()
                        if i >= len(current_job_listings):
                            break
                        fresh_job_element = current_job_listings[i]

                        success = self._process_single_job(fresh_job_element, is_remote_mode=("Remoto" in mode_label))
                        if success:
                            current_count += 1

                    except Exception as e:
                        logger.warning(f"Error processing job at index {i}, safely skipping to next. Error: {e}")
                        continue

                # Go to next page
                if not pagination_element or not self.scraper.go_to_next_page(pagination_element, current_page):
                    logger.info(f"No more pages available for '{search_term}' [{mode_label}].")
                    break

    def _process_single_job(self, job_element, is_remote_mode: bool = False) -> bool:
        """Processes a single job card. Returns True if applied successfully."""
        from datetime import datetime
        if settings_data.keep_screen_awake: pyautogui.press('shiftright')

        details = self.scraper.extract_job_card_details(job_element)
        job_id = details.get('job_id')
        job_title = details.get('title', 'Unknown')

        if job_id in self.applied_jobs or self.scraper.is_already_applied(
                job_element) or details.get('company') in self.blacklisted_companies:
            logger.info(f"Skipping job {job_id} (Already applied/blacklisted company)")
            self.skip_count += 1
            return False

        # Evaluate job title against job_title_bad_words BEFORE clicking card
        for word in search_data.job_title_bad_words:
            if word.lower() in job_title.lower():
                logger.info(f"Skipping job {job_id}: Blacklisted title word found '{word}' in '{job_title}'")
                self.rejected_jobs.add(job_id)
                self.skip_count += 1
                self.csv.log_failed_job({'Job ID': job_id, 'Assumed Reason': f"Blacklisted title word: {word}"})
                return False

        # Instant Pre-filter: Check card location BEFORE opening/clicking card ONLY in local (non-remote) search mode
        if not is_remote_mode:
            card_style = details.get('work_style', '').lower()
            card_loc = details.get('work_location', '').lower()
            card_is_remote = any(term in (card_style + " " + card_loc) for term in ['remote', 'remoto', 'home office', 'trabalho remoto', 'teletrabalho'])

            sjrp_allowed = [
                'são josé do rio preto', 'sao jose do rio preto', 'rio preto',
                'mirassol', 'bady bassitt', 'tanabi', 'monte aprazível', 'monte aprazivel',
                'josé bonifácio', 'jose bonifacio', 'catanduva', 'pindorama', 'santa adélia',
                'novo horizonte', 'votuporanga', 'jales', 'fernandópolis', 'fernandopolis',
                'olímpia', 'olimpia', 'barretos', 'bebedouro', 'jaboticabal', 'taquaritinga',
                'matão', 'matao', 'araraquara', 'sertãozinho', 'sertaozinho', 'araçatuba', 'aracatuba',
                'birigui', 'penápolis', 'penapolis', 'lins', 'promissão', 'promissao',
                'frutal', 'iturama', 'guaíra', 'guaira'
            ]
            far_sp_keywords = [
                'são paulo, são paulo', 'sao paulo, sao paulo', 'grande são paulo', 'grande sao paulo',
                'suzano', 'guarulhos', 'osasco', 'santo andré', 'santo andre', 'são bernardo', 'sao bernardo',
                'são caetano', 'sao caetano', 'barueri', 'alphaville', 'campinas', 'sorocaba',
                'santos', 'jundiaí', 'jundiai', 'taubaté', 'taubate', 'são josé dos campos', 'sao jose dos campos',
                'piracicaba', 'indaiatuba', 'americana', 'limeira', 'sumaré', 'sumare', 'hortolândia', 'hortolandia',
                'valinhos', 'vinhedo', 'itu', 'cotia', 'taboão', 'taboao', 'mogi das cruzes', 'diadema', 'mogi guaçu',
                'ribeirão preto', 'ribeirao preto', 'são carlos', 'sao carlos', 'marília', 'marilia', 'bauru', 'uberaba',
                'goiás', 'goias', 'maranhão', 'maranhao', 'mato grosso', 'paraná', 'parana', 'rio de janeiro', 'minas gerais', 'bahia', 'ceará', 'ceara', 'pernambuco'
            ]

            if not card_is_remote and card_loc and card_loc != 'unknown':
                is_within_sjrp = any(city in card_loc for city in sjrp_allowed) and not any(far in card_loc for far in far_sp_keywords)
                if not is_within_sjrp:
                    logger.info(f"Skipping job {job_id} before click: On-site/Hybrid job outside 160km SJRP ({details.get('work_location')})")
                    self.rejected_jobs.add(job_id)
                    self.skip_count += 1
                    self.csv.log_failed_job({'Job ID': job_id, 'Assumed Reason': f"Distant non-remote location (>160km SJRP): {details.get('work_location')}"})
                    return False

        # Load job card details in right pane
        self.scraper.click_job_card(job_element)

        job_desc, skip_reason = self.scraper.get_job_description_and_check_blacklist()
        if skip_reason:
            logger.info(f"Skipping job {job_id}: {skip_reason}")
            self.rejected_jobs.add(job_id)
            self.skip_count += 1
            self.csv.log_failed_job({'Job ID': job_id, 'Assumed Reason': skip_reason})
            return False

        # Filter location: Remote jobs anywhere in Brazil, On-site/Hybrid within ~160km of SJRP
        work_style = details.get('work_style', '').lower()
        work_loc = details.get('work_location', '').lower()
        job_text_check = (work_style + " " + work_loc + " " + (job_desc[:500] if job_desc else "")).lower()

        is_remote = any(term in job_text_check for term in ['remote', 'remoto', 'home office', 'trabalho remoto', 'teletrabalho'])

        if not is_remote_mode and not is_remote:
            sjrp_allowed = [
                'são josé do rio preto', 'sao jose do rio preto', 'rio preto',
                'mirassol', 'bady bassitt', 'tanabi', 'monte aprazível', 'monte aprazivel',
                'josé bonifácio', 'jose bonifacio', 'catanduva', 'pindorama', 'santa adélia',
                'novo horizonte', 'votuporanga', 'jales', 'fernandópolis', 'fernandopolis',
                'olímpia', 'olimpia', 'barretos', 'bebedouro', 'jaboticabal', 'taquaritinga',
                'matão', 'matao', 'araraquara', 'sertãozinho', 'sertaozinho', 'araçatuba', 'aracatuba',
                'birigui', 'penápolis', 'penapolis', 'lins', 'promissão', 'promissao',
                'frutal', 'iturama', 'guaíra', 'guaira'
            ]
            far_sp_keywords = [
                'são paulo, são paulo', 'sao paulo, sao paulo', 'grande são paulo', 'grande sao paulo',
                'suzano', 'guarulhos', 'osasco', 'santo andré', 'santo andre', 'são bernardo', 'sao bernardo',
                'são caetano', 'sao caetano', 'barueri', 'alphaville', 'campinas', 'sorocaba',
                'santos', 'jundiaí', 'jundiai', 'taubaté', 'taubate', 'são josé dos campos', 'sao jose dos campos',
                'piracicaba', 'indaiatuba', 'americana', 'limeira', 'sumaré', 'sumare', 'hortolândia', 'hortolandia',
                'valinhos', 'vinhedo', 'itu', 'cotia', 'taboão', 'taboao', 'mogi das cruzes', 'diadema', 'mogi guaçu',
                'ribeirão preto', 'ribeirao preto', 'são carlos', 'sao carlos', 'marília', 'marilia', 'bauru', 'uberaba'
            ]

            is_within_sjrp_region = any(city in work_loc for city in sjrp_allowed) and not any(far in work_loc for far in far_sp_keywords)

            if not is_within_sjrp_region:
                loc_disp = details.get('work_location') or work_loc or 'desconhecida'
                logger.info(f"Skipping job {job_id}: On-site/Hybrid job outside ~160km SJRP target region ({loc_disp})")
                self.rejected_jobs.add(job_id)
                self.skip_count += 1
                self.csv.log_failed_job({'Job ID': job_id, 'Assumed Reason': f"Distant non-remote location (>160km SJRP): {loc_disp}"})
                return False

        if self.ai.is_active and hasattr(self.ai.client, 'evaluate_job_relevance'):
            if not self.ai.client.evaluate_job_relevance(job_title, job_desc):
                logger.info(f"Skipping job {job_id}: AI evaluated job '{job_title}' as irrelevant to candidate background.")
                self.rejected_jobs.add(job_id)
                self.skip_count += 1
                self.csv.log_failed_job({'Job ID': job_id, 'Assumed Reason': 'AI Evaluated Irrelevant Job Title/Description'})
                return False

        import os
        selected_resume = select_resume_path(job_title, job_desc)
        self.ai.set_resume_path(selected_resume)

        # Token optimization: skip extracting skills via AI for every job card to save 50%+ tokens
        skills_required = "Skipped (Token Optimization)"

        try:
            is_easy_apply = self.scraper.click_apply_button()

            if is_easy_apply:
                logger.info(f"Applying For Job: {job_title}")
                questions_list = self.job_applier.execute_easy_apply_flow(job_id, job_desc, resume_path=selected_resume)
                if questions_list is not False:  # Flow succeeded
                    self.easy_applied_count += 1
                    self.applied_jobs.add(job_id)

                    # Properly formatted dictionary for CSV
                    self.csv.log_submitted_job({
                        'Job ID': job_id,
                        'Title': details.get('title', 'Unknown'),
                        'Company': details.get('company', 'Unknown'),
                        'Work Location': details.get('work_location', 'Unknown'),
                        'Work Style': details.get('work_style', 'Unknown'),
                        'About Job': job_desc,
                        'Experience required': 'Unknown',
                        'Skills required': str(skills_required),
                        'HR Name': 'Unknown',
                        'HR Link': 'Unknown',
                        'Resume': os.path.basename(selected_resume),
                        'Re-posted': False,
                        'Date Posted': 'Unknown',
                        'Date Applied': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'Job Link': f"https://www.linkedin.com/jobs/view/{job_id}",
                        'External Job link': 'Easy Applied',
                        'Questions Found': str(questions_list),
                        'Connect Request': 'In Development'
                    })
                else:
                    self.failed_count += 1
                    self.scraper.discard_application()
            return True

        except Exception as e:
            logger.error(f"Failed to apply to {job_id}: {e}")
            self.failed_count += 1
            self.scraper.discard_application()
            return False

    def _cycle_date_settings(self):
        """Rotates the date_posted filter for continuous runs."""
        from typing import cast, Any
        date_options = ["Any time", "Past month", "Past week", "Past 24 hours"]
        current_idx = date_options.index(search_data.date_posted) if search_data.date_posted in date_options else 0
        next_idx = current_idx + 1 if current_idx + 1 < len(date_options) else 0
        search_data.date_posted = cast(Any, date_options[next_idx])

    def print_summary(self):
        """Prints the final summary when the bot stops."""
        summary = (
            f"Total runs: {self.total_runs}\n"
            f"Jobs Easy Applied: {self.easy_applied_count}\n"
            f"External job links collected: {self.external_jobs_count}\n"
            f"Total applied/collected: {self.easy_applied_count + self.external_jobs_count}\n"
            f"Failed jobs: {self.failed_count}\n"
            f"Irrelevant jobs skipped: {self.skip_count}\n"
        )
        logger.info("\n=== BOT EXECUTION SUMMARY ===\n" + summary)

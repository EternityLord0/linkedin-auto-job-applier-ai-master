# src/core/publisher.py
import os
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

try:
    import pymsgbox
except ImportError:
    pymsgbox = None

from src.utils.logger import logger


class LinkedInPublisher:
    def __init__(self, scraper):
        self.scraper = scraper
        self.driver = scraper.driver
        self.interactor = scraper.interactor

    def open_feed(self):
        """Navigates to the LinkedIn feed and verifies login status."""
        logger.info("Opening LinkedIn Feed...")
        self.driver.get("https://www.linkedin.com/feed/")
        self.interactor.sleep_buffer(3, 5)

        if not self.scraper.is_logged_in():
            logger.warning("User is not logged in. Prompting for manual login...")
            self.scraper.manual_login_retry()

    def create_post(self, post_text: str, banner_path: str | None = None, dry_run: bool = False) -> bool:
        """
        Creates and optionally publishes a post on LinkedIn with optional media banner.
        
        :param post_text: Content of the LinkedIn post.
        :param banner_path: Relative or absolute path to the banner image.
        :param dry_run: If True, populates the post and pauses for user confirmation without auto-clicking publish.
        :return: True if successfully published, False otherwise.
        """
        self.open_feed()

        logger.info("Triggering 'Start a post' dialog...")
        try:
            # 1. Click on the "Start a post" / "Começar publicação" trigger button
            start_post_xpaths = [
                "//button[contains(@class, 'share-box-feed-entry__trigger')]",
                "//button[contains(., 'Começar publicação') or contains(., 'Criar publicação') or contains(., 'Start a post')]",
                "//div[contains(@class, 'share-box-feed-entry')]//button",
                "//span[contains(text(), 'Começar publicação') or contains(text(), 'Start a post')]/ancestor::button"
            ]

            clicked_trigger = False
            for xpath in start_post_xpaths:
                btn = self.interactor.try_xpath(xpath, click=True)
                if btn:
                    clicked_trigger = True
                    break

            if not clicked_trigger:
                logger.error("Could not find 'Start a post' button on LinkedIn Feed.")
                return False

            self.interactor.sleep_buffer(2, 3)

            # 2. Upload media/banner if provided
            if banner_path and os.path.exists(banner_path):
                abs_banner_path = os.path.abspath(banner_path)
                logger.info(f"Attaching banner image: {abs_banner_path}")

                try:
                    file_inputs = self.driver.find_elements(By.XPATH, "//input[@type='file']")
                    if file_inputs:
                        file_inputs[0].send_keys(abs_banner_path)
                        logger.info("Banner image sent to file input.")
                    else:
                        # Click media button to activate file input
                        media_btn = self.interactor.try_xpath(
                            "//button[contains(@aria-label, 'Adicionar mídia') or contains(@aria-label, 'Add media') or contains(@aria-label, 'foto') or contains(@aria-label, 'photo') or contains(@class, 'share-promoted-detour-button')]",
                            click=True
                        )
                        time.sleep(1)
                        file_inputs = self.driver.find_elements(By.XPATH, "//input[@type='file']")
                        if file_inputs:
                            file_inputs[0].send_keys(abs_banner_path)

                    self.interactor.sleep_buffer(2, 4)

                    # Click "Next" / "Avançar" / "Concluir" in media preview dialog
                    media_confirm_xpaths = [
                        "//button[contains(@class, 'share-box-footer__primary-btn')]",
                        "//button[contains(., 'Avançar') or contains(., 'Next') or contains(., 'Concluir') or contains(., 'Done')]",
                        "//div[contains(@class, 'share-media-editor')]//button[contains(@class, 'primary')]"
                    ]
                    for conf_xpath in media_confirm_xpaths:
                        if self.interactor.try_xpath(conf_xpath, click=True):
                            logger.info("Confirmed banner in media dialog.")
                            break

                    self.interactor.sleep_buffer(1.5, 2.5)

                except Exception as e:
                    logger.warning(f"Could not attach banner image: {e}")

            # 3. Enter post text in the editor
            logger.info("Writing post content in LinkedIn editor...")
            editor_xpaths = [
                "//div[contains(@class, 'ql-editor')]",
                "//div[@role='textbox']",
                "//div[contains(@aria-label, 'publicação') or contains(@aria-label, 'post')]",
                "//div[@data-placeholder]"
            ]

            editor_el = None
            for ed_xpath in editor_xpaths:
                elements = self.driver.find_elements(By.XPATH, ed_xpath)
                if elements and elements[0].is_displayed():
                    editor_el = elements[0]
                    break

            if not editor_el:
                logger.error("Could not find post text editor element.")
                return False

            editor_el.click()
            time.sleep(0.5)

            # Type text smoothly using clipboard/send_keys to preserve line breaks and formatting
            self.driver.execute_script("""
                var editor = arguments[0];
                var text = arguments[1];
                editor.innerText = text;
                editor.dispatchEvent(new Event('input', { bubbles: true }));
                editor.dispatchEvent(new Event('change', { bubbles: true }));
            """, editor_el, post_text)

            time.sleep(1)
            # Add a space and backspace to trigger LinkedIn React state synchronization
            editor_el.send_keys(Keys.SPACE)
            time.sleep(0.2)
            editor_el.send_keys(Keys.BACKSPACE)
            time.sleep(1)

            logger.info("Post text successfully inserted into editor!")

            # 4. Preview / Safety Pause or Direct Publish
            if dry_run:
                logger.info("=== MODO PRÉVIA ATIVO ===")
                logger.info("O post foi preparado na tela do Chrome para sua conferência.")
                if pymsgbox:
                    choice = pymsgbox.confirm(
                        "O post e a imagem foram preparados no LinkedIn!\n\nDeseja PUBLICAR agora?",
                        "Confirmação de Publicação",
                        ("Publicar", "Cancelar / Descartar")
                    )
                    if choice != "Publicar":
                        logger.info("Publicação cancelada pelo usuário.")
                        return False
                else:
                    time.sleep(5)

            # 5. Click "Publicar" / "Post"
            publish_xpaths = [
                "//button[contains(@class, 'share-actions__primary-action')]",
                "//button[contains(@class, 'artdeco-button--primary') and (contains(., 'Publicar') or contains(., 'Post'))]",
                "//button[contains(., 'Publicar') or contains(., 'Post')]"
            ]

            published = False
            for pub_xpath in publish_xpaths:
                btn = self.interactor.try_xpath(pub_xpath, click=True)
                if btn:
                    published = True
                    logger.info("Botão 'Publicar' clicado com sucesso!")
                    break

            self.interactor.sleep_buffer(3, 5)

            if published:
                logger.info("🎉 Publicação enviada com sucesso no LinkedIn!")
                return True
            else:
                logger.warning("Não foi possível acionar o botão de publicação final.")
                return False

        except Exception as e:
            logger.error(f"Erro durante publicação no LinkedIn: {e}", exc_info=True)
            return False

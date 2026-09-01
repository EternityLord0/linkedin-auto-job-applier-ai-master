#!/usr/bin/env python
# publish_post.py
"""
Script interativo para criação e publicação automatizada de posts e artigos no LinkedIn
com suporte a anexação de banners visuais de alta conversão e modo de prévia.
"""
import os
import sys

from src.browser.driver_factory import create_driver
from src.browser.scraper import LinkedInScraper
from src.ai.ai_manager import AIManager
from src.ai.post_generator import PostGenerator, POST_TEMPLATES
from src.core.publisher import LinkedInPublisher
from src.utils.logger import logger


def display_menu():
    print("\n" + "=" * 65)
    print(" 🚀 PUBLICADOR AUTOMATIZADO DE CONTEÚDO NO LINKEDIN")
    print("=" * 65)
    print("Escolha o post que deseja publicar:\n")

    for i, t in enumerate(POST_TEMPLATES, 1):
        print(f"  [{i}] {t['title']}")
        print(f"      Banner padrão: {t['banner']}\n")

    print("  [5] ✍️  Gerar post personalizado sobre outro tema")
    print("  [6] ❌ Sair\n")
    print("=" * 65)


def list_available_banners():
    banners_dir = "banners"
    if not os.path.exists(banners_dir):
        return []
    return [os.path.join(banners_dir, f) for f in os.listdir(banners_dir) if f.endswith(('.jpg', '.jpeg', '.png'))]


def main():
    display_menu()
    choice = input("Digite o número da sua opção (1-6) [1]: ").strip() or "1"

    if choice == "6":
        print("Operação cancelada.")
        return

    post_text = ""
    selected_banner = None

    if choice in ["1", "2", "3", "4"]:
        template = POST_TEMPLATES[int(choice) - 1]
        post_text = template["content"]
        selected_banner = template["banner"]
        print(f"\n✅ Tema selecionado: '{template['title']}'")
    elif choice == "5":
        topic = input("\nQual o tema do post? (ex: Agentes autônomos em Python): ").strip()
        if not topic:
            topic = "Engenharia de IA e Full Stack"
        ai_mgr = AIManager()
        gen = PostGenerator(ai_mgr)
        print("\nGerando copy profissional...")
        post_text = gen.generate_custom_post(topic)
        selected_banner = "banners/4_AI_Architecture.jpg"
    else:
        print("Opção inválida.")
        return

    print("\n--- PRÉVIA DO TEXTO DO POST ---")
    print(post_text)
    print("--------------------------------")

    # Banner selection option
    change_banner = input(f"\nBanner atual: '{selected_banner}'. Deseja alterar o banner? (s/N): ").strip().lower()
    if change_banner == 's':
        banners = list_available_banners()
        print("\nBanners disponíveis:")
        for idx, b in enumerate(banners, 1):
            print(f"  [{idx}] {b}")
        b_choice = input(f"Selecione o número do banner (1-{len(banners)}): ").strip()
        try:
            selected_banner = banners[int(b_choice) - 1]
            print(f"Banner definido: {selected_banner}")
        except:
            print("Seleção mantida no padrão.")

    # Dry-run option (review before posting)
    review_mode = input("\nDeseja pausar no navegador para REVISAR antes de publicar? (S/n) [S]: ").strip().lower()
    dry_run = review_mode != 'n'

    print("\nIniciando navegador Chrome...")
    driver, actions, wait = create_driver()
    scraper = LinkedInScraper(driver, actions, wait)
    publisher = LinkedInPublisher(scraper)

    try:
        success = publisher.create_post(
            post_text=post_text,
            banner_path=selected_banner,
            dry_run=dry_run
        )
        if success:
            print("\n✅ Processo de publicação concluído com sucesso!")
        else:
            print("\n⚠️ A publicação não foi concluída.")
    finally:
        input("\nPressione ENTER para fechar o navegador...")
        try:
            driver.quit()
        except:
            pass


if __name__ == "__main__":
    main()

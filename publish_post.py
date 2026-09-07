#!/usr/bin/env python
# publish_post.py
"""
Script interativo para criação e publicação automatizada de posts no LinkedIn.
Suporta importação rápida de cópias do Gemini Spark (post_hoje.txt), templates
de autoridade, geração por IA e anexação inteligente de banners visuais.
"""
import os
import sys

from src.browser.driver_factory import create_driver
from src.browser.scraper import LinkedInScraper
from src.ai.ai_manager import AIManager
from src.ai.post_generator import PostGenerator, POST_TEMPLATES
from src.core.publisher import LinkedInPublisher
from src.utils.logger import logger


POST_HOJE_FILE = "post_hoje.txt"


def auto_select_banner(text: str) -> str:
    """Seleciona automaticamente o banner mais alinhado ao conteúdo do post."""
    t = text.lower()
    if any(k in t for k in ["arquitetura", "llm", "inteligência artificial", "ia ", "agente", "openai", "deep learning", "prompt"]):
        return "banners/4_AI_Architecture.jpg"
    elif any(k in t for k in ["polyanalytics", "mercado preditivo", "probabilidade", "rede"]):
        return "banners/7_Polyanalytics_Network.jpg"
    elif any(k in t for k in ["react", "typescript", "full stack", "fullstack", "front", "backend", "código", "programação"]):
        return "banners/5_Code_Fullstack.jpg"
    elif any(k in t for k in ["power bi", "dax", "dashboard", "analytics", "faturamento", "inteligência de dados", "e-commerce"]):
        return "banners/3_Data_Waves_Probability.jpg"
    elif any(k in t for k in ["neural", "redes neurais", "lattice", "conexões"]):
        return "banners/2_Neural_Lattice.jpg"
    elif any(k in t for k in ["minimal", "clean", "simplicidade", "disciplina"]):
        return "banners/6_Vercel_Minimal.jpg"
    return "banners/1_Glassmorphism_Tech.jpg"


def list_available_banners():
    banners_dir = "banners"
    if not os.path.exists(banners_dir):
        return []
    return [os.path.join(banners_dir, f) for f in os.listdir(banners_dir) if f.endswith(('.jpg', '.jpeg', '.png'))]


def get_post_from_file_or_input() -> str:
    """Lê o post salvo em post_hoje.txt ou permite colar diretamente."""
    if os.path.exists(POST_HOJE_FILE):
        with open(POST_HOJE_FILE, "r", encoding="utf-8") as f:
            content = f.read().strip()
        
        # Ignora se for o texto de instrução inicial padrão
        if content and "Cole aqui o texto do seu post gerado no Gemini Spark!" not in content:
            print(f"\n📄 Encontrado conteúdo salvo em '{POST_HOJE_FILE}' ({len(content)} caracteres):")
            preview = content[:200] + ("..." if len(content) > 200 else "")
            print(f"\n--- INÍCIO DA PRÉVIA ---\n{preview}\n--- FIM DA PRÉVIA ---\n")
            use_file = input("Deseja usar este texto de 'post_hoje.txt'? (S/n) [S]: ").strip().lower()
            if use_file != 'n':
                return content

    print("\n✍️  Digite ou cole o texto do seu post (pressione ENTER duas vezes ou digite 'FIM' em uma linha vazia para concluir):")
    lines = []
    while True:
        try:
            line = input()
            if line.strip() == "FIM":
                break
            if not line and lines and lines[-1] == "":
                break
            lines.append(line)
        except EOFError:
            break
    
    post = "\n".join(lines).strip()
    return post


def display_menu():
    print("\n" + "=" * 68)
    print(" 🚀 PUBLICADOR AUTOMATIZADO DE CONTEÚDO NO LINKEDIN")
    print("=" * 68)
    print("Como deseja criar a sua publicação hoje?\n")
    print("  [1] 📋 Publicar post do Gemini Spark (carregar post_hoje.txt ou colar)")
    print("  [2] 🏆 Template: Arquitetura de Produtos com IA & LLMs")
    print("  [3] ⚡ Template: Polyanalytics (Full Stack Moderno & Supabase)")
    print("  [4] 📊 Template: Inteligência de Dados & BI (+50% Faturamento)")
    print("  [5] 🛠️ Template: Engenharia de Software & Foco")
    print("  [6] 🤖 Gerar copy personalizada com Gemini sobre um tema livre")
    print("  [0] ❌ Sair\n")
    print("=" * 68)


def main():
    display_menu()
    choice = input("Digite a sua opção (0-6) [1]: ").strip() or "1"

    if choice == "0":
        print("Operação cancelada.")
        return

    post_text = ""
    selected_banner = None

    if choice == "1":
        post_text = get_post_from_file_or_input()
        if not post_text:
            print("Nenhum texto informado. Cancelando.")
            return
        selected_banner = auto_select_banner(post_text)

    elif choice in ["2", "3", "4", "5"]:
        idx_map = {"2": 0, "3": 1, "4": 2, "5": 3}
        template = POST_TEMPLATES[idx_map[choice]]
        post_text = template["content"]
        selected_banner = template["banner"]
        print(f"\n✅ Template selecionado: '{template['title']}'")

    elif choice == "6":
        topic = input("\nQual o tema do post? (ex: Agentes autônomos com LangGraph): ").strip()
        if not topic:
            topic = "Engenharia de IA e Full Stack Moderno"
        ai_mgr = AIManager()
        gen = PostGenerator(ai_mgr)
        print("\nGerando copy profissional com IA...")
        post_text = gen.generate_custom_post(topic)
        selected_banner = auto_select_banner(post_text)
    else:
        print("Opção inválida.")
        return

    print("\n" + "-" * 40)
    print("PRÉVIA DO TEXTO DO POST:")
    print("-" * 40)
    print(post_text)
    print("-" * 40)

    # Banner selection option
    print(f"\n🖼️  Banner selecionado: '{selected_banner}'")
    change_banner = input("Deseja trocar o banner? (s/N) [N]: ").strip().lower()
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

    # Dry-run / preview option
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
            print("\n🎉 Processo de publicação concluído com sucesso!")
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

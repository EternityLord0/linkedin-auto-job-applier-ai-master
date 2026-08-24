"""
Scraper do Perfil LinkedIn usando o perfil REAL do Chrome (com sessão já logada).
Não requer login manual — usa os cookies existentes no seu Chrome.
"""
import sys
import time
import os

try:
    import undetected_chromedriver as uc
except ImportError:
    print("Instale: pip install undetected-chromedriver")
    sys.exit(1)

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def get_real_chrome_profile():
    """Localiza o perfil padrão do Chrome com os cookies de sessão."""
    local_app = os.getenv('LOCALAPPDATA', '')
    path = os.path.join(local_app, 'Google', 'Chrome', 'User Data')
    if os.path.exists(path):
        return path
    return None


def scroll_and_expand(driver):
    """Scroll lento + clica em todos os botões de 'exibir mais'."""
    last_height = driver.execute_script("return document.body.scrollHeight")
    for attempt in range(8):
        driver.execute_script("window.scrollBy(0, window.innerHeight * 1.5);")
        time.sleep(1.5)

        try:
            btns = driver.find_elements(By.XPATH,
                "//button[contains(normalize-space(.), 'Ver mais') or "
                "contains(normalize-space(.), 'Exibir mais') or "
                "contains(normalize-space(.), 'Show more') or "
                "contains(normalize-space(.), 'see more') or "
                "contains(normalize-space(.), 'Mostrar') or "
                "contains(normalize-space(.), 'Exibir')]"
            )
            for btn in btns:
                try:
                    driver.execute_script("arguments[0].click();", btn)
                    time.sleep(0.3)
                except:
                    pass
        except:
            pass

        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(2)


def extract_section_text(driver, section_id):
    """Extrai texto de uma section pelo id do div âncora."""
    selectors = [
        f"//*[@id='{section_id}']/ancestor::section",
        f"//section[.//*[@id='{section_id}']]",
        f"//div[@id='{section_id}']/..",
    ]
    for sel in selectors:
        try:
            el = driver.find_element(By.XPATH, sel)
            text = driver.execute_script("return arguments[0].innerText;", el)
            if text and len(text.strip()) > 10:
                return text.strip()
        except:
            continue
    return None


def main():
    profile_path = get_real_chrome_profile()
    if not profile_path:
        print("ERRO: Perfil do Chrome não encontrado.")
        sys.exit(1)

    print(f"Usando perfil Chrome: {profile_path}")
    print("IMPORTANTE: Feche TODAS as janelas do Chrome antes de continuar!")
    input("Pressione ENTER depois de fechar o Chrome...")

    options = uc.ChromeOptions()
    options.add_argument(f"--user-data-dir={profile_path}")
    options.add_argument("--profile-directory=Default")
    options.add_argument("--no-first-run")
    options.add_argument("--no-default-browser-check")

    print("Abrindo Chrome com perfil real...")
    driver = uc.Chrome(options=options)
    wait = WebDriverWait(driver, 15)
    driver.maximize_window()

    print("Acessando perfil: https://www.linkedin.com/in/gabrielhvcaldeira")
    driver.get("https://www.linkedin.com/in/gabrielhvcaldeira")
    time.sleep(8)

    # Verifica se está logado
    if "authwall" in driver.current_url or "login" in driver.current_url:
        print("LinkedIn pediu login. Faça o login manualmente no Chrome aberto.")
        input("Pressione ENTER após realizar o login manualmente...")
        driver.get("https://www.linkedin.com/in/gabrielhvcaldeira")
        time.sleep(8)

    print("Scrollando e expandindo seções...")
    scroll_and_expand(driver)

    output = ""
    SEPARATOR = "\n" + "=" * 60 + "\n"

    # --- Header (nome, título) via texto da página inteira ---
    print("Extraindo HEADER...")
    try:
        name_el = driver.find_element(By.XPATH, "//h1")
        name = name_el.text.strip()
        headline_els = driver.find_elements(By.XPATH, "//div[contains(@class,'text-body-medium break-words')]")
        headline = headline_els[0].text.strip() if headline_els else "N/D"
        location_els = driver.find_elements(By.XPATH, "//span[contains(@class,'text-body-small')]")
        location = location_els[0].text.strip() if location_els else "N/D"
        output += f"{SEPARATOR}### NOME & TÍTULO ###\nNome: {name}\nTítulo: {headline}\nLocalização: {location}\n"
    except Exception as e:
        output += f"{SEPARATOR}### NOME & TÍTULO (erro: {e}) ###\n"

    # --- Extrai seções por ID ---
    sections = [
        ("about", "SOBRE"),
        ("featured", "EM DESTAQUE"),
        ("experience", "EXPERIÊNCIAS PROFISSIONAIS"),
        ("education", "EDUCAÇÃO"),
        ("licenses_and_certifications", "LICENÇAS E CERTIFICAÇÕES"),
        ("skills", "COMPETÊNCIAS / SKILLS"),
        ("projects", "PROJETOS"),
        ("languages", "IDIOMAS"),
        ("recommendations", "RECOMENDAÇÕES"),
        ("honors_and_awards", "CONQUISTAS E PRÊMIOS"),
        ("publications", "PUBLICAÇÕES"),
        ("volunteer_experience", "VOLUNTARIADO"),
        ("courses", "CURSOS"),
    ]

    for section_id, label in sections:
        print(f"Extraindo {label}...")
        text = extract_section_text(driver, section_id)
        if text:
            output += f"{SEPARATOR}### {label} ###\n{SEPARATOR}{text}\n"
        else:
            output += f"{SEPARATOR}### {label} - (seção não encontrada ou vazia) ###\n"

    # Salva
    with open("meu_perfil_completo.txt", "w", encoding="utf-8") as f:
        f.write(output)

    print(f"\n{'='*60}")
    print("✅ Perfil extraído com sucesso! Arquivo: meu_perfil_completo.txt")
    print(f"{'='*60}")

    driver.quit()


if __name__ == "__main__":
    main()

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import Select
import time, json
import re

# Setup do Selenium
options = webdriver.ChromeOptions()
options.add_argument("--headless")  # tirar se quiser ver o navegador
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
wait = WebDriverWait(driver, 10)

base_url = "https://servicos.tcesc.tc.br/contracheque_externo/index.php"

def get_popup_url(onclick_attr):
    match = re.search(r"popup\('(.*?)'\)", onclick_attr)
    if match:
        return f"https://servicos.tcesc.tc.br/contracheque_externo/{match.group(1)}"
    return None

def extract_servidor_detail(url):
    try:
        detail_driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        detail_driver.get(url)
        time.sleep(1)
        content = detail_driver.page_source
        detail_driver.quit()
        return content
    except Exception as e:
        print("Erro ao acessar página do servidor:", e)
        return None

def extract_data(categoria_value, tipo_nome):
    driver.get(base_url)
    wait.until(EC.presence_of_element_located((By.NAME, "cd_categoria_funcional")))

    # Seleciona categoria (Ativos ou Inativos)
    select = Select(driver.find_element(By.NAME, "cd_categoria_funcional"))
    select.select_by_value(categoria_value)
    time.sleep(1)

    # Clica em Pesquisar
    btn = driver.find_element(By.XPATH, "//input[@type='submit' and @value='Pesquisar']")
    btn.click()
    time.sleep(2)

    servidores = []

    # Encontra todos os botões com onclick que chama popup
    elementos = driver.find_elements(By.XPATH, "//a[contains(@onclick, 'popup')]")

    for elem in elementos:
        try:
            nome = elem.text.strip()
            onclick = elem.get_attribute("onclick")
            folha_url = get_popup_url(onclick)
            folha_html = extract_servidor_detail(folha_url)

            servidores.append({
                "tipo": tipo_nome,
                "nome": nome,
                "url_folha": folha_url,
                "html_folha": folha_html
            })

        except Exception as e:
            print("Erro com servidor:", e)
            continue

    return servidores

# Extrai ativos e inativos
ativos = extract_data("3, 1, 8, 6, 9, 5, 12, 16, 17, 19", "ATIVO")
inativos = extract_data("2, 4, 7, 10, 15, 18", "INATIVO")

# Junta e salva tudo
todos = ativos + inativos

with open("servidores_tce_sc_completo.json", "w", encoding="utf-8") as f:
    json.dump(todos, f, ensure_ascii=False, indent=4)

driver.quit()
print("Scraping finalizado. Dados salvos em servidores_tce_sc_completo.json")

import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# --- Configuração do navegador headless ---
options = Options()
options.add_argument("--headless=new")
driver = webdriver.Chrome(options=options)
wait = WebDriverWait(driver, 20)
driver.get("https://tcerjtransparencia.admrh.inf.br/rhsysportaltransp/")

# Espera a tabela aparecer
wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table.table-selectable tbody tr")))

servidores_data = []
pagina = 1

def parse_valor_br(valor_str):
    return float(valor_str.replace(".", "").replace(",", ".").strip())

while True:
    print(f"🔄 Lendo página {pagina}...")

    rows = driver.find_elements(By.CSS_SELECTOR, "table.table-selectable tbody tr")

    for i, row in enumerate(rows):
        try:
            nome = row.find_element(By.CSS_SELECTOR, "td[data-title='Nome']").text.strip()
            cargo = row.find_element(By.CSS_SELECTOR, "td[data-title='Cargo']").text.strip()
            tipo = row.find_element(By.CSS_SELECTOR, "td[data-title='Vinculo']").text.strip()

            # Clica na linha
            driver.execute_script("arguments[0].scrollIntoView(true);", row)
            ActionChains(driver).move_to_element(row).click().perform()
            time.sleep(1.5)

            # Coleta dados detalhados no painel lateral
            total_blocks = driver.find_elements(By.CSS_SELECTOR, ".valores")
            proventos = []
            total_proventos = 0.0
            total_descontos = 0.0
            salario_liquido = 0.0

            for bloco in total_blocks:
                descricao = bloco.find_element(By.CSS_SELECTOR, ".column-string").text.strip()
                valor_str = bloco.find_element(By.CSS_SELECTOR, ".column-number").text.strip()
                valor = parse_valor_br(valor_str)

                if "deduções" in descricao.lower():
                    salario_liquido = valor
                elif "desconto" in descricao.lower():
                    total_descontos += valor
                    if valor > 0:
                        proventos.append({"descricao": descricao, "valor": valor_str})
                else:
                    total_proventos += valor
                    if valor > 0:
                        proventos.append({"descricao": descricao, "valor": valor_str})

            servidores_data.append({
                "nome": nome,
                "cargo": cargo,
                "tipo": tipo,
                "salario_liquido": f"{salario_liquido:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
                "total_proventos": f"{total_proventos:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
                "total_descontos": f"{total_descontos:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
                "proventos": proventos
            })

            # Fecha o painel com ESC
            ActionChains(driver).send_keys(u'\ue00c').perform()
            time.sleep(0.5)

        except Exception as e:
            print(f"⚠️ Erro ao processar servidor {i} na página {pagina}: {e}")
            continue

    try:
        # Localiza botão novamente a cada iteração (nunca reaproveita referência antiga)
        btn_proximo = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "a[title='Próxima']"))
        )

        if not btn_proximo.is_displayed() or "disabled" in btn_proximo.get_attribute("class"):
            break

        # Captura nome do primeiro servidor atual
        primeiro_nome_antes = driver.find_element(By.CSS_SELECTOR, "table.table-selectable tbody tr td[data-title='Nome']").text.strip()

        btn_proximo.click()

        # Espera até que o nome do primeiro servidor mude
        WebDriverWait(driver, 10).until(
            lambda d: d.find_element(By.CSS_SELECTOR, "table.table-selectable tbody tr td[data-title='Nome']").text.strip() != primeiro_nome_antes
        )

        pagina += 1
        time.sleep(1)

    except Exception as e:
        print(f"❌ Erro ao avançar para a próxima página: {e}")
        break
    
driver.quit()

# Salvar os dados
with open("servidores_tce_rj_estruturado.json", "w", encoding="utf-8") as f:
    json.dump(servidores_data, f, ensure_ascii=False, indent=2)

print(f"✅ Extraídos {len(servidores_data)} servidores.")

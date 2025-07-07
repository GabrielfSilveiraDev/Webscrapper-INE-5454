import requests
from bs4 import BeautifulSoup
import json

URL = "https://www.tce.sp.gov.br/transparencia-tcesp/gestao-pessoas/remuneracao/tabela"
TIPO = "ATIVO"
MES_ANO = "Abril - Ano: 2025"
servidores = []


# Base params, sem o page (vai adicionar depois)
base_params = {
    "vencimentos_ano": 1,
    "Mes": 4,
    "Situacao": 1,
    "Nome": "",
    "Identificacao": 1
}

def parse_num(txt):
    t = txt.strip().replace(".", "").replace(",", ".")
    try:
        return float(t)
    except:
        return 0.0


def extract_data(situacao, identificacao):
    global TIPO
    TIPO = situacao

    if TIPO == 1:
        TIPO = "ATIVO"
    else:
        TIPO = "INATIVO"

    page = 1
    params = base_params.copy()
    params["Situacao"] = situacao
    params["Identificacao"] = identificacao
    print(f"{params["Situacao"]}, {params["Identificacao"]}")
    global servidores
    while True:
        params["page"] = page
        res = requests.get(URL, params=params)

        soup = BeautifulSoup(res.text, "html.parser")

        tabela = soup.select_one("div.table-responsive table.table-hover.table-striped tbody")
        if not tabela:
            print(f"❌ Tabela não encontrada na página {page}. Parando.")
            break

        for tr in tabela.find_all("tr"):
            td = tr.find_all("td")
            if len(td) < 21:
                continue

            nome = td[3].text.strip()
            cargo = td[20].text.strip()

            proventos_raw = [
                ("Vencimentos", td[5].text.strip()),
                ("Vantagens Pessoais", td[6].text.strip()),
                ("Outras Verbas", td[7].text.strip()),
                ("Eventuais", td[11].text.strip()),
                ("Abono Permanência", td[12].text.strip()),
                ("Auxílios", td[13].text.strip()),
                ("1/3 Férias", td[14].text.strip()),
                ("13º Salário", td[16].text.strip()),
                ("13º Abono", td[17].text.strip()),
            ]
            proventos = [{"descricao": desc, "valor": val} for desc, val in proventos_raw if parse_num(val) != 0]

            descontos_raw = [
                ("Redutor", td[8].text.strip()),
                ("Descontos Legais", td[10].text.strip()),
                ("Desconto Férias", td[15].text.strip()),
                ("Desconto 13º", td[18].text.strip()),
            ]
            descontos = [{"descricao": desc, "valor": val} for desc, val in descontos_raw if parse_num(val) != 0]

            total_desc = sum(parse_num(d["valor"]) for d in descontos)
            total_prov = td[9].text.strip()
            sal_liq = td[19].text.strip()

            servidores.append({
                "nome": nome,
                "admissao": "",
                "cargo": cargo,
                "mes_ano": MES_ANO,
                "proventos": proventos,
                "descontos": descontos,
                "total_proventos": total_prov,
                "total_descontos": f"{total_desc:.2f}",
                "salario_liquido": sal_liq,
                "tipo": TIPO,
                "url_folha": res.url
            })

        # Check if "Próxima página" link exists
        next_page_link = soup.find("a", {"rel": "next"})
        if not next_page_link:
            print("✅ Última página atingida.")
            break
        else:
            page += 1

extract_data(1, 1)
# extract_data(1, 2)
# extract_data(1, 3)
extract_data(2, 1)
# extract_data(2, 2)
# extract_data(2, 3)

with open("servidores_tce_sp_estruturado.json", "w", encoding="utf-8") as f:
    json.dump(servidores, f, ensure_ascii=False, indent=4)

print(f"✅ Extraídos {len(servidores)} servidores no total.")

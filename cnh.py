import requests
from datetime import datetime
import colorama
from colorama import Fore, Style
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

colorama.init(autoreset=True)

API_URL = "https://api.bronxservices.net/consulta/dHJhdmVsZXI6VHJhdmVsZXI3N0A=/srs22/cpf/{cpf}"
API_HEADERS = {'Content-Type': 'application/json'}
CIDADES_INTERIOR = ["BALNEARIO BARRA DO SUL", "BARREIRAS", "ARAGUAINA", "ITAPEMA", "CATANDUVA", "CAXIAS DO SUL"]
PROFISSOES_RELEVANTES = ["COMERCIANTE", "AGRICULTORA", "AUTÔNOMA", "MOTORISTA", "TAXISTA", "CAMINHONEIRA"]
THREADS = 30  # ajuste conforme seu hardware/limite

lock = Lock()  # para evitar conflito de escrita

def to_float(valor):
    try:
        return float(str(valor).replace(',', '.'))
    except:
        return 0.0

def prob_nao_tem_cnh(dados):
    hoje = datetime.now()
    nasc = datetime.strptime(dados["NASC"].split(" ")[0], "%Y-%m-%d")
    idade = hoje.year - nasc.year - ((hoje.month, hoje.day) < (nasc.month, nasc.day))
    renda = to_float(dados.get("RENDA", "0"))
    sexo = dados.get("SEXO", "F")
    cidade = ""
    mosaic = dados.get("CD_MOSAIC_NOVO", "")
    profissao = (dados.get("CBO", "") or "").upper()
    rg = dados.get("RG", "")
    if "enderecos" in dados and dados["enderecos"]:
        cidade = (dados["enderecos"][0].get("CIDADE", "") or "").upper()
    score = 0
    if idade < 18:
        return True, 100
    if 18 <= idade <= 21:
        score += 10
    if renda < 1200:
        score += 10
    if sexo == "F":
        score += 2
    if mosaic in ["D12", "D13"]:
        score += 5
    if not rg or rg.lower().startswith("sem"):
        score += 3
    if (sexo == "F" and idade > 45 and cidade in CIDADES_INTERIOR and renda < 1500):
        score += 5
    if profissao and any(prof in profissao for prof in PROFISSOES_RELEVANTES):
        score -= 2
    return (score > 19), score

def consulta_api(cpf):
    url = API_URL.format(cpf=cpf)
    try:
        resp = requests.get(url, headers=API_HEADERS, timeout=10)
        if resp.status_code == 200:
            retorno = resp.json()
            if "dados" in retorno:
                return retorno
        return None
    except Exception:
        return None

def get_telefone(retorno):
    if "telefones" in retorno and retorno["telefones"]:
        tel_prio1 = [t for t in retorno["telefones"] if str(t.get("PRIORIDADE", "")).strip() == "1"]
        if tel_prio1:
            t = tel_prio1[0]
        else:
            t = retorno["telefones"][0]
        ddd = str(t.get("DDD", "")).strip()
        tel = str(t.get("TELEFONE", "")).strip()
        if ddd and tel:
            return f"({ddd}) {tel}"
        return tel or ""
    return ""

def print_banner():
    banner = f"""
{Fore.CYAN}{Style.BRIGHT}
████████╗██████╗  █████╗ ██╗   ██╗███████╗██╗     ███████╗██████╗      ██████╗ ██████╗ ██████╗ ███████╗██████╗ 
╚══██╔══╝██╔══██╗██╔══██╗██║   ██║██╔════╝██║     ██╔════╝██╔══██╗    ██╔════╝██╔═══██╗██╔══██╗██╔════╝██╔══██╗
   ██║   ██████╔╝███████║██║   ██║█████╗  ██║     █████╗  ██████╔╝    ██║     ██║   ██║██║  ██║█████╗  ██████╔╝
   ██║   ██╔══██╗██╔══██║██║   ██║██╔══╝  ██║     ██╔══╝  ██╔══██╗    ██║     ██║   ██║██║  ██║██╔══╝  ██╔══██╗
   ██║   ██║  ██║██║  ██║╚██████╔╝███████╗███████╗███████╗██║  ██║    ╚██████╗╚██████╔╝██████╔╝███████╗██║  ██║
   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚══════╝╚══════╝╚═╝  ╚═╝     ╚═════╝ ╚═════╝ ╚═════╝ ╚══════╝╚═╝  ╚═╝
{Style.RESET_ALL}
"""
    print(banner)

def process_cpf(cpf):
    resposta = consulta_api(cpf)
    if not resposta:
        return ("SKIP", cpf, "", "")
    dados = resposta["dados"]
    resultado, _ = prob_nao_tem_cnh(dados)
    nome = dados.get("NOME", "").strip()
    telefone = get_telefone(resposta)
    saida = f"{cpf},{nome},{telefone}"
    if resultado:
        return ("LIVE", cpf, nome, telefone)
    else:
        return ("DIE", cpf, "", "")

def main():
    os.system('cls' if os.name == 'nt' else 'clear')
    print_banner()
    # Abertura do arquivo já em modo append
    with open('lista.txt', 'r') as f:
        cpfs = [linha.strip() for linha in f if linha.strip()]

    with ThreadPoolExecutor(max_workers=THREADS) as executor:
        futures = {executor.submit(process_cpf, cpf): cpf for cpf in cpfs}
        for future in as_completed(futures):
            tipo, cpf, nome, telefone = future.result()
            if tipo == "LIVE":
                saida = f"{cpf},{nome},{telefone}"
                print(f"{Fore.GREEN}LIVE ; {saida}{Style.RESET_ALL}")
                with lock:
                    with open('live.txt', 'a', encoding='utf-8') as livefile:
                        livefile.write(f"{saida}\n")
            elif tipo == "DIE":
                print(f"{Fore.RED}DIE ; {cpf}{Style.RESET_ALL}")
            # SKIP = erro, não exibe nada

if __name__ == '__main__':
    main()

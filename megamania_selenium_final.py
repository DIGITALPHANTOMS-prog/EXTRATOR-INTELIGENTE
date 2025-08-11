# megamania_selenium_final.py
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import undetected_chromedriver as uc
import requests
import json
import time
import re

class MegaManiaSeleniumChecker:
    def __init__(self):
        self.base_url = "https://consulta.megamaniadasorte.com.br"
        
    def format_cpf(self, cpf):
        """Formata CPF com pontos e traço"""
        cpf_clean = re.sub(r'\D', '', cpf)
        if len(cpf_clean) != 11:
            return None
        return f"{cpf_clean[:3]}.{cpf_clean[3:6]}.{cpf_clean[6:9]}-{cpf_clean[9:]}"
    
    def setup_driver(self):
        """Configura driver Chrome indetectável"""
        options = uc.ChromeOptions()
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--start-maximized")
        
        # Descomente para modo headless (sem interface)
        # options.add_argument("--headless")
        
        driver = uc.Chrome(options=options)
        return driver
    
    def wait_for_turnstile(self, driver, timeout=30):
        """Aguarda o Turnstile ser resolvido"""
        try:
            # Aguarda o iframe do Turnstile aparecer
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".cf-turnstile iframe"))
            )
            print("   ⏳ Aguardando Cloudflare Turnstile...")
            
            # Aguarda o Turnstile ser resolvido
            start_time = time.time()
            while time.time() - start_time < timeout:
                try:
                    # Verifica se o Turnstile foi resolvido
                    driver.switch_to.default_content()
                    token_field = driver.find_element(By.CSS_SELECTOR, "input[name='cf-turnstile-response']")
                    if token_field.get_attribute("value"):
                        print("   ✓ Turnstile resolvido!")
                        return True
                except:
                    pass
                time.sleep(0.5)
                
        except Exception as e:
            print(f"   ⚠️ Erro com Turnstile: {str(e)[:50]}")
        
        return False
    
    def get_jwt_token(self, driver, cpf):
        """Obtém o token JWT após preencher o formulário"""
        cpf_formatted = self.format_cpf(cpf)
        if not cpf_formatted:
            return None
            
        try:
            # Navega para a página
            driver.get(f"{self.base_url}/meus-cupons")
            time.sleep(2)
            
            # Aguarda o formulário carregar
            wait = WebDriverWait(driver, 10)
            cpf_input = wait.until(EC.presence_of_element_located((By.ID, "cpf")))
            
            # Preenche o CPF
            cpf_input.clear()
            cpf_input.send_keys(cpf_formatted)
            time.sleep(0.5)
            
            # Aguarda o Turnstile
            self.wait_for_turnstile(driver)
            
            # Encontra e clica no botão
            button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']")))
            button.click()
            
            # Aguarda redirecionamento
            time.sleep(3)
            
            # Verifica se foi redirecionado e pega o token da URL
            current_url = driver.current_url
            if "token=" in current_url:
                # Extrai o token da URL
                import urllib.parse
                parsed = urllib.parse.urlparse(current_url)
                params = urllib.parse.parse_qs(parsed.query)
                token = params.get('token', [None])[0]
                return token
            
            return None
            
        except Exception as e:
            print(f"   ❌ Erro ao obter token: {str(e)[:50]}")
            return None
    
    def check_cpf_with_token(self, cpf, token):
        """Verifica cupons usando o token JWT"""
        cpf_formatted = self.format_cpf(cpf)
        if not cpf_formatted or not token:
            return "ERROR", "CPF ou token inválido", 0
            
        try:
            # Faz a requisição com o token
            url = f"{self.base_url}/meus-cupons/ver"
            params = {
                'cpf': cpf_formatted,
                'token': token,
                '_data': 'routes/meus-cupons.ver'
            }
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "application/json",
                "Referer": f"{self.base_url}/meus-cupons"
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=10)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if 'couponsSummary' in data:
                        total = data['couponsSummary'].get('totalCoupons', 0)
                        if total > 0:
                            return "LIVE", f"{total} cupons", total
                        else:
                            return "DIE", "Sem cupons", 0
                except:
                    pass
                    
            return "ERROR", f"Status {response.status_code}", 0
            
        except Exception as e:
            return "ERROR", str(e)[:50], 0
    
    def process_list(self, cpf_list):
        """Processa lista de CPFs"""
        print(f"\n🎯 MegaMania Checker v8.0 SELENIUM")
        print(f"📍 Site: {self.base_url}")
        print(f"\n📋 {len(cpf_list)} CPFs carregados")
        
        driver = self.setup_driver()
        
        try:
            # Estatísticas
            total_live = 0
            total_die = 0
            total_error = 0
            total_cupons = 0
            
            with open("live.txt", "w") as live_file:
                for i, cpf in enumerate(cpf_list, 1):
                    print(f"\n[{i}/{len(cpf_list)}] Verificando: {self.format_cpf(cpf)}")
                    
                    # Obtém token JWT
                    token = self.get_jwt_token(driver, cpf)
                    
                    if token:
                        # Verifica cupons com o token
                        status, msg, cupons = self.check_cpf_with_token(cpf, token)
                        
                        if status == "LIVE":
                            total_live += 1
                            total_cupons += cupons
                            live_file.write(f"{cpf}\n")
                            live_file.flush()
                            print(f"   ✅ LIVE - {msg}")
                        elif status == "DIE":
                            total_die += 1
                            print(f"   ❌ DIE - {msg}")
                        else:
                            total_error += 1
                            print(f"   ⚠️ {status} - {msg}")
                    else:
                        total_die += 1
                        print(f"   ❌ DIE - Não conseguiu obter token")
                    
                    # Delay entre verificações
                    if i < len(cpf_list):
                        time.sleep(2)
            
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
            
        finally:
            driver.quit()

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
    checker = MegaManiaSeleniumChecker()
    checker.process_list(cpf_list)

if __name__ == "__main__":
    main()
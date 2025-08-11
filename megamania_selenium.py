# megamania_selenium.py
"""
Script para consultar cupons no MegaMania usando Selenium
Lida com Cloudflare Turnstile automaticamente
"""

import time
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import pandas as pd
from datetime import datetime

class MegaManiaConsultor:
    def __init__(self, headless=False):
        """Inicializa o navegador"""
        self.options = Options()
        if headless:
            self.options.add_argument('--headless')
        self.options.add_argument('--disable-gpu')
        self.options.add_argument('--no-sandbox')
        self.options.add_argument('--disable-dev-shm-usage')
        self.options.add_argument('--window-size=1920,1080')
        
        # User agent real
        self.options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        self.driver = None
        self.wait = None
        
    def iniciar(self):
        """Inicia o driver do Chrome"""
        try:
            self.driver = webdriver.Chrome(options=self.options)
            self.wait = WebDriverWait(self.driver, 20)
            print("✅ Navegador iniciado com sucesso!")
            return True
        except Exception as e:
            print(f"❌ Erro ao iniciar navegador: {e}")
            return False
            
    def formatar_cpf(self, cpf):
        """Formata CPF para o padrão XXX.XXX.XXX-XX"""
        cpf_clean = re.sub(r'\D', '', cpf)
        return f"{cpf_clean[:3]}.{cpf_clean[3:6]}.{cpf_clean[6:9]}-{cpf_clean[9:]}"
        
    def consultar_cpf(self, cpf):
        """Consulta um CPF no site"""
        cpf_formatted = self.formatar_cpf(cpf)
        print(f"\n🔍 Consultando CPF: {cpf_formatted}")
        
        try:
            # Acessa a página
            url = f"https://consulta.megamaniadasorte.com.br/meus-cupons?cpf={cpf_formatted}"
            self.driver.get(url)
            time.sleep(2)
            
            # Preenche o CPF se necessário
            try:
                cpf_input = self.wait.until(EC.presence_of_element_located((By.ID, "cpf")))
                cpf_input.clear()
                cpf_input.send_keys(cpf_formatted)
                print("📝 CPF preenchido no formulário")
            except:
                print("ℹ️ Campo CPF não encontrado ou já preenchido")
                
            # Aguarda o Turnstile carregar e resolver
            print("⏳ Aguardando Cloudflare Turnstile...")
            time.sleep(3)  # Tempo para o Turnstile carregar
            
            # Procura o botão de continuar
            try:
                continuar_btn = self.wait.until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Continuar')]"))
                )
                
                # Aguarda o Turnstile ser resolvido (botão habilitado)
                max_tentativas = 30
                tentativa = 0
                while tentativa < max_tentativas:
                    if not continuar_btn.get_attribute('disabled'):
                        print("✅ Turnstile resolvido!")
                        break
                    time.sleep(1)
                    tentativa += 1
                    
                if tentativa >= max_tentativas:
                    print("⚠️ Timeout esperando Turnstile")
                    return None
                    
                # Clica no botão
                continuar_btn.click()
                print("🖱️ Botão Continuar clicado")
                
            except Exception as e:
                print(f"❌ Erro ao clicar em Continuar: {e}")
                return None
                
            # Aguarda a página carregar
            time.sleep(3)
            
            # Verifica se foi para a página de resultados
            current_url = self.driver.current_url
            if '/ver' in current_url or 'cupons' in self.driver.page_source.lower():
                return self.extrair_dados()
            else:
                print("⚠️ Não foi redirecionado para os resultados")
                return None
                
        except Exception as e:
            print(f"❌ Erro na consulta: {e}")
            return None
            
    def extrair_dados(self):
        """Extrai os dados da página de resultados"""
        try:
            # Pega o HTML da página
            page_source = self.driver.page_source
            
            # Procura por padrões de cupons/títulos
            resultado = {
                'tem_cupons': False,
                'quantidade': 0,
                'numeros': [],
                'texto_completo': ''
            }
            
            # Busca texto da página
            try:
                body = self.driver.find_element(By.TAG_NAME, 'body')
                texto = body.text
                resultado['texto_completo'] = texto
                
                # Procura por números (possíveis quantidades)
                numeros = re.findall(r'\b(\d+)\s*(?:cupons?|títulos?)\b', texto, re.IGNORECASE)
                if numeros:
                    resultado['quantidade'] = int(numeros[0])
                    resultado['tem_cupons'] = resultado['quantidade'] > 0
                    
                # Procura por mensagens de "não possui"
                if re.search(r'não\s+possui|nenhum|zero|0\s*cupons?|0\s*títulos?', texto, re.IGNORECASE):
                    resultado['tem_cupons'] = False
                    resultado['quantidade'] = 0
                    
                print(f"📊 Resultado: {resultado['quantidade']} cupons/títulos")
                
            except Exception as e:
                print(f"⚠️ Erro ao extrair texto: {e}")
                
            return resultado
            
        except Exception as e:
            print(f"❌ Erro ao extrair dados: {e}")
            return None
            
    def processar_lista(self, arquivo_cpfs, arquivo_saida='resultados_megamania.csv'):
        """Processa uma lista de CPFs"""
        # Lê os CPFs
        with open(arquivo_cpfs, 'r') as f:
            cpfs = [linha.strip() for linha in f if linha.strip()]
            
        print(f"\n📋 Total de CPFs para processar: {len(cpfs)}")
        
        resultados = []
        
        for i, cpf in enumerate(cpfs, 1):
            print(f"\n[{i}/{len(cpfs)}]", end='')
            
            resultado = self.consultar_cpf(cpf)
            
            if resultado:
                resultados.append({
                    'cpf': self.formatar_cpf(cpf),
                    'tem_cupons': resultado['tem_cupons'],
                    'quantidade': resultado['quantidade'],
                    'data_consulta': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })
            else:
                resultados.append({
                    'cpf': self.formatar_cpf(cpf),
                    'tem_cupons': None,
                    'quantidade': None,
                    'data_consulta': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'erro': True
                })
                
            # Salva parcialmente a cada 10 consultas
            if i % 10 == 0:
                df = pd.DataFrame(resultados)
                df.to_csv(arquivo_saida, index=False)
                print(f"\n💾 Salvando progresso... ({i} CPFs processados)")
                
            # Delay entre consultas
            time.sleep(2)
            
        # Salva resultado final
        df = pd.DataFrame(resultados)
        df.to_csv(arquivo_saida, index=False)
        print(f"\n\n✅ Processamento concluído! Resultados salvos em: {arquivo_saida}")
        
        # Estatísticas
        total_com_cupons = sum(1 for r in resultados if r.get('tem_cupons') == True)
        total_sem_cupons = sum(1 for r in resultados if r.get('tem_cupons') == False)
        total_erros = sum(1 for r in resultados if r.get('erro'))
        
        print(f"\n📊 Estatísticas:")
        print(f"   - Com cupons: {total_com_cupons}")
        print(f"   - Sem cupons: {total_sem_cupons}")
        print(f"   - Erros: {total_erros}")
        
        return df
        
    def fechar(self):
        """Fecha o navegador"""
        if self.driver:
            self.driver.quit()
            print("\n👋 Navegador fechado")

# Exemplo de uso
if __name__ == "__main__":
    print("🎰 MegaMania Consultor - Versão Selenium")
    print("="*50)
    
    consultor = MegaManiaConsultor(headless=False)  # Use True para modo sem janela
    
    if consultor.iniciar():
        # Teste com um CPF
        resultado = consultor.consultar_cpf("92972373987")
        if resultado:
            print(f"\nResultado do teste:")
            print(f"  Tem cupons: {resultado['tem_cupons']}")
            print(f"  Quantidade: {resultado['quantidade']}")
            
        # Para processar uma lista:
        # consultor.processar_lista('cpfs.txt', 'resultados.csv')
        
        consultor.fechar()
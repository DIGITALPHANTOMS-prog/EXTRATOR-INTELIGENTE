# megamania_api.py
"""
Script para consultar MegaMania tentando simular as requisições do navegador
"""

import requests
import re
import time
import json
from datetime import datetime
import urllib3

urllib3.disable_warnings()

class MegaManiaAPI:
    def __init__(self):
        self.session = requests.Session()
        self.base_url = "https://consulta.megamaniadasorte.com.br"
        
        # Headers padrão do navegador
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Cache-Control": "max-age=0"
        }
        
        self.session.headers.update(self.headers)
        
    def formatar_cpf(self, cpf):
        """Formata CPF para XXX.XXX.XXX-XX"""
        cpf_clean = re.sub(r'\D', '', cpf)
        return f"{cpf_clean[:3]}.{cpf_clean[3:6]}.{cpf_clean[6:9]}-{cpf_clean[9:]}"
        
    def obter_token_turnstile(self, sitekey):
        """
        Tenta obter um token do Turnstile
        Nota: Esta é uma demonstração - em produção seria necessário um serviço de resolução
        """
        print("⚠️ Turnstile detectado. Token necessário.")
        
        # Aqui você poderia integrar com serviços como:
        # - 2captcha
        # - Anti-Captcha
        # - CapSolver
        
        # Por enquanto, retorna None
        return None
        
    def consultar_cpf(self, cpf):
        """Consulta um CPF"""
        cpf_formatted = self.formatar_cpf(cpf)
        print(f"\n🔍 Consultando CPF: {cpf_formatted}")
        
        try:
            # Passo 1: Acessar a página inicial para obter cookies
            url_inicial = f"{self.base_url}/meus-cupons"
            print("📡 Acessando página inicial...")
            
            resp1 = self.session.get(url_inicial, verify=False)
            print(f"   Status: {resp1.status_code}")
            print(f"   Cookies: {dict(self.session.cookies)}")
            
            # Extrair siteKey do Turnstile
            sitekey_match = re.search(r'"siteKey":"([^"]+)"', resp1.text)
            if sitekey_match:
                sitekey = sitekey_match.group(1)
                print(f"   SiteKey Turnstile: {sitekey}")
                
                # Tentar obter token
                token = self.obter_token_turnstile(sitekey)
                if not token:
                    print("❌ Não foi possível obter token do Turnstile")
                    return None
            
            # Passo 2: Tentar acessar diretamente a URL de visualização
            url_ver = f"{self.base_url}/meus-cupons/ver?cpf={cpf_formatted}"
            print(f"\n📡 Tentando acesso direto: {url_ver}")
            
            # Headers adicionais para a segunda requisição
            self.session.headers.update({
                "Referer": url_inicial,
                "Sec-Fetch-Site": "same-origin"
            })
            
            resp2 = self.session.get(url_ver, verify=False, allow_redirects=True)
            print(f"   Status: {resp2.status_code}")
            print(f"   URL final: {resp2.url}")
            
            # Analisar resposta
            if resp2.status_code == 200:
                return self.analisar_resposta(resp2.text, cpf_formatted)
            else:
                print(f"❌ Erro: Status {resp2.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Erro na consulta: {e}")
            return None
            
    def analisar_resposta(self, html, cpf):
        """Analisa o HTML da resposta"""
        resultado = {
            'cpf': cpf,
            'tem_cupons': None,
            'quantidade': 0,
            'mensagem': ''
        }
        
        # Remove tags HTML
        texto = re.sub(r'<[^>]+>', ' ', html)
        texto = ' '.join(texto.split())
        
        # Procura por padrões
        # Padrão 1: "X cupons" ou "X títulos"
        match = re.search(r'(\d+)\s*(?:cupons?|títulos?)', texto, re.IGNORECASE)
        if match:
            resultado['quantidade'] = int(match.group(1))
            resultado['tem_cupons'] = resultado['quantidade'] > 0
            
        # Padrão 2: Mensagens negativas
        if re.search(r'não\s+possui|nenhum|zero|sem\s+cupons?|sem\s+títulos?', texto, re.IGNORECASE):
            resultado['tem_cupons'] = False
            resultado['quantidade'] = 0
            
        # Padrão 3: Verificar se voltou para o formulário
        if 'CPFContinuar' in texto or 'Acessar meus títulos' in texto:
            print("⚠️ Redirecionado para formulário - Turnstile ativo")
            resultado['mensagem'] = 'Requer verificação Turnstile'
            return resultado
            
        print(f"📊 Resultado: {resultado['quantidade']} cupons/títulos")
        return resultado
        
    def processar_lista(self, arquivo_entrada, arquivo_saida='resultados_api.txt'):
        """Processa uma lista de CPFs"""
        print(f"\n📋 Processando lista: {arquivo_entrada}")
        
        # Lê CPFs do arquivo
        try:
            with open(arquivo_entrada, 'r') as f:
                cpfs = [linha.strip() for linha in f if linha.strip()]
        except FileNotFoundError:
            print(f"❌ Arquivo {arquivo_entrada} não encontrado!")
            return
            
        print(f"   Total de CPFs: {len(cpfs)}")
        
        resultados = []
        cpfs_com_cupons = []
        
        for i, cpf in enumerate(cpfs, 1):
            print(f"\n[{i}/{len(cpfs)}] ", end='')
            
            resultado = self.consultar_cpf(cpf)
            
            if resultado:
                resultados.append(resultado)
                
                # Se tem cupons, adiciona à lista
                if resultado.get('tem_cupons') == True:
                    cpfs_com_cupons.append(cpf)
                    
            # Delay entre requisições
            if i < len(cpfs):
                time.sleep(2)
                
        # Salva resultados
        print(f"\n\n💾 Salvando resultados...")
        
        # Arquivo com todos os resultados
        with open(arquivo_saida, 'w') as f:
            f.write(f"Consulta MegaMania - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("="*60 + "\n\n")
            
            for r in resultados:
                f.write(f"CPF: {r['cpf']}\n")
                f.write(f"Tem cupons: {r['tem_cupons']}\n")
                f.write(f"Quantidade: {r['quantidade']}\n")
                if r.get('mensagem'):
                    f.write(f"Mensagem: {r['mensagem']}\n")
                f.write("-"*40 + "\n")
                
        # Arquivo apenas com CPFs que têm cupons
        if cpfs_com_cupons:
            arquivo_com_cupons = arquivo_saida.replace('.txt', '_com_cupons.txt')
            with open(arquivo_com_cupons, 'w') as f:
                for cpf in cpfs_com_cupons:
                    f.write(f"{cpf}\n")
            print(f"✅ CPFs com cupons salvos em: {arquivo_com_cupons}")
            
        print(f"✅ Resultados completos salvos em: {arquivo_saida}")
        
        # Estatísticas
        total_consultados = len(resultados)
        total_com_cupons = sum(1 for r in resultados if r.get('tem_cupons') == True)
        total_sem_cupons = sum(1 for r in resultados if r.get('tem_cupons') == False)
        total_turnstile = sum(1 for r in resultados if 'Turnstile' in r.get('mensagem', ''))
        
        print(f"\n📊 Estatísticas:")
        print(f"   Total consultados: {total_consultados}")
        print(f"   Com cupons: {total_com_cupons}")
        print(f"   Sem cupons: {total_sem_cupons}")
        print(f"   Bloqueados (Turnstile): {total_turnstile}")

# Teste
if __name__ == "__main__":
    print("🎰 MegaMania API - Consultor de Cupons")
    print("="*50)
    
    api = MegaManiaAPI()
    
    # Teste único
    resultado = api.consultar_cpf("92972373987")
    if resultado:
        print(f"\nResultado:")
        print(f"  CPF: {resultado['cpf']}")
        print(f"  Tem cupons: {resultado['tem_cupons']}")
        print(f"  Quantidade: {resultado['quantidade']}")
        if resultado.get('mensagem'):
            print(f"  Mensagem: {resultado['mensagem']}")
            
    # Para processar lista:
    # api.processar_lista('cpfs.txt', 'resultados.txt')
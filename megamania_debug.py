# megamania_debug.py
import requests
import re
import urllib3
from bs4 import BeautifulSoup
import json

urllib3.disable_warnings()

def analisar_resposta(cpf):
    """Analisa detalhadamente a resposta para um CPF"""
    
    # Formata CPF
    cpf_clean = re.sub(r'\D', '', cpf)
    cpf_formatted = f"{cpf_clean[:3]}.{cpf_clean[3:6]}.{cpf_clean[6:9]}-{cpf_clean[9:]}"
    
    print(f"\n🔍 Analisando CPF: {cpf_formatted}")
    print("="*60)
    
    # Session para manter cookies
    session = requests.Session()
    
    # Headers mais completos
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    }
    
    # Primeira requisição - página de consulta
    url = f"https://consulta.megamaniadasorte.com.br/meus-cupons?cpf={cpf_formatted}"
    
    print(f"\n📡 Requisição 1: GET {url}")
    response = session.get(url, headers=headers, verify=False)
    
    print(f"Status Code: {response.status_code}")
    print(f"URL Final: {response.url}")
    print(f"Cookies: {dict(session.cookies)}")
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Procura por dados do Remix (framework usado)
        remix_context = re.search(r'window\.__remixContext = ({.*?});', response.text, re.DOTALL)
        if remix_context:
            print("\n🔧 Contexto Remix encontrado:")
            try:
                context_data = json.loads(remix_context.group(1))
                print(json.dumps(context_data, indent=2, ensure_ascii=False)[:500] + "...")
            except:
                print("Erro ao parsear JSON do contexto")
                
        # Procura form action
        forms = soup.find_all('form')
        if forms:
            print("\n📝 Forms encontrados:")
            for i, form in enumerate(forms):
                print(f"\nForm {i+1}:")
                print(f"  Action: {form.get('action', 'N/A')}")
                print(f"  Method: {form.get('method', 'N/A')}")
                
                # Inputs do form
                inputs = form.find_all('input')
                for inp in inputs:
                    print(f"  Input: name='{inp.get('name')}' type='{inp.get('type')}' value='{inp.get('value', '')}'")
                    
        # Tenta a segunda URL (ver)
        url2 = f"https://consulta.megamaniadasorte.com.br/meus-cupons/ver?cpf={cpf_formatted}"
        print(f"\n📡 Requisição 2: GET {url2}")
        
        response2 = session.get(url2, headers=headers, verify=False, allow_redirects=True)
        print(f"Status Code: {response2.status_code}")
        print(f"URL Final: {response2.url}")
        
        if response2.status_code == 200:
            soup2 = BeautifulSoup(response2.text, 'html.parser')
            
            # Remove scripts e styles
            for script in soup2(["script", "style"]):
                script.extract()
                
            # Pega texto limpo
            text = soup2.get_text()
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            
            print("\n📄 Conteúdo da segunda página:")
            for line in lines[:30]:  # Primeiras 30 linhas
                print(f"   {line}")
                
        # Salva ambos HTMLs
        with open(f"debug1_{cpf_clean}.html", "w", encoding="utf-8") as f:
            f.write(response.text)
        with open(f"debug2_{cpf_clean}.html", "w", encoding="utf-8") as f:
            f.write(response2.text)
            
        print(f"\n💾 HTMLs salvos: debug1_{cpf_clean}.html e debug2_{cpf_clean}.html")

# Teste com alguns CPFs
if __name__ == "__main__":
    print("🧪 Debug MegaMania - Análise Detalhada v2\n")
    
    # CPFs para testar
    cpfs_teste = [
        "92972373987",    # Primeiro da sua lista
    ]
    
    for cpf in cpfs_teste:
        analisar_resposta(cpf)
        print("\n" + "="*60 + "\n")
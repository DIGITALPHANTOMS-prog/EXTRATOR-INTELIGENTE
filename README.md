# CPF Checker com reCAPTCHA Resolver

Sistema automatizado para verificação de CPFs com resolução de reCAPTCHA invisível usando 2Captcha e proxies rotativos BrightData.

## Funcionalidades

- ✅ Resolve reCAPTCHA invisível automaticamente via 2Captcha
- ✅ Usa proxy rotativo BrightData (1 IP único por CPF)
- ✅ Classifica CPFs como LIVE/DIE
- ✅ Múltiplas estratégias de clique e submit
- ✅ Logs detalhados e arquivos de saída organizados

## Instalação

```bash
# Instalar dependências
npm install

# O Playwright será instalado automaticamente com o Chromium
```

## Uso

```bash
# Executar com arquivo de lista
node vale_play_clickforce_recaptcha.js lista.txt

# Ou usar o comando npm
npm start
```

## Formato do arquivo de entrada

O arquivo `lista.txt` deve conter um CPF por linha:
```
12345678901
98765432109
11122233344
```

## Arquivos de saída

Os resultados são salvos na pasta `saida_vale_chk/`:
- `live.txt` - CPFs válidos (LIVE)
- `die.txt` - CPFs inválidos (DIE)
- `resultado.log` - Log detalhado de todas as operações

## Configurações

### 2Captcha
- API Key já configurada: `99c6cdfca126ca1ffa2b0d2e0991c694`
- Para trocar, edite a variável `CAPTCHA_API_KEY` no código

### Proxy BrightData
- Host: `brd.superproxy.io:33335`
- Usuário: `brd-customer-hl_499adb66-zone-datacenter_proxy2`
- Senha: `l8kr9wg6xk1m`

### Modo Headless
Por padrão roda com interface gráfica. Para rodar sem interface:
```javascript
// Linha 298 - mude para:
headless: true,
```

## Como funciona

1. **Carrega a página** com proxy único
2. **Detecta reCAPTCHA** invisível e extrai o sitekey
3. **Envia para 2Captcha** resolver
4. **Injeta o token** no DOM antes de continuar
5. **Preenche CPF** com máscara e eventos
6. **Clica em Continuar** usando múltiplas estratégias
7. **Classifica resultado**:
   - LIVE: Campo senha aparece ou API retorna `isRegistered: true`
   - DIE: Mensagem "não cadastrado" ou timeout

## Troubleshooting

### reCAPTCHA não detectado
- O site pode não ter reCAPTCHA em todas as páginas
- Verifique se o sitekey está sendo extraído corretamente

### Erro de proxy
- Verifique credenciais do BrightData
- Confirme se tem saldo/créditos na conta

### 2Captcha timeout
- Verifique saldo na conta 2Captcha
- API Key pode estar inválida

## Melhorias implementadas

1. **Detecção automática de sitekey** - Procura em múltiplos lugares no DOM
2. **Injeção inteligente de token** - Injeta em todos os campos possíveis
3. **Callbacks automáticos** - Executa callbacks do reCAPTCHA se existirem
4. **Tratamento de erros** - Continua execução mesmo se captcha falhar
5. **Logs detalhados** - Mostra progresso da resolução do captcha
# Digital Phantoms WhatsApp Bot v2.0

Bot automatizado para envio de mensagens em grupos do WhatsApp usando Venom-bot.

## 🚀 Melhorias Implementadas

### 1. **Tratamento de Erros Robusto**
- Sistema de retry automático (até 2 tentativas por grupo)
- Verificação de conexão antes de enviar
- Timeout aumentado para 30 segundos
- Mensagens de erro detalhadas

### 2. **Interface Melhorada**
- Visual mais limpo com cores usando chalk
- Contador de tempo em tempo real durante delays
- Relatório detalhado ao final do processo
- Logs mais informativos durante o envio

### 3. **Gerenciamento de Sessão**
- Diretório específico para tokens (`./tokens`)
- Criação automática de diretórios necessários
- Melhor configuração do Puppeteer
- User-agent personalizado para evitar detecção

### 4. **Segurança e Confiabilidade**
- Backup automático dos arquivos de controle
- Validação de IDs de grupos
- Tratamento de caracteres especiais nos nomes
- Delay aleatório aumentado (12-20 segundos)

### 5. **Funcionalidades Extras**
- Possibilidade de retentar grupos com erro
- Estatísticas completas ao final
- Confirmação antes de iniciar o envio
- Detecção melhorada de grupos

## 📋 Pré-requisitos

```bash
# Node.js 14 ou superior
node --version

# NPM ou Yarn
npm --version
```

## 🔧 Instalação

```bash
# Instalar dependências
npm install

# ou
yarn install
```

## 🎯 Como Usar

1. **Prepare sua mensagem**
   - Crie um arquivo de texto (ex: `mensagem.txt`)
   - Escreva a mensagem que deseja enviar

2. **Execute o bot**
   ```bash
   npm start
   # ou
   node whatsapp-bot.js
   ```

3. **Escaneie o QR Code**
   - Uma janela do Chrome será aberta
   - Escaneie o QR code com seu WhatsApp

4. **Siga as instruções**
   - O bot listará todos os grupos encontrados
   - Informe o caminho do arquivo de mensagem
   - Confirme o envio

## 📊 Arquivos de Controle

- **`enviados.txt`**: Lista de grupos que receberam a mensagem
- **`erros.txt`**: Lista de grupos onde ocorreram erros
- **`*.backup`**: Backups automáticos dos arquivos

## ⚙️ Configurações

Você pode ajustar as seguintes constantes no código:

```javascript
const DELAY_MIN = 12000;     // Delay mínimo entre mensagens (ms)
const DELAY_MAX = 20000;     // Delay máximo entre mensagens (ms)
const SEND_TIMEOUT = 30000;  // Timeout para envio (ms)
const MAX_RETRIES = 2;       // Número de tentativas por grupo
```

## 🛠️ Solução de Problemas

### Erro de Timeout
- Aumente o valor de `SEND_TIMEOUT`
- Verifique sua conexão com a internet
- Certifique-se de que o WhatsApp Web está conectado

### Grupos não encontrados
- Aguarde alguns segundos após escanear o QR code
- Verifique se você participa de grupos
- Tente reiniciar o bot

### Mensagens não enviadas
- Verifique se o formato da mensagem está correto
- Evite mensagens muito longas
- Aguarde mais tempo entre os envios

## 🔒 Segurança

- **NUNCA** compartilhe a pasta `tokens/`
- Use delays adequados para evitar bloqueios
- Teste primeiro em poucos grupos
- Respeite os Termos de Uso do WhatsApp

## 📝 Scripts Disponíveis

```bash
# Iniciar o bot
npm start

# Modo desenvolvimento (com auto-restart)
npm run dev

# Limpar arquivos temporários
npm run clean
```

## ⚠️ Avisos Importantes

1. Este bot é para uso educacional
2. Use com responsabilidade
3. O WhatsApp pode bloquear contas que fazem spam
4. Sempre teste em pequena escala primeiro
5. Mantenha delays adequados entre mensagens

## 🐛 Debug

Se encontrar problemas:

1. Delete a pasta `tokens/` e tente novamente
2. Verifique os logs de erro no console
3. Confirme que o WhatsApp Web funciona normalmente
4. Teste com um único grupo primeiro

## 📄 Licença

MIT License - use por sua conta e risco.
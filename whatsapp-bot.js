const venom = require('venom-bot');
const fs = require('fs');
const readline = require('readline');
const chalk = require('chalk');
const path = require('path');

// Configurações
const ENVIADOS_FILE = 'enviados.txt';
const ERROS_FILE = 'erros.txt';
const DELAY_MIN = 12000; // Aumentado para evitar bloqueios
const DELAY_MAX = 20000; // Aumentado para parecer mais natural
const SEND_TIMEOUT = 30000; // Aumentado timeout
const MAX_RETRIES = 2; // Número de tentativas por grupo
const SESSION_DIR = './tokens';

const rl = readline.createInterface({ 
  input: process.stdin, 
  output: process.stdout 
});

// Função para garantir que o diretório existe
function ensureDirectoryExists(dirPath) {
  if (!fs.existsSync(dirPath)) {
    fs.mkdirSync(dirPath, { recursive: true });
  }
}

// Função de delay com feedback visual
function delay(ms) {
  const seconds = Math.round(ms / 1000);
  return new Promise(resolve => {
    let remaining = seconds;
    const interval = setInterval(() => {
      process.stdout.write(`⏳ Aguardando ${remaining}s...  \r`);
      remaining--;
      if (remaining < 0) {
        clearInterval(interval);
        process.stdout.write('                        \r');
        resolve();
      }
    }, 1000);
  });
}

// Delay aleatório
function randDelay() {
  return DELAY_MIN + Math.floor(Math.random() * (DELAY_MAX - DELAY_MIN));
}

// Salvar arquivo com backup
function saveToFile(file, lines) {
  try {
    // Fazer backup se o arquivo existir
    if (fs.existsSync(file)) {
      fs.copyFileSync(file, `${file}.backup`);
    }
    fs.writeFileSync(file, lines.join('\n'), { encoding: 'utf-8' });
  } catch (err) {
    console.error(chalk.red(`Erro ao salvar arquivo ${file}: ${err.message}`));
  }
}

// Função para enviar mensagem com timeout e retry
async function sendWithRetry(client, groupId, msg, maxRetries = MAX_RETRIES) {
  let lastError;
  
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      console.log(chalk.gray(`  Tentativa ${attempt}/${maxRetries}...`));
      
      // Verifica se o WhatsApp está conectado antes de enviar
      const isConnected = await client.isConnected();
      if (!isConnected) {
        throw new Error('WhatsApp não está conectado');
      }
      
      // Envia mensagem com timeout
      const result = await Promise.race([
        client.sendText(groupId, msg),
        new Promise((_, reject) =>
          setTimeout(() => reject(new Error('Timeout: mensagem demorou muito para enviar')), SEND_TIMEOUT)
        )
      ]);
      
      // Se chegou aqui, mensagem foi enviada com sucesso
      return result;
      
    } catch (err) {
      lastError = err;
      console.log(chalk.yellow(`  ⚠️  Tentativa ${attempt} falhou: ${err.message}`));
      
      if (attempt < maxRetries) {
        // Aguarda um pouco antes da próxima tentativa
        await delay(5000);
      }
    }
  }
  
  // Se todas as tentativas falharam, lança o último erro
  throw lastError;
}

// Função para obter informações do grupo de forma segura
function getGroupInfo(group) {
  let nome = 'Sem Nome';
  let id = '';
  
  try {
    // Tenta diferentes formas de obter o nome
    if (group.contact && group.contact.name) {
      nome = group.contact.name;
    } else if (group.name) {
      nome = group.name;
    } else if (group.formattedName) {
      nome = group.formattedName;
    }
    
    // Tenta diferentes formas de obter o ID
    if (group.id && group.id._serialized) {
      id = group.id._serialized;
    } else if (group.id && typeof group.id === 'string') {
      id = group.id;
    } else if (group._serialized) {
      id = group._serialized;
    }
    
    // Remove caracteres problemáticos do nome
    nome = nome.replace(/[\t\n\r]/g, ' ').trim();
    
  } catch (err) {
    console.error(chalk.red('Erro ao obter informações do grupo:'), err);
  }
  
  return { nome, id };
}

// Função principal
async function main() {
  console.log(chalk.cyan('\n═══════════════════════════════════════════'));
  console.log(chalk.cyan.bold('    Digital Phantoms WhatsApp Bot v2.0'));
  console.log(chalk.cyan('═══════════════════════════════════════════\n'));
  
  // Garantir que o diretório de sessão existe
  ensureDirectoryExists(SESSION_DIR);
  
  try {
    const client = await venom.create({
      session: 'DigitalPhantoms',
      headless: false,
      multidevice: true,
      folderNameToken: SESSION_DIR,
      mkdirFolderToken: SESSION_DIR,
      puppeteerOptions: {
        userDataDir: SESSION_DIR,
        args: [
          '--no-sandbox',
          '--disable-setuid-sandbox',
          '--disable-dev-shm-usage',
          '--disable-accelerated-2d-canvas',
          '--no-first-run',
          '--disable-gpu',
          '--disable-blink-features=AutomationControlled',
          '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        ],
        protocolTimeout: 900000
      },
      disableWelcome: true,
      updatesLog: false,
      autoClose: 60000,
      createPathFileToken: true,
      waitForLogin: true
    });
    
    console.log(chalk.green('✅ Bot iniciado com sucesso!\n'));
    
    // Aguarda um pouco para garantir que tudo está carregado
    await delay(3000);
    
    // Obtém todos os chats
    console.log(chalk.yellow('📋 Carregando lista de grupos...'));
    const chats = await client.getAllChats();
    
    // Filtra apenas grupos
    const groups = chats.filter(chat => {
      try {
        // Verifica se é um grupo de várias formas
        return (chat.id && chat.id.server === 'g.us') ||
               (chat.id && chat.id._serialized && chat.id._serialized.includes('@g.us')) ||
               (chat.isGroup === true);
      } catch {
        return false;
      }
    });
    
    if (!groups.length) {
      console.log(chalk.red('\n❌ Nenhum grupo encontrado.'));
      console.log(chalk.yellow('Verifique se o WhatsApp está conectado e tente novamente.'));
      await client.close();
      process.exit(1);
    }
    
    console.log(chalk.green(`\n✅ ${groups.length} grupos encontrados:\n`));
    
    // Lista grupos com informações detalhadas
    groups.forEach((group, index) => {
      const { nome, id } = getGroupInfo(group);
      console.log(chalk.white(`[${index + 1}] ${nome}`));
      console.log(chalk.gray(`    ID: ${id}`));
    });
    
    // Solicita arquivo de mensagem
    const filePath = await new Promise(resolve => {
      rl.question(chalk.cyan('\n📄 Digite o caminho do arquivo de mensagem (ex: mensagem.txt): '), resolve);
    });
    
    // Lê mensagem do arquivo
    let mensagem;
    try {
      mensagem = fs.readFileSync(filePath.trim(), 'utf-8').trim();
      if (!mensagem) {
        throw new Error('Arquivo vazio');
      }
      console.log(chalk.green('\n✅ Mensagem carregada com sucesso!'));
      console.log(chalk.gray(`Tamanho: ${mensagem.length} caracteres\n`));
    } catch (err) {
      console.error(chalk.red('\n❌ Erro ao ler arquivo:'), err.message);
      await client.close();
      process.exit(1);
    }
    
    // Carrega histórico
    let enviados = fs.existsSync(ENVIADOS_FILE) 
      ? fs.readFileSync(ENVIADOS_FILE, 'utf-8').split('\n').filter(Boolean) 
      : [];
    let erros = fs.existsSync(ERROS_FILE) 
      ? fs.readFileSync(ERROS_FILE, 'utf-8').split('\n').filter(Boolean) 
      : [];
    
    // Cria sets para busca rápida
    const enviadosSet = new Set(enviados.map(linha => linha.split('\t')[1]));
    const errosSet = new Set(erros.map(linha => linha.split('\t')[1]));
    
    console.log(chalk.yellow(`\n📊 Status: ${enviados.length} já enviados, ${erros.length} com erro\n`));
    
    // Confirma envio
    const confirmar = await new Promise(resolve => {
      rl.question(chalk.yellow('Deseja iniciar o envio? (s/n): '), resolve);
    });
    
    if (confirmar.toLowerCase() !== 's') {
      console.log(chalk.yellow('\n⚠️  Operação cancelada pelo usuário.'));
      await client.close();
      process.exit(0);
    }
    
    console.log(chalk.green('\n🚀 Iniciando envio de mensagens...\n'));
    
    // Estatísticas
    let sucessos = 0;
    let falhas = 0;
    let pulados = 0;
    
    // Processa cada grupo
    for (let idx = 0; idx < groups.length; idx++) {
      const group = groups[idx];
      const { nome, id: groupId } = getGroupInfo(group);
      
      if (!groupId) {
        console.log(chalk.red(`❌ [${idx + 1}/${groups.length}] Grupo sem ID válido, pulando...`));
        pulados++;
        continue;
      }
      
      const registro = `${nome}\t${groupId}`;
      const grupoStatus = `[${idx + 1}/${groups.length}] ${nome}`;
      
      // Verifica se já foi enviado
      if (enviadosSet.has(groupId)) {
        console.log(chalk.blue(`⏭️  ${grupoStatus}: já enviado anteriormente`));
        pulados++;
        continue;
      }
      
      // Verifica se está na lista de erros
      if (errosSet.has(groupId)) {
        console.log(chalk.yellow(`⚠️  ${grupoStatus}: marcado com erro anterior, tentando novamente...`));
        // Remove da lista de erros para tentar novamente
        erros = erros.filter(linha => !linha.includes(groupId));
        errosSet.delete(groupId);
      }
      
      console.log(chalk.cyan(`\n➡️  ${grupoStatus}`));
      
      try {
        // Envia mensagem com retry
        await sendWithRetry(client, groupId, mensagem);
        
        console.log(chalk.green(`✅ ${grupoStatus}: Mensagem enviada com sucesso!`));
        sucessos++;
        
        // Adiciona aos enviados
        enviados.push(registro);
        enviadosSet.add(groupId);
        saveToFile(ENVIADOS_FILE, enviados);
        
        // Aguarda antes do próximo envio
        if (idx < groups.length - 1) {
          const waitTime = randDelay();
          await delay(waitTime);
        }
        
      } catch (err) {
        console.log(chalk.red(`❌ ${grupoStatus}: ERRO ao enviar`));
        console.log(chalk.red(`   Detalhes: ${err.message || err}`));
        falhas++;
        
        // Adiciona aos erros
        erros.push(registro);
        errosSet.add(groupId);
        saveToFile(ERROS_FILE, erros);
        
        // Pequena pausa antes de continuar
        await delay(3000);
      }
    }
    
    // Relatório final
    console.log(chalk.cyan('\n═══════════════════════════════════════════'));
    console.log(chalk.cyan.bold('           RELATÓRIO FINAL'));
    console.log(chalk.cyan('═══════════════════════════════════════════'));
    console.log(chalk.green(`✅ Enviados com sucesso: ${sucessos}`));
    console.log(chalk.red(`❌ Falhas no envio: ${falhas}`));
    console.log(chalk.blue(`⏭️  Pulados: ${pulados}`));
    console.log(chalk.white(`📊 Total de grupos: ${groups.length}`));
    console.log(chalk.cyan('═══════════════════════════════════════════\n'));
    
    console.log(chalk.yellow('📁 Arquivos de relatório:'));
    console.log(chalk.gray(`   - ${ENVIADOS_FILE} (grupos que receberam a mensagem)`));
    console.log(chalk.gray(`   - ${ERROS_FILE} (grupos com erro no envio)`));
    
    // Fecha conexão
    await client.close();
    rl.close();
    
    console.log(chalk.green('\n✅ Processo finalizado com sucesso!'));
    process.exit(0);
    
  } catch (err) {
    console.error(chalk.red('\n❌ Erro fatal:'), err);
    rl.close();
    process.exit(1);
  }
}

// Inicia o bot
main().catch(err => {
  console.error(chalk.red('Erro ao iniciar bot:'), err);
  process.exit(1);
});
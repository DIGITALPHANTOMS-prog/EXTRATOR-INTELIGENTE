// megamania_playwright.js
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

// Configurações
const URL = 'https://consulta.megamaniadasorte.com.br/meus-cupons';
const MAX_CONCURRENT = 3;
const DELAY_BETWEEN_CHECKS = 2000;

// Formata CPF
function formatCPF(cpf) {
    const clean = cpf.replace(/\D/g, '');
    if (clean.length !== 11) return null;
    return `${clean.slice(0,3)}.${clean.slice(3,6)}.${clean.slice(6,9)}-${clean.slice(9)}`;
}

// Verifica um CPF
async function checkCPF(browser, cpf) {
    const cpfFormatted = formatCPF(cpf);
    if (!cpfFormatted) return { status: 'ERROR', msg: 'CPF inválido' };
    
    const context = await browser.newContext({
        userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        viewport: { width: 1280, height: 720 },
        locale: 'pt-BR',
        timezoneId: 'America/Sao_Paulo'
    });
    
    const page = await context.newPage();
    
    try {
        // Navega para a página
        await page.goto(`${URL}?cpf=${cpfFormatted}`, {
            waitUntil: 'networkidle',
            timeout: 30000
        });
        
        // Aguarda um pouco para garantir que a página carregou
        await page.waitForTimeout(3000);
        
        // Verifica se há Turnstile/Cloudflare
        const turnstile = await page.$('.cf-turnstile');
        if (turnstile) {
            console.log(`   ⏳ Aguardando Cloudflare Turnstile...`);
            
            // Aguarda o Turnstile ser resolvido (máximo 30 segundos)
            try {
                await page.waitForFunction(
                    () => {
                        const iframe = document.querySelector('.cf-turnstile iframe');
                        if (!iframe) return false;
                        const widget = iframe.contentWindow?.document?.querySelector('[data-state="passed"]');
                        return widget !== null;
                    },
                    { timeout: 30000 }
                );
                console.log(`   ✓ Turnstile resolvido!`);
                await page.waitForTimeout(2000);
            } catch (e) {
                console.log(`   ⚠️ Timeout esperando Turnstile`);
            }
        }
        
        // Pega o conteúdo da página
        const content = await page.content();
        const text = await page.textContent('body');
        
        // Verifica se está no formulário de CPF
        const hasForm = await page.$('form[action*="/meus-cupons/ver"]');
        const hasCPFInput = await page.$('input#cpf');
        
        if (hasForm || hasCPFInput) {
            // Se tem formulário, precisa preencher e enviar
            if (hasCPFInput) {
                console.log(`   📝 Preenchendo formulário...`);
                
                // Preenche o CPF
                await page.fill('input#cpf', cpfFormatted);
                await page.waitForTimeout(500);
                
                // Procura e clica no botão
                const button = await page.$('button[type="submit"]');
                if (button) {
                    await button.click();
                    
                    // Aguarda navegação ou mudança de conteúdo
                    await page.waitForTimeout(5000);
                    
                    // Pega novo conteúdo
                    const newText = await page.textContent('body');
                    
                    // Verifica se ainda está no formulário
                    if (newText.includes('Acessar meus títulos') || newText.includes('identifique-se')) {
                        return { status: 'DIE', msg: 'Sem cadastro' };
                    }
                    
                    // Verifica se tem cupons
                    if (newText.match(/\d+\s*(cupons?|títulos?)/i)) {
                        const match = newText.match(/(\d+)\s*(cupons?|títulos?)/i);
                        return { status: 'LIVE', msg: `${match[1]} cupons` };
                    }
                    
                    if (newText.includes('você possui') || newText.includes('seus títulos')) {
                        return { status: 'LIVE', msg: 'Tem cupons' };
                    }
                }
            }
            
            return { status: 'DIE', msg: 'Sem cadastro' };
        }
        
        // Se não tem formulário, verifica o conteúdo
        if (text.match(/\d+\s*(cupons?|títulos?)/i)) {
            const match = text.match(/(\d+)\s*(cupons?|títulos?)/i);
            return { status: 'LIVE', msg: `${match[1]} cupons` };
        }
        
        if (text.includes('você possui') || text.includes('seus títulos') || text.includes('número da sorte')) {
            return { status: 'LIVE', msg: 'Tem cupons' };
        }
        
        if (text.includes('não possui') || text.includes('nenhum título')) {
            return { status: 'DIE', msg: 'Sem cupons' };
        }
        
        // Salva HTML para debug se não conseguiu determinar
        fs.writeFileSync(`debug_${cpf}.html`, content);
        return { status: 'UNKNOWN', msg: 'Não foi possível determinar' };
        
    } catch (error) {
        return { status: 'ERROR', msg: error.message.slice(0, 50) };
    } finally {
        await context.close();
    }
}

// Processa lista de CPFs
async function processList(cpfList) {
    console.log(`\n🎯 MegaMania Checker v6.0 (Playwright)`);
    console.log(`📍 Site: ${URL}`);
    console.log(`\n📋 ${cpfList.length} CPFs carregados`);
    
    const browser = await chromium.launch({
        headless: false, // Deixe false para ver o que está acontecendo
        args: [
            '--disable-blink-features=AutomationControlled',
            '--disable-features=IsolateOrigins,site-per-process'
        ]
    });
    
    // Teste com primeiro CPF
    console.log(`\n🧪 Testando com primeiro CPF...`);
    const testResult = await checkCPF(browser, cpfList[0]);
    console.log(`   CPF: ${formatCPF(cpfList[0])}`);
    console.log(`   Status: ${testResult.status}`);
    console.log(`   Info: ${testResult.msg}`);
    
    console.log(`\n▶️  Pressione ENTER para continuar com todos...`);
    await new Promise(resolve => process.stdin.once('data', resolve));
    
    // Processa todos
    console.log(`\n🚀 Processando ${cpfList.length} CPFs...\n`);
    
    const results = { live: [], die: [], error: [] };
    const liveFile = fs.createWriteStream('live.txt');
    
    // Processa em lotes
    for (let i = 0; i < cpfList.length; i += MAX_CONCURRENT) {
        const batch = cpfList.slice(i, i + MAX_CONCURRENT);
        const promises = batch.map(cpf => checkCPF(browser, cpf));
        const batchResults = await Promise.all(promises);
        
        // Processa resultados
        batch.forEach((cpf, index) => {
            const result = batchResults[index];
            const cpfFormatted = formatCPF(cpf);
            const num = i + index + 1;
            
            if (result.status === 'LIVE') {
                results.live.push(cpf);
                liveFile.write(`${cpf}\n`);
                console.log(`[${num}/${cpfList.length}] ✅ LIVE - ${cpfFormatted} (${result.msg})`);
            } else if (result.status === 'DIE') {
                results.die.push(cpf);
                console.log(`[${num}/${cpfList.length}] ❌ DIE - ${cpfFormatted} (${result.msg})`);
            } else {
                results.error.push(cpf);
                console.log(`[${num}/${cpfList.length}] ⚠️ ${result.status} - ${cpfFormatted} (${result.msg})`);
            }
        });
        
        // Delay entre lotes
        if (i + MAX_CONCURRENT < cpfList.length) {
            await new Promise(resolve => setTimeout(resolve, DELAY_BETWEEN_CHECKS));
        }
    }
    
    liveFile.end();
    await browser.close();
    
    // Resumo final
    console.log(`\n${'='.repeat(50)}`);
    console.log(`📊 RESUMO FINAL:`);
    console.log(`   Total verificados: ${cpfList.length}`);
    console.log(`   ✅ LIVE: ${results.live.length}`);
    console.log(`   ❌ DIE: ${results.die.length}`);
    console.log(`   ⚠️ ERRO: ${results.error.length}`);
    console.log(`   📁 Lives salvos em: live.txt`);
    console.log(`${'='.repeat(50)}`);
}

// Main
async function main() {
    // Lê lista de CPFs
    if (!fs.existsSync('lista.txt')) {
        console.log('❌ Arquivo lista.txt não encontrado!');
        return;
    }
    
    const cpfList = fs.readFileSync('lista.txt', 'utf8')
        .split('\n')
        .map(line => line.trim())
        .filter(line => line.length > 0);
    
    // Remove duplicados
    const uniqueCpfs = [...new Set(cpfList)];
    
    await processList(uniqueCpfs);
}

// Executa
main().catch(console.error);
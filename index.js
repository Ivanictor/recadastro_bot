import makeWASocket, {
    useMultiFileAuthState,
    fetchLatestWaWebVersion,
    DisconnectReason,
    delay
} from '@whiskeysockets/baileys';

import express from 'express';
import P from 'pino';
import fs from 'fs';
import 'dotenv/config';

const logger = P({ level: 'silent' });
const AUTH_DIR = './auth_info';

const app = express();
app.use(express.json());

const API_KEY = process.env.API_KEY;

if (!API_KEY) {
    console.error('\nERRO FATAL: Variável de ambiente API_KEY não definida no .env');
    process.exit(1);
}

let sock = null;
let isConnected = false;
let isConnecting = false;
let pairingRequested = false;
let lastPairingCode = null;
let pairingCodeTimer = null;

// Middleware de autenticação por API key
function requireApiKey(req, res, next) {
    const authHeader = req.headers['authorization'] || '';
    const [scheme, token] = authHeader.split(' ');

    if (scheme !== 'Bearer' || !token) {
        return res.status(401).json({
            error: 'Autenticação necessária. Envie o header Authorization: Bearer <API_KEY>.'
        });
    }

    if (token !== API_KEY) {
        return res.status(403).json({ error: 'API key inválida.' });
    }

    next();
}

/**
 * Conecta ao WhatsApp e gerencia o ciclo de vida dos eventos.
 * Remove ouvintes anteriores para evitar vazamento de memória.
 */
async function connectToWhatsApp(phoneNumberForPairing = null) {
    // Remove listeners de instâncias anteriores se houver
    if (sock?.ev) {
        sock.ev.removeAllListeners('creds.update');
        sock.ev.removeAllListeners('connection.update');
    }

    // Busca versão mais recente de forma segura
    let version;
    try {
        const waVersionInfo = await fetchLatestWaWebVersion();
        version = waVersionInfo.version;
    } catch (err) {
        console.warn('\n⚠️ Não foi possível buscar versão mais recente do WA Web, usando fallback padrão.');
    }

    const { state, saveCreds } = await useMultiFileAuthState(AUTH_DIR);

    sock = makeWASocket({
        version,
        browser: ['Ubuntu', 'Chrome', '120.0.0'],
        auth: state,
        logger
    });

    sock.ev.on('creds.update', saveCreds);

    sock.ev.on('connection.update', async (update) => {
        const { connection, lastDisconnect } = update;

        // Solicitação de código de pareamento
        if (
            connection === 'connecting' &&
            !sock.authState.creds.registered &&
            phoneNumberForPairing &&
            !pairingRequested
        ) {
            pairingRequested = true;
            await delay(1500);

            try {
                const code = await sock.requestPairingCode(phoneNumberForPairing);
                lastPairingCode = code;
                console.log('🔑 Código de pareamento gerado:', code);

                // Expira o código local após 2 minutos por segurança
                if (pairingCodeTimer) clearTimeout(pairingCodeTimer);
                pairingCodeTimer = setTimeout(() => {
                    lastPairingCode = null;
                }, 120000);

            } catch (err) {
                console.error('\n❌ Erro ao solicitar código de pareamento:', err);
                pairingRequested = false;
            }
        }

        if (connection === 'open') {
            isConnected = true;
            isConnecting = false;
            pairingRequested = false;
            lastPairingCode = null;
            console.log('\n✅ WhatsApp conectado com sucesso!');
        }

        if (connection === 'close') {
            isConnected = false;
            const statusCode = lastDisconnect?.error?.output?.statusCode;
            console.log(`🔌 Conexão encerrada. Código de status: ${statusCode}`);

            if (statusCode !== DisconnectReason.loggedOut) {
                console.log('🔄 Tentando reconectar...');
                try {
                    await connectToWhatsApp(phoneNumberForPairing);
                } catch (err) {
                    console.error('\n❌ Erro ao tentar reconectar:', err);
                    isConnecting = false;
                }
            } else {
                console.log('\n🔒 Sessão encerrada/desconectada pelo celular. É necessário autenticar novamente.');
                isConnecting = false;
                pairingRequested = false;
                lastPairingCode = null;
            }
        }
    });
}

/**
 * Ponto de entrada protegido contra chamadas concorrentes.
 */
async function start(phoneNumberForPairing = null) {
    if (isConnecting || isConnected) {
        console.log('\nℹ️ start() ignorado: Conexão já ativa ou em andamento.');
        return { started: false, reason: 'already-connecting-or-connected' };
    }

    isConnecting = true;

    try {
        await connectToWhatsApp(phoneNumberForPairing);
        return { started: true };
    } catch (err) {
        isConnecting = false;
        throw err;
    }
}

// Endpoint para solicitar pareamento por código
app.post('/request-pairing-code', requireApiKey, async (req, res) => {
    try {
        const { numero } = req.body;

        if (!numero || !/^\d{10,15}$/.test(numero)) {
            return res.status(400).json({
                error: 'Número é obrigatório e deve conter apenas dígitos com DDI+DDD (ex: 5562999999999).'
            });
        }

        const result = await start(numero);

        if (!result.started) {
            return res.status(409).json({
                error: 'Já existe uma sessão conectada ou uma tentativa de conexão em andamento.'
            });
        }

        return res.status(200).json({
            success: true,
            message: 'Solicitação enviada. Consulte GET /pairing-code em alguns segundos.'
        });

    } catch (error) {
        console.error('Erro ao iniciar processo de pareamento:', error);
        return res.status(500).json({ error: 'Erro ao iniciar processo de pareamento.' });
    }
});

// Endpoint para consultar o código gerado
app.get('/pairing-code', requireApiKey, (req, res) => {
    if (!lastPairingCode) {
        return res.status(404).json({ error: 'Código ainda não gerado ou expirado.' });
    }
    return res.status(200).json({ code: lastPairingCode });
});

// Endpoint para consultar status
app.get('/status', requireApiKey, (req, res) => {
    return res.status(200).json({ conectado: isConnected, conectando: isConnecting });
});

// Endpoint para envio de mensagem
app.post('/send-message', requireApiKey, async (req, res) => {
    try {
        const { numero, mensagem } = req.body;

        if (!numero || !mensagem) {
            console.log("\nMensagem não enviada: número e mensagem não foram enviados ao Baileys\n")
            return res.status(400).json({ error: 'Número e mensagem são obrigatórios.' });
        }

        if (!/^\d{10,15}$/.test(numero)) {
            console.log("\nMensagem não enviada: formato de número inválido\n")
            return res.status(400).json({ error: 'Formato de número inválido.' });
        }

        if (!isConnected || !sock) {
            return res.status(503).json({ error: 'WhatsApp ainda não está conectado.' });
        }

        const jid = `${numero}@s.whatsapp.net`;
        await sock.sendMessage(jid, { text: mensagem });

        console.log(`\n✉️ Mensagem enviada para ${numero}\n`);
        return res.status(200).json({ success: true, numero, mensagem });

    } catch (error) {
        console.error('\nErro ao enviar mensagem:', error);
        return res.status(502).json({ error: 'Falha ao enviar mensagem via WhatsApp.' });
    }
});

// Inicialização automática SOMENTE se já existir sessão salva prévia
const hasAuthCredentials = fs.existsSync(AUTH_DIR) && fs.readdirSync(AUTH_DIR).length > 0;

if (hasAuthCredentials) {
    console.log('\n📦 Credenciais encontradas. Tentando reconexão automática...');
    start().catch(err => console.error('Erro na reconexão automática:', err));
} else {
    console.log('\nℹ️ Nenhuma sessão salva encontrada. Aguardando chamada a /request-pairing-code para parear.');
}

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
    console.log(`\n🚀 Servidor Express do WhatsApp rodando na porta ${PORT}`);
});
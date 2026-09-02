import makeWASocket, {
    useMultiFileAuthState,
    fetchLatestWaWebVersion,
    DisconnectReason,
    delay
} from '@whiskeysockets/baileys';

import express from 'express';
import P from 'pino';
import 'dotenv/config';

const logger = P({ level: 'silent' });

const { version } = await fetchLatestWaWebVersion();

const app = express();
app.use(express.json());

const API_KEY = process.env.API_KEY;

if (!API_KEY) {
    console.error('ERRO FATAL: variável de ambiente API_KEY não definida. Configure-a no .env antes de subir o servidor.');
    process.exit(1);
}

let sock;
let isConnected = false;
let isConnecting = false; 
let pairingRequested = false; 
let lastPairingCode = null;

// Middleware de autenticação por API key.
// Espera o header: Authorization: Bearer <API_KEY>
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
 * Faz o trabalho real de criar o socket e registrar os listeners.
 * NÃO tem proteção contra chamadas concorrentes — isso é responsabilidade
 * de quem chama (start(), na primeira vez, ou o próprio listener de
 * 'connection.update', nas reconexões automáticas).
 * @param {string} [phoneNumberForPairing]
 */
async function connectToWhatsApp(phoneNumberForPairing) {
    const { state, saveCreds } = await useMultiFileAuthState('./auth_info');

    sock = makeWASocket({
        version,
        browser: ['Ubuntu', 'Chrome', '120.0.0'],
        auth: state,
        logger
    });

    sock.ev.on('creds.update', saveCreds);

    sock.ev.on('connection.update', async (update) => {
        const { connection, lastDisconnect } = update;

        // Solicita o código de pareamento apenas quando:
        // - o socket entrou em "connecting"
        // - ainda não há sessão registrada
        // - um número foi informado
        // - ainda não pedimos código nesta tentativa
        if (
            connection === 'connecting' &&
            !sock.authState.creds.registered &&
            phoneNumberForPairing &&
            !pairingRequested
        ) {
            pairingRequested = true;
            await delay(1500); // pequeno atraso recomendado antes de solicitar o código

            try {
                const code = await sock.requestPairingCode(phoneNumberForPairing);
                lastPairingCode = code;
                console.log('Código de pareamento gerado:', code);
            } catch (err) {
                console.error('Erro ao solicitar código de pareamento:', err);
                pairingRequested = false; 
            }
        }

        if (connection === 'open') {
            isConnected = true;
            isConnecting = false;
            pairingRequested = false;
            lastPairingCode = null;
            console.log('WhatsApp conectado!');
        }

        if (connection === 'close') {
            isConnected = false;
            const statusCode = lastDisconnect?.error?.output?.statusCode;

            console.log('Conexão encerrada. Código:', statusCode);

            if (statusCode !== DisconnectReason.loggedOut) {
                console.log('Tentando reconectar...');
                // Reconexão automática: chama a conexão diretamente (sem passar
                // pelo guard de start()), pois é continuação do mesmo ciclo de
                // vida e isConnecting já está true.
                try {
                    await connectToWhatsApp(phoneNumberForPairing);
                } catch (err) {
                    console.error('Erro ao tentar reconectar:', err);
                    isConnecting = false;
                }
            } else {
                console.log('Sessão encerrada. É necessário autenticar novamente.');
                isConnecting = false;
                pairingRequested = false;
                lastPairingCode = null;
            }
        }
    });
}

/**
 * Ponto de entrada público para iniciar a conexão com o WhatsApp.
 * Protegido contra chamadas concorrentes: se já existir uma conexão
 * ativa ou uma tentativa em andamento, não cria um novo socket
 * (evita instâncias duplicadas de `sock` e listeners órfãos).
 * @param {string} [phoneNumberForPairing] - Número no formato DDI+DDD+número, sem +()- (ex: "5562999999999")
 * @returns {Promise<{started: boolean, reason?: string}>}
 */
async function start(phoneNumberForPairing) {
    if (isConnecting || isConnected) {
        console.log('start() ignorado: já existe uma conexão ativa ou em andamento.');
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

// Endpoint para iniciar a autenticação via código de pareamento
app.post('/request-pairing-code', requireApiKey, async (req, res) => {
    try {
        const { numero } = req.body;

        if (!numero) {
            return res.status(400).json({
                error: 'Número é obrigatório (formato: DDI+DDD+número, sem +, (), ou -).'
            });
        }

        // Validação simples: apenas dígitos, entre 10 e 15 caracteres
        if (!/^\d{10,15}$/.test(numero)) {
            return res.status(400).json({
                error: 'Formato de número inválido. Use apenas dígitos, com DDI e DDD (ex: 5562999999999).'
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
        return res.status(404).json({ error: 'Código ainda não gerado ou já expirado.' });
    }
    return res.status(200).json({ code: lastPairingCode });
});

// Endpoint para verificar status da conexão
app.get('/status', requireApiKey, (req, res) => {
    return res.status(200).json({ conectado: isConnected, conectando: isConnecting });
});

// Endpoint para enviar mensagem (apenas contatos individuais)
app.post('/send-message', requireApiKey, async (req, res) => {
    try {
        const { numero, mensagem } = req.body;

        if (!numero || !mensagem) {
            return res.status(400).json({
                error: 'Número e mensagem são obrigatórios.'
            });
        }

        if (!/^\d{10,15}$/.test(numero)) {
            return res.status(400).json({
                error: 'Formato de número inválido. Use apenas dígitos, com DDI e DDD (ex: 5562999999999).'
            });
        }

        if (!isConnected) {
            return res.status(503).json({
                error: 'WhatsApp ainda não está conectado.'
            });
        }

        const jid = `${numero}@s.whatsapp.net`;

        try {
            await sock.sendMessage(jid, { text: mensagem });
        } catch (sendError) {
            console.error(`Erro ao enviar mensagem para ${numero}:`, sendError);
            return res.status(502).json({
                error: 'Falha ao enviar a mensagem via WhatsApp.',
                detalhe: sendError?.message
            });
        }

        console.log(`Mensagem enviada para ${numero}`);

        return res.status(200).json({
            success: true,
            numero,
            mensagem
        });

    } catch (error) {
        console.error('Erro inesperado ao enviar mensagem:', error);
        return res.status(500).json({ error: 'Erro inesperado ao enviar mensagem.' });
    }
});

// Se já existir auth_info salvo (./auth_info), reconecta automaticamente sem pedir código.
// Se ainda não houver sessão, isso não conecta sozinho — é necessário chamar
// POST /request-pairing-code (com o número) para gerar o código pela primeira vez.
start().catch(err => console.error('Erro ao iniciar servidor WhatsApp:', err));

// Inicia o servidor Express
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
    console.log(`Servidor Express rodando na porta ${PORT}`);
});
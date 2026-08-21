import makeWASocket, {
    useMultiFileAuthState,
    fetchLatestWaWebVersion,
    DisconnectReason
} from '@whiskeysockets/baileys';

import express from 'express';
import P from 'pino';
import 'dotenv/config';

const logger = P({ level: 'silent' });

const { version } = await fetchLatestWaWebVersion();

const app = express();

app.use(express.json());

let sock;

async function start() {
    const { state, saveCreds } = await useMultiFileAuthState('./auth_info');

    sock = makeWASocket({
        version,
        browser: ['Windows', 'Chrome', '145.0.0'],
        auth: state,
        logger
    });

    sock.ev.on('creds.update', saveCreds);

    sock.ev.on('connection.update', ({ connection, lastDisconnect }) => {
        if (connection === 'open') {
            console.log('WhatsApp conectado!');
        }

        if (connection === 'close') {
            const statusCode = lastDisconnect?.error?.output?.statusCode;

            console.log('Conexão encerrada. Código:', statusCode);

            if (statusCode !== DisconnectReason.loggedOut) {
                console.log('Tentando reconectar...')
                start()
            } else {
                console.log('Sessão encerrada. É necessário autenticar novamente.')
            }
        }
    });
}


// Endpoint para enviar mensagem
app.post('/send-message', async (req, res) => {
    try {
        const { numero, mensagem } = req.body;

        if (!numero || !mensagem) {
            return res.status(400).json({
                error: 'Número e mensagem são obrigatórios.'
            });
        }

        if (!sock) {
            return res.status(503).json({
                error: 'WhatsApp ainda não está conectado.'
            });
        }

        const jid = `${numero}@s.whatsapp.net`;

        await sock.sendMessage(jid, {
            text: mensagem
        });

        console.log(`Mensagem enviada para ${numero}`);

        return res.status(200).json({
            success: true,
            numero,
            mensagem
        });

    } catch (error) {
        console.error('Erro ao enviar mensagem:', error);

        return res.status(500).json({
            error: 'Erro ao enviar mensagem.'
        });
    }
});


// Inicia o Baileys
start();

// Inicia o servidor Express
app.listen(3000, () => {
    console.log('Servidor Express rodando na porta 3000');
});
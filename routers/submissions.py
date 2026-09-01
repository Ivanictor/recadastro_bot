from fastapi import APIRouter
import time
from models.webhook import Webhook
from utils.validate_data import formatar_cpf, validar_cpf, validar_foto, validar_unidade
from services.data_loader import query_banco
from services.request_whatsapp import enviar_whatsapp
from services.email_service import send_email_to_manager

router = APIRouter()

sessoes = {}
TEMPO_SESSAO = 30 * 60

@router.post("/webhook")
def webhook(dados: Webhook):

    print(dados)

    nome = (dados.queryResult.parameters.nome5 
            or dados.queryResult.parameters.nome7)
    
    cpf = (dados.queryResult.parameters.cpf5 
           or dados.queryResult.parameters.cpf7)

    unidade = (dados.queryResult.parameters.unidadelot
               or dados.queryResult.parameters.unidadelot2)

    foto13 = dados.queryResult.parameters.foto5

    fotorosto13 = dados.queryResult.parameters.fotorosto5

    fotodoc16 = dados.queryResult.parameters.fotodoc7

    fotorosto16 = dados.queryResult.parameters.fotorosto7
    
    session = dados.session
    sim = (dados.queryResult.parameters.Sim 
           or dados.queryResult.parameters.sim)

    if cpf is not None:
        cpf = formatar_cpf(cpf)
        if not validar_cpf(cpf):
            return {
                "fulfillmentText": "Verificamos que o CPF que você enviou é inválido. Digite '13' ou '16' para reiniciar a conversa"
            }

    if unidade is not None:
        if not validar_unidade(unidade):
            return {
                "fulfillmentText": "Verificamos que a unidade que você informou foi digitada incorretamente ou não está presente em nosso banco de dados. Digite '13' ou '16' para reiniciar a conversa"
            }

    print(f"Nome: {nome}, CPF: {cpf}")

    if nome and cpf:
        sessoes[session] = {
            "nome": nome,
            "cpf": cpf,
            "unidade": unidade,
            "expira_em": time.monotonic() + TEMPO_SESSAO,
            "foto13": foto13,
            "fotorosto13": fotorosto13,
            "fotodoc16": fotodoc16,
            "fotorosto16": fotorosto16
        }

    sessao = sessoes.get(session)

    if sessao is None:
        return {
                "fulfillmentText": "Não encontramos os dados da sessão. Digite 13 (Recadastramento normal) ou 16 (Recadastramento fora do aniversário) para iniciar novamente"
            }

    if time.monotonic() > sessao["expira_em"]:
        del sessoes[session]
        return {
                "fulfillmentText": "Sua sessão expirou. Digite 13 (Recadastramento normal) ou 16 (Recadastramento fora do aniversário) para iniciar novamente"
            }

    if sim == '' and validar_foto(
        sessao.get("foto13"), 
        sessao.get("fotorosto13"), 
        sessao.get("fotodoc16"), 
        sessao.get("fotorosto16")
        ):

        nome_query = sessao.get("nome")
        cpf_query = sessao.get("cpf")
        unidade_query = sessao.get("unidade")

        print(f"\nQuery: {nome_query}, {cpf_query}")

        gerente_nome, gerente_numero, gerente_email, mensagem = query_banco(unidade_query, nome_query)

        if gerente_numero:
            sucesso = enviar_whatsapp(gerente_numero, mensagem)
            
        sucesso_email = send_email_to_manager(nome_query, gerente_email, mensagem)

        if sucesso or sucesso_email:
            return {
                "fulfillmentText": f"Dados enviados ao gerente responsável: {gerente_nome}"
            }
        else:
            print("Falha ao enviar ao gerente")
            return {
                "fulfillmentText": "Solicitação recebida, favor entrar em contato com o gerente para solicitar sua aprovação"
            }

        
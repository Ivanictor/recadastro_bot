from fastapi import APIRouter
from models.webhook import Webhook
from utils.cpf import format_cpf, validate_cpf, query_banco, validate_photo
import time

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

    foto13 = dados.queryResult.parameters.foto5

    fotorosto13 = dados.queryResult.parameters.fotorosto5

    fotodoc16 = dados.queryResult.parameters.fotodoc7

    fotorosto16 = dados.queryResult.parameters.fotorosto7
    
    session = dados.session
    sim = (dados.queryResult.parameters.Sim 
           or dados.queryResult.parameters.sim)

    if cpf is not None:
        cpf = format_cpf(cpf)
        if not validate_cpf(cpf):
            return {
                "fulfillmentText": "Verificamos que o CPF que você enviou é inválido. Digite '13' ou '16' para reiniciar a conversa"
            }

    print(f"Nome: {nome}, CPF: {cpf}")

    if nome and cpf:
        sessoes[session] = {
            "nome": nome,
            "cpf": cpf,
            "expira_em": time.monotonic() + TEMPO_SESSAO,
            "foto13": foto13,
            "fotorosto13": fotorosto13,
            "fotodoc16": fotodoc16,
            "fotorosto16": fotorosto16
        }

    sessao = sessoes.get(session)

    if time.monotonic() > sessao["expira_em"]:
        del sessoes[session]

    if sessao is None:
        return {
                "fulfillmentText": "Não encontramos os dados da sessão. Digite 13 (Recadastramento normal) ou 16 (Recadastramento fora do aniversário) para iniciar novamente"
            }

    if sim == '' and validate_photo(
        sessao.get("foto13"), 
        sessao.get("fotorosto13"), 
        sessao.get("fotodoc16"), 
        sessao.get("fotorosto16")
        ):

        nome_query = sessao.get("nome")
        cpf_query = sessao.get("cpf")

        query_banco(nome_query, cpf_query)
        print(f"\nSucesso! Query: {nome_query}, {cpf_query}")
        return {
            "fulfillmentText": "Dados enviados ao gerente responsável"
        }

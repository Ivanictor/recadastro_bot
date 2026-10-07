from fastapi import APIRouter, Depends, HTTPException
import time
import secrets
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from models.webhook import Webhook
from config import settings
from utils.validate_data import formatar_cpf, validar_cpf, validar_foto
from services.data_loader import query_banco
from services.request_whatsapp import enviar_whatsapp, enviar_whatsapp_rh
from services.email_service import send_email_to_manager

router = APIRouter()

security = HTTPBasic()

sessoes = {}
TEMPO_SESSAO = 30 * 60

@router.post("/webhook")
def webhook(dados: Webhook, creds: HTTPBasicCredentials = Depends(security)):

    if not (secrets.compare_digest(creds.username, settings.basic_user) and
            secrets.compare_digest(creds.password, settings.basic_password.get_secret_value())):
        raise HTTPException(status_code=401, headers={"WWW-Authenticate": "Basic"})

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

    sim_maiusculo = dados.queryResult.parameters.Sim
    sim_minusculo = dados.queryResult.parameters.sim

    if sim_maiusculo is not None:
        sim = sim_maiusculo
    else:
        sim = sim_minusculo

    if cpf is not None:
        cpf = formatar_cpf(cpf)
        if not validar_cpf(cpf):
            return {
                "fulfillmentText": "Verificamos que o CPF que você enviou é inválido. Digite '13' ou '16' para reiniciar a conversa"
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

        print(f"\nQuery: {nome_query}, {cpf_query}, {unidade_query}")

        gerente_nome, gerente_numero, gerente_email, mensagem = query_banco(unidade_query, nome_query)

        sucesso_email = False
        
        if gerente_email:
            sucesso_email = send_email_to_manager(nome_query, gerente_email, mensagem)

        sucesso = False

        if gerente_numero:
            sucesso = enviar_whatsapp(gerente_numero, mensagem)

        if sucesso or sucesso_email:

            if gerente_nome and gerente_nome != "Nenhum":

                mensagem_rh = f"O funcionário {nome_query} solicitou recadastramento e o gerente/coordenador {gerente_nome}, da {unidade_query} foi corretamente notificado"

                print("\nSucesso! Dados enviados ao gerente responsável\n")

                enviar_whatsapp_rh(mensagem_rh)

                return {
                    "fulfillmentText": f"Dados enviados ao gerente responsável: {gerente_nome}.\n\n Para receber o protocolo desta operação, digite 10."
                }
            
            elif gerente_nome == "Nenhum":

                mensagem_rh = f"O funcionário {nome_query} solicitou recadastramento, porém sua unidade ({unidade_query}) está sem gerente/coordenador"

                print("\n Dados enviados ao Luan para processamento manual")

                enviar_whatsapp_rh(mensagem_rh)

                return {
                    "fulfillmentText": f"No banco de dados, consta que a sua unidade não possui gerente responsável no momento, logo seus dados serão processados manualmente. \n\n Para receber o protocolo desta operação, digite 10."
                }

            elif not gerente_nome:

                mensagem_rh = f"O funcionário {nome_query} solicitou recadastramento, porém sua unidade informada ({unidade_query}) não foi encontrada no banco de dados"

                print("\n Dados enviados ao Luan para processamento manual")

                enviar_whatsapp_rh(mensagem_rh)

                return {
                    "fulfillmentText": f"A unidade informada foi digitada incorretamente ou não está presente em nosso banco de dados. Seus dados serão processados manualmente.\n Para receber o protocolo desta operação, digite 10."
                }
                
        else:

            mensagem_rh = f"O funcionário {nome_query}, da {unidade_query}, solicitou recadastramento, porém houve falha na notificação do gestor responsável"

            print("Falha ao enviar ao gerente")

            enviar_whatsapp_rh(mensagem_rh)

            return {
                "fulfillmentText": "Solicitação recebida, favor entrar em contato com o gerente para solicitar sua aprovação. \n\n Para receber o protocolo desta operação, digite 10"
            }

    else:
        print("\nNão enviou:\n")

        if sim != '' and not nome:
            print("Sim não enviado\n")
            print(sim)

        if not validar_foto(
        sessao.get("foto13"), 
        sessao.get("fotorosto13"), 
        sessao.get("fotodoc16"), 
        sessao.get("fotorosto16")
        ) and not nome:
            print("Fotos não validadas\n")
        else:
            print("Ainda não chegou na última intent")
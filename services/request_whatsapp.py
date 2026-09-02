import requests
import time
from config import settings


API_KEY = settings.api_key.get_secret_value()
PHONE_NUMBER = settings.phone_number
WHATSAPP_WEB_URL = settings.whatsapp_service_url

def solicitar_codigo_pareamento():

    url = f"{WHATSAPP_WEB_URL}/request-pairing-code"

    json = {
        "numero": PHONE_NUMBER
        }
    
    headers = {
        "Authorization": f"Bearer {API_KEY}"
        }

    response = requests.post(url=url, json=json, headers=headers)

    return response

def consultar_codigo_pareamento():

    url = f"{WHATSAPP_WEB_URL}/pairing-code"

    headers = {
        "Authorization": f"Bearer {API_KEY}"
        }

    response = requests.get(url=url, headers=headers)

    return response

def iniciar_whatsapp():
    resposta = solicitar_codigo_pareamento()

    if resposta.status_code == 409:
        print("Já existe uma sessão conectada")
        return

    elif resposta.status_code == 200:
        print("Solicitação de pareamento enviada.")

        time.sleep(4)

        codigo = consultar_codigo_pareamento()

        if codigo.status_code == 200:
            code = codigo.json()["code"]

            print(f"Código de pareamento: {code}")
            return

        else:
            print("Erro: ", codigo.json())

    else:
        print("Erro: ", resposta.json())

def tratar_numero_wpp(numero: str):
    numero = numero.strip()
    numero = numero.replace("-", "")

    if len(numero) == 11:
        numero = "55" + numero

    else:
        numero = "5562" + numero

    return numero

def enviar_whatsapp(numero, mensagem):

    numero = tratar_numero_wpp(numero)
    
    try:

        headers = {
            "Authorization": f"Bearer {API_KEY}"
            }
    
        response = requests.post(f"{WHATSAPP_WEB_URL}/send-message", json={
            "numero": numero,
            "mensagem": mensagem
        },
        headers=headers)

        if response.status_code == 200:
            print("Mensagem enviada com sucesso ao WhatsApp")

            return True
        else:
            print("Erro:", response.status_code)
            return False

    except requests.exceptions.RequestException as e:
        print(f"Erro ao conectar com o servidor de WhatsApp: {e}")
        return False
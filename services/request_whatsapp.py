import requests

def enviar_whatsapp(numero, mensagem):
    try:
    
        response = requests.post("http://127.0.0.1:3000/send-message", json={
            "numero": numero,
            "mensagem": mensagem
        })

        if response.status_code == 200:
            print("Mensagem enviada com sucesso ao WhatsApp")

            return True
        else:
            print("Erro:", response.status_code)
            return False

    except requests.exceptions.RequestException as e:
        print(f"Erro ao conectar com o servidor de WhatsApp: {e}")
        return False
from dotenv import load_dotenv
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

load_dotenv()

def send_email_to_manager(nome_funcionario, destiny_email, mensagem):
    email_remetente = os.getenv("Email")
    senha = os.getenv("Senha_App")

    msg = MIMEMultipart()
    msg["From"] = email_remetente
    msg["To"] = destiny_email
    msg["Subject"] = f"Recadastramento do funcionário {nome_funcionario}"

    msg.attach(MIMEText(mensagem, "plain"))

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(email_remetente, senha)
            server.sendmail(email_remetente, destiny_email, msg.as_string())
        print("Email enviado")

        return True

    except Exception as e:
        print(f"Erro ao enviar email: {e}")
        return False


    
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import settings


def send_email_to_manager(nome_funcionario, destiny_email, mensagem):
    email_remetente = settings.email_gmail
    senha = settings.senha_app_gmail

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
        print("\nEmail enviado\n")

        return True

    except Exception as e:
        print(f"\nErro ao enviar email: {e}\n")
        return False


    
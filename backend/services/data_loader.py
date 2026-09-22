import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import unicodedata
from utils.text_similarity import compare_names
from config import settings


def normalizar(texto):
    if texto is None:
        return ""
    
    texto = texto.strip().lower()

    texto = unicodedata.normalize("NFD", texto)

    texto = "".join(
        c for c in texto
        if unicodedata.category(c) != "Mn"
    )

    return texto

def query_banco(unidade_query, nome_query):

    # Escopos de acesso
    SCOPES = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]

    # Caminho do JSON baixado
    credentials = Credentials.from_service_account_file(
        settings.google_credentials.get_secret_value(),
        scopes=SCOPES
    )
    
    #Abrir planilha
    client = gspread.authorize(credentials)
    sheet = client.open("Cadastro de Unidades da SEAD - atualizado (2)").worksheet("Unidades Completo")
    data = sheet.get_all_values()
    headers = data[3]
    rows = data[4:]
    df = pd.DataFrame(rows, columns=headers)

    df["SIGLA"] = df["SIGLA"].fillna("").map(normalizar)
    df["UNIDADE"] = df["UNIDADE"].fillna("").map(normalizar)
    df["CELULAR"] = df["CELULAR"].astype(str)

    unidade_query = normalizar(unidade_query)

    df["similaridade"] = df["UNIDADE"].apply(
        lambda x: compare_names(unidade_query, x)
        )
    
    indice = df["similaridade"].idxmax()

    resultado = df.loc[indice]

    if resultado["similaridade"] < 0.85:
        print("Unidade não encontrada")

        mensagem = (
            f"""
            Alerta Recadastro: o(a) servidor(a) {nome_query} informou ser integrante da gerência {unidade_query},
            na solicitação de recadastramento. No entanto, essa unidade não consta no banco de dados informado.
            Sigam com os procedimentos necessários para o recadastramento do servidor. """
            )


        return None, None, "luan.asilva@goias.gov.br", mensagem

    gerente_nome = resultado["NOME"]
    gerente_numero = resultado["CELULAR"]
    gerente_email = resultado["EMAIL"]

    if pd.isna(gerente_email) or not str(gerente_email).strip():
        print("Unidade sem gerente")

        mensagem = (
            f"""
            Alerta Recadastro: o(a) servidor(a) {nome_query} informou ser integrante da unidade "{unidade_query}",
            na solicitação de recadastramento. No entanto, essa unidade não possui gerente responável 
            no banco de dados informado. Sigam com os procedimentos necessários para o recadastramento 
            do servidor. """
            )
        return "Nenhum", None, "luan.asilva@goias.gov.br", mensagem

    mensagem = (
            f"""
            Prezado(a) {gerente_nome}, venho alertar que o(a) servidor(a) {nome_query}, integrante da sua gerência, solicitou o recadastramento anual. 
            
            Conforme os novos procedimentos adotados pela GGDP, é necessário que o gerente da área autorize enviando para o e-mail atendimento.ggdp.sead@goias.gov.br a autorização de recadastramento dos seus funcionários. 
            """
            )
    print(f"\nNome do gerente responsável: {gerente_nome}\n")
    
    return gerente_nome, gerente_numero, gerente_email, mensagem
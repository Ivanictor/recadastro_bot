import pandas as pd
import unicodedata
from utils.text_similarity import compare_names


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
    df = pd.read_excel("Cadastro de Unidades da SEAD - atualizado.xlsx", skiprows=3, header=0)

    df["SIGLA"] = df["SIGLA"].fillna("").map(normalizar)
    df["UNIDADE"] = df["UNIDADE"].fillna("").map(normalizar)

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
                    Alerta Recadastro: o servidor {nome_query} informou ser integrante da gerência {unidade_query},
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
                    Alerta Recadastro: o servidor {nome_query} informou ser integrante da unidade "{unidade_query}",
                    na solicitação de recadastramento. No entanto, essa unidade não possui gerente responável 
                    no banco de dados informado. Sigam com os procedimentos necessários para o recadastramento 
                    do servidor. """
                )
        return "Nenhum", None, "luan.asilva@goias.gov.br", mensagem

    mensagem = (
                f"""
                Prezado {gerente_nome}, venho alertá-lo de que o servidor {nome_query}, integrante da sua gerência,
                solicitou o recadastramento. Conforme os novos procedimentos adotados pela GGDP, é necessário que o 
                gerente da área assine o processo de recadastramento dos seus funcionários, razão pela qual solicitamos
                a sua assinatura no processo em anexo. """
            )
    print(f"\nNome do gerente responsável: {gerente_nome}\n")
    
    return gerente_nome, gerente_numero, gerente_email, mensagem
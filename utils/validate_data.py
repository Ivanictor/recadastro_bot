import pandas as pd
import unicodedata
from text_similarity import compare_names

def formatar_cpf(cpf: str | None):
    if cpf is None:
        return None
    
    cpf_formatado = cpf.replace(".", "").replace("-", "").strip()
    return cpf_formatado

def validar_cpf(cpf: str) -> bool:
    # Remove caracteres não numéricos
    cpf = "".join(filter(str.isdigit, cpf))

    # CPF deve possuir exatamente 11 dígitos
    if len(cpf) != 11:
        return False

    # Rejeita CPFs com todos os dígitos iguais
    if cpf == cpf[0] * 11:
        return False

    # Primeiro dígito verificador
    soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
    resto = soma % 11
    digito1 = 0 if resto < 2 else 11 - resto

    if int(cpf[9]) != digito1:
        return False

    # Segundo dígito verificador
    soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
    resto = soma % 11
    digito2 = 0 if resto < 2 else 11 - resto

    if int(cpf[10]) != digito2:
        return False

    return True

def validar_foto(foto13, fotorosto13, fotodoc16, fotorosto16):
    if foto13 and fotorosto13:
        return True
    
    if fotodoc16 and fotorosto16:
        return True
    
    print("Fotos não validadas")
    return False

def normalizar(texto):
    texto = texto.strip().lower()

    texto = unicodedata.normalize("NFD", texto)

    texto = "".join(
        c for c in texto
        if unicodedata.category(c) != "Mn"
    )

    return texto

def validar_unidade(unidade):
    df = pd.read_excel("Cadastro de Unidades da SEAD - atualizado (1).xlsx", skiprows=3, header=0)

    df["UNIDADE"] = df["UNIDADE"].fillna("").map(normalizar)

    unidade = normalizar(unidade)

    df["similaridade"] = df["UNIDADE"].apply(
    lambda x: compare_names(unidade, x)
    )

    indice = df["similaridade"]

    resultado = df.loc[indice].idxmax()

    if resultado["similaridade"] < 0.85:
        print("Unidade não encontrada")
        return False

    else:
        return True




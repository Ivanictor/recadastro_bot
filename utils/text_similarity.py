from rapidfuzz import fuzz

def compare_names(name1, name2):
    # Similaridade usando Levenshtein Distance
    levenshtein_score = fuzz.ratio(name1.lower(), name2.lower())
    
    # Similaridade usando Jaro-Winkler (melhor para nomes)
    jaro_winkler_score = fuzz.WRatio(name1.lower(), name2.lower())
    
    # Média ponderada das similaridades
    final_score = (levenshtein_score * 0.5) + (jaro_winkler_score * 0.5)
    
    return final_score/100

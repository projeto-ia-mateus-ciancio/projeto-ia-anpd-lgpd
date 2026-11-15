"""
Projeto: Extracao estruturada de decisoes sancionadoras da ANPD com LLM
Disciplina: Inteligencia Artificial - Prof. Dr. Leandro Zerbinatti - 7oJ SI Noite
Integrante: Mateus Ciancio - RA 10390145 - 10390145@mackenzista.com.br

Sintese: checagens automaticas contra alucinacao. Confere se cada trecho citado
existe no documento e se cada dispositivo aparece no texto e e juridicamente
possivel. Nao depende do gabarito humano.

Historico de alteracoes:
- 03/11/2026, Mateus Ciancio, criacao do arquivo para a entrega N2
- 15/11/2026, Mateus Ciancio, artigo seguido de ordinal (7º) deixava de ser reconhecido
"""
import json
import re

import pandas as pd
from rapidfuzz import fuzz

from comum import EXTRACOES, RESULTADOS, TEXTOS, canonizar_dispositivo, ler_fontes, normalizar_texto

LIMIAR_EVIDENCIA = 90
ULTIMO_ARTIGO_LGPD = 65


def texto_do_processo(identificador: str) -> str:
    fontes = ler_fontes()
    arquivos = fontes[fontes.id == identificador].arquivo
    return " ".join((TEXTOS / f"{a[:-4]}.txt").read_text(encoding="utf-8") for a in arquivos)


def checar(arquivo_json) -> list[dict]:
    dados = json.loads(arquivo_json.read_text(encoding="utf-8"))
    extracao = dados["extracao"]
    original = re.sub(r"\[PAGINA \d+\]", " ", texto_do_processo(dados["id"]))
    normalizado = normalizar_texto(original)
    usou_pdf = dados["entrada"] == "pdf"
    linhas = []
    for conduta in extracao["condutas"]:
        canonico = canonizar_dispositivo(conduta["dispositivo"])
        numero = int(canonico[0].split("art")[1]) if canonico else None
        trecho = normalizar_texto(conduta["evidencia"])
        pontuacao = None if usou_pdf else round(fuzz.partial_ratio(trecho, normalizado), 1)
        no_texto = None
        if canonico and not usou_pdf:
            no_texto = re.search(rf"art(?:igo)?s?\.?\s*{numero}(?!\d)", normalizado) is not None
        tipos = [s["tipo"] for s in conduta["sancoes"]]
        linhas.append({
            "id": dados["id"], "rodada": dados["rodada"], "entrada": dados["entrada"],
            "dispositivo": conduta["dispositivo"], "evidencia": conduta["evidencia"],
            "pontuacao_evidencia": pontuacao,
            "evidencia_confirmada": None if usou_pdf else pontuacao >= LIMIAR_EVIDENCIA,
            "dispositivo_reconhecido": canonico is not None,
            "dispositivo_aparece_no_texto": no_texto,
            "artigo_existe_na_lgpd": (numero <= ULTIMO_ARTIGO_LGPD
                                      if canonico and canonico[0].startswith("LGPD") else None),
            "multa_a_ente_publico": extracao["setor"] == "publico" and "multa_simples" in tipos,
        })
    return linhas


def main() -> None:
    linhas = []
    for arquivo in sorted(EXTRACOES.glob("*.json")):
        linhas.extend(checar(arquivo))
    tabela = pd.DataFrame(linhas)
    tabela.to_csv(RESULTADOS / "validacao.csv", index=False, encoding="utf-8-sig")
    print(f"{len(tabela)} condutas verificadas.")
    if not tabela.empty:
        suspeitas = tabela[(tabela.evidencia_confirmada == False)  # noqa: E712
                           | (tabela.dispositivo_aparece_no_texto == False)  # noqa: E712
                           | (tabela.artigo_existe_na_lgpd == False)  # noqa: E712
                           | tabela.multa_a_ente_publico]
        print(f"{len(suspeitas)} com algum alerta.")


if __name__ == "__main__":
    main()

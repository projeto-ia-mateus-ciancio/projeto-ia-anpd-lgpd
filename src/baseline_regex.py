"""
Projeto: Extracao estruturada de decisoes sancionadoras da ANPD com LLM
Disciplina: Inteligencia Artificial - Prof. Dr. Leandro Zerbinatti - 7oJ SI Noite
Integrante: Mateus Ciancio - RA 10390145 - 10390145@mackenzista.com.br

Sintese: metodo de comparacao sem IA. Procura artigos e sancoes por expressoes
regulares na parte final do documento, para mostrar o ganho real do LLM.

Historico de alteracoes:
- 03/11/2026, Mateus Ciancio, criacao do arquivo para a entrega N2
"""
import re

from comum import TEXTOS, canonizar_dispositivo, ler_fontes, normalizar_texto

PALAVRAS_SANCAO = {
    "advertencia": "advertencia", "multa simples": "multa_simples", "multa diaria": "multa_diaria",
    "publicizacao": "publicizacao", "bloqueio": "bloqueio", "eliminacao": "eliminacao",
}
ARTIGO = re.compile(r"art(?:igo)?s?\.?\s*\d{1,3}")


def trecho_decisorio(texto: str) -> str:
    """Devolve a parte do texto entre a ultima 'conclusao' e os 'encaminhamentos'."""
    t = normalizar_texto(re.sub(r"\[PAGINA \d+\]", " ", texto))
    posicoes = [m.start() for m in re.finditer(r"\bconclus(?:ao|oes)\b", t)]
    if not posicoes:
        return t[-6000:]
    inicio = posicoes[-1] if len(t) - posicoes[-1] > 300 else posicoes[max(len(posicoes) - 2, 0)]
    fim = t.find("encaminhamento", inicio)
    return t[inicio:] if fim == -1 else t[inicio:fim]


def extrair(identificador: str) -> dict:
    """Prefere o despacho, quando existe; caso contrario usa o relatorio."""
    fontes = ler_fontes()
    grupo = fontes[fontes.id == identificador]
    escolhidos = grupo[grupo.tipo_doc == "despacho"]
    if escolhidos.empty:
        escolhidos = grupo
    pares = set()
    dispositivos = set()
    for arquivo in escolhidos.arquivo:
        texto = (TEXTOS / f"{arquivo[:-4]}.txt").read_text(encoding="utf-8")
        base = trecho_decisorio(texto) if grupo.tipo_doc.eq("relatorio").all() else normalizar_texto(texto)
        for frase in re.split(r"(?<=[;:])\s+|(?<=\.)\s+(?=[a-z])", base):
            achados = [canonizar_dispositivo(m.group()) for m in ARTIGO.finditer(frase)]
            achados = [a for a in achados if a]
            sancoes = [v for k, v in PALAVRAS_SANCAO.items() if k in frase]
            if not achados or not sancoes:
                continue
            for artigo, _ in achados[:1]:
                dispositivos.add(artigo)
                pares.update((artigo, s) for s in sancoes)
    return {"dispositivos": dispositivos, "pares": pares}

"""
Projeto: Extracao estruturada de decisoes sancionadoras da ANPD com LLM
Disciplina: Inteligencia Artificial - Prof. Dr. Leandro Zerbinatti - 7oJ SI Noite
Integrante: Mateus Ciancio - RA 10390145 - 10390145@mackenzista.com.br

Sintese: caminhos, leitura de fontes e normalizacao de dispositivos legais
usados por todas as etapas do pipeline.

Historico de alteracoes:
- 03/11/2026, Mateus Ciancio, criacao do arquivo para a entrega N2
"""
import os
import re
import sys
import unicodedata
from pathlib import Path

import pandas as pd

RAIZ = Path(os.environ.get("PROJETO_RAIZ", Path(__file__).resolve().parents[1]))
FONTES = RAIZ / "dados" / "fontes.csv"
PDFS = RAIZ / "dados" / "pdfs"
TEXTOS = RAIZ / "dados" / "textos"
GABARITO = RAIZ / "dados" / "gabarito" / "gabarito_manual.xlsx"
RESULTADOS = RAIZ / "resultados"
EXTRACOES = RESULTADOS / "extracoes"
MINIMO_CARACTERES_POR_PAGINA = 300

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def ler_fontes() -> pd.DataFrame:
    return pd.read_csv(FONTES, dtype=str, encoding="utf-8")


def sem_acento(texto: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", texto) if not unicodedata.combining(c))


def normalizar_texto(texto: str) -> str:
    """Minusculas, sem acento e com espacos unicos, para comparar trechos."""
    return re.sub(r"\s+", " ", sem_acento(texto or "").lower()).strip()


ORDINAL = re.compile(r"[ºª°]|(?<=\d)o\b")
PADRAO_ART = re.compile(
    r"art(?:igo)?s?\.?\s*(\d{1,3})\s*(?:[,;]?\s*(?:inciso\s+)?\b([ivxlc]{1,6})\b)?(?:\s*[,;]?\s*§\s*(\d+|unico))?"
)


def canonizar_dispositivo(valor: str) -> tuple[str, str] | None:
    """Converte um dispositivo livre em (artigo, artigo com inciso).

    'LGPD, art. 6º, VIII' -> ('LGPD art6', 'LGPD art6-viii')
    Devolve None quando nao ha numero de artigo reconhecivel.
    """
    t = normalizar_texto(valor)
    t = ORDINAL.sub("", t)
    m = PADRAO_ART.search(t)
    if not m:
        return None
    norma = "RFANPD" if re.search(r"rfanpd|resolu|regulamento|cd/anpd", t) else "LGPD"
    artigo = f"{norma} art{int(m.group(1))}"
    return artigo, artigo + (f"-{m.group(2)}" if m.group(2) else "")


SANCOES_VALIDAS = {
    "advertencia", "multa_simples", "multa_diaria", "publicizacao", "bloqueio",
    "eliminacao", "suspensao_banco", "suspensao_tratamento", "proibicao_tratamento",
}


def canonizar_sancao(valor: str) -> str:
    t = normalizar_texto(valor).replace(" ", "_").replace("-", "_")
    apelidos = {
        "multa": "multa_simples", "publicizacao_da_infracao": "publicizacao",
        "eliminacao_de_dados": "eliminacao",
    }
    return apelidos.get(t, t)

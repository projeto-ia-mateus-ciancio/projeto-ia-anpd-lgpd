"""
Projeto: Extracao estruturada de decisoes sancionadoras da ANPD com LLM
Disciplina: Inteligencia Artificial - Prof. Dr. Leandro Zerbinatti - 7oJ SI Noite
Integrante: Mateus Ciancio - RA 10390145 - 10390145@mackenzista.com.br

Sintese: extrai o texto de cada PDF, mascara CPF e e-mail, e identifica
documentos sem camada de texto (digitalizados), que seguem para o LLM como PDF.

Historico de alteracoes:
- 03/11/2026, Mateus Ciancio, criacao do arquivo para a entrega N2
"""
import re

import pandas as pd
from pypdf import PdfReader

from comum import MINIMO_CARACTERES_POR_PAGINA, PDFS, RESULTADOS, TEXTOS, ler_fontes

CPF = re.compile(r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b")
EMAIL = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")


def mascarar(texto: str) -> str:
    return EMAIL.sub("[EMAIL]", CPF.sub("[CPF]", texto))


def main() -> None:
    TEXTOS.mkdir(parents=True, exist_ok=True)
    registros = []
    for linha in ler_fontes().to_dict("records"):
        leitor = PdfReader(PDFS / linha["arquivo"])
        paginas = [f"[PAGINA {n}]\n{p.extract_text() or ''}" for n, p in enumerate(leitor.pages, 1)]
        texto = mascarar("\n".join(paginas))
        n = len(leitor.pages)
        uteis = len(re.sub(r"\[PAGINA \d+\]|\s", "", texto))
        media = uteis / n if n else 0
        (TEXTOS / f"{linha['arquivo'][:-4]}.txt").write_text(texto, encoding="utf-8")
        registros.append({
            "id": linha["id"], "arquivo": linha["arquivo"], "tipo_doc": linha["tipo_doc"],
            "paginas": n, "caracteres": uteis, "caracteres_por_pagina": round(media, 1),
            "tem_camada_de_texto": media >= MINIMO_CARACTERES_POR_PAGINA,
        })
        print(f"{linha['arquivo']}: {n} paginas, {media:.0f} caracteres por pagina")
    tabela = pd.DataFrame(registros)
    tabela.to_csv(RESULTADOS / "documentos.csv", index=False, encoding="utf-8-sig")
    print(f"\nDocumentos digitalizados: {(~tabela.tem_camada_de_texto).sum()} de {len(tabela)}")


if __name__ == "__main__":
    main()

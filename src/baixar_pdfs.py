"""
Projeto: Extracao estruturada de decisoes sancionadoras da ANPD com LLM
Disciplina: Inteligencia Artificial - Prof. Dr. Leandro Zerbinatti - 7oJ SI Noite
Integrante: Mateus Ciancio - RA 10390145 - 10390145@mackenzista.com.br

Sintese: baixa os PDFs oficiais listados em dados/fontes.csv e registra o
hash SHA-256 de cada arquivo, para que a coleta possa ser auditada.

Historico de alteracoes:
- 03/11/2026, Mateus Ciancio, criacao do arquivo para a entrega N2
"""
import hashlib
import time

import pandas as pd
import requests

from comum import PDFS, RESULTADOS, ler_fontes

CABECALHO = {"User-Agent": "Mozilla/5.0 (projeto academico; Universidade Presbiteriana Mackenzie)"}


def baixar(url: str) -> bytes | None:
    try:
        r = requests.get(url, headers=CABECALHO, timeout=90)
    except requests.RequestException as erro:
        print(f"    falhou: {erro}")
        return None
    if r.ok and r.content[:5] == b"%PDF-":
        return r.content
    print(f"    falhou: HTTP {r.status_code}, conteudo nao e PDF")
    return None


def main() -> None:
    PDFS.mkdir(parents=True, exist_ok=True)
    RESULTADOS.mkdir(exist_ok=True)
    registros, faltando = [], []
    for linha in ler_fontes().to_dict("records"):
        destino = PDFS / linha["arquivo"]
        origem = "ja existia"
        if not destino.exists():
            origem = ""
            for url in linha["urls"].split("|"):
                print(f"Baixando {linha['arquivo']}")
                conteudo = baixar(url.strip())
                if conteudo:
                    destino.write_bytes(conteudo)
                    origem = url.strip()
                    break
                time.sleep(2)
            time.sleep(2)
        if not destino.exists():
            faltando.append(linha)
            continue
        registros.append({
            "arquivo": linha["arquivo"],
            "origem": origem,
            "bytes": destino.stat().st_size,
            "sha256": hashlib.sha256(destino.read_bytes()).hexdigest(),
        })
    pd.DataFrame(registros).to_csv(RESULTADOS / "coleta.csv", index=False, encoding="utf-8-sig")
    print(f"\n{len(registros)} PDF(s) prontos em dados/pdfs.")
    if faltando:
        print("\nFALTAM estes arquivos. Baixe pelo navegador, na pagina Decisoes em Processos")
        print("Sancionadores da ANPD, e salve em dados/pdfs com exatamente este nome:")
        for f in faltando:
            print(f"  {f['arquivo']}  <-  {f['entidade']}: {f['documento']}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()

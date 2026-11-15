"""
Projeto: Extracao estruturada de decisoes sancionadoras da ANPD com LLM
Disciplina: Inteligencia Artificial - Prof. Dr. Leandro Zerbinatti - 7oJ SI Noite
Integrante: Mateus Ciancio - RA 10390145 - 10390145@mackenzista.com.br

Sintese: envia cada processo ao Gemini com saida estruturada, varias vezes,
guardando cada resposta. Se a cota acabar, basta rodar de novo: o que ja foi
extraido e reaproveitado.

Historico de alteracoes:
- 03/11/2026, Mateus Ciancio, criacao do arquivo para a entrega N2
- 05/11/2026, Mateus Ciancio, log em arquivo e mais tolerancia a instabilidade
- 06/11/2026, Mateus Ciancio, refaz extracoes de modelo diferente do configurado
- 10/11/2026, Mateus Ciancio, opcao de modelo local via Ollama, sem chave nem cota
"""
import json
import os
import time
import traceback
from datetime import datetime, timezone

import httpx
import pandas as pd
import re
import requests
from dotenv import load_dotenv
from google import genai
from google.genai import errors, types

from comum import EXTRACOES, PDFS, RAIZ, RESULTADOS, TEXTOS, ler_fontes
from esquema import PROMPT, VERSAO_PROMPT, Extracao

TENTATIVAS = 6
FALHAS_SEGUIDAS_MAXIMAS = 3
TEMPO_LIMITE_MS = 240_000
LIMITE_CARACTERES_LOCAL = 60_000
PAGINA_CHAVE = re.compile(r"CONCLUS|DECIDE|DISPOSITIVO|Por viola|infra[cç][aã]o ao|agente de tratamento", re.I)


def selecionar_paginas(texto: str) -> str:
    """Para o modelo local (contexto menor): primeiras paginas e paginas decisorias, com a seguinte."""
    partes = re.split(r"(\[PAGINA \d+\]\n)", texto)
    paginas = [(partes[i], partes[i + 1]) for i in range(1, len(partes) - 1, 2)]
    escolhidas = {0, 1}
    for n, (_, corpo) in enumerate(paginas):
        if PAGINA_CHAVE.search(corpo):
            escolhidas.update({n, n + 1})
    saida = ""
    for n in sorted(escolhidas):
        if n < len(paginas):
            saida += paginas[n][0] + paginas[n][1]
    return saida


def chamar_ollama(modelo: str, partes: list, semente: int) -> tuple[Extracao, dict]:
    url = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434") + "/api/chat"
    corpo = {
        "model": modelo, "stream": False, "think": False,
        "format": Extracao.model_json_schema(),
        "options": {"temperature": 0, "seed": semente, "num_ctx": 24576, "num_predict": 3000},
        "messages": [{"role": "user", "content": "\n".join(partes)}],
    }
    for tentativa in range(1, 4):
        try:
            r = requests.post(url, json=corpo, timeout=420)
            r.raise_for_status()
            dados = r.json()
            extracao = Extracao.model_validate_json(dados["message"]["content"])
            return extracao, {"tokens_entrada": dados.get("prompt_eval_count"),
                              "tokens_saida": dados.get("eval_count")}
        except requests.ConnectionError:
            raise SystemExit("O Ollama nao esta aberto. Abra o app Ollama e rode de novo.")
        except (requests.RequestException, ValueError, KeyError) as erro:
            avisar(f"    resposta invalida do modelo local ({type(erro).__name__}), tentativa {tentativa}")
    raise RuntimeError("Modelo local sem resposta valida apos 3 tentativas.")
LOG = RESULTADOS / "log_extracao.txt"


def avisar(mensagem: str) -> None:
    """Mostra a mensagem na tela e guarda no log, para nada se perder se a janela fechar."""
    print(mensagem)
    with LOG.open("a", encoding="utf-8") as arquivo:
        arquivo.write(f"{datetime.now().isoformat(timespec='seconds')} {mensagem}\n")


def montar_partes(grupo: pd.DataFrame, digitalizados: set[str], processo: str) -> tuple[list, str]:
    partes: list = [PROMPT.format(processo=processo)]
    entrada = "texto"
    for linha in grupo.to_dict("records"):
        if linha["arquivo"] in digitalizados:
            entrada = "pdf"
            partes.append(types.Part.from_bytes(data=(PDFS / linha["arquivo"]).read_bytes(),
                                                mime_type="application/pdf"))
        else:
            texto = (TEXTOS / f"{linha['arquivo'][:-4]}.txt").read_text(encoding="utf-8")
            if os.environ.get("PROVEDOR") == "ollama":
                texto = selecionar_paginas(texto)
            partes.append(f"--- {linha['documento']} ---\n{texto}")
    return partes, entrada


def chamar(cliente: genai.Client, modelo: str, partes: list, semente: int) -> tuple[Extracao, dict]:
    configuracao = types.GenerateContentConfig(
        temperature=0, seed=semente, response_mime_type="application/json", response_schema=Extracao,
    )
    for tentativa in range(1, TENTATIVAS + 1):
        try:
            resposta = cliente.models.generate_content(model=modelo, contents=partes, config=configuracao)
            extracao = Extracao.model_validate_json(resposta.text)
            uso = resposta.usage_metadata
            return extracao, {
                "tokens_entrada": getattr(uso, "prompt_token_count", None),
                "tokens_saida": getattr(uso, "candidates_token_count", None),
            }
        except errors.ClientError as erro:
            if erro.code != 429 or "perday" in str(erro).lower().replace(" ", ""):
                raise
            espera = 60 * tentativa
            avisar(f"    cota por minuto atingida, aguardando {espera}s")
        except errors.ServerError as erro:
            espera = 60 * tentativa
            avisar(f"    servidor indisponivel (HTTP {erro.code}), aguardando {espera}s")
        except httpx.TransportError as erro:
            espera = 60 * tentativa
            avisar(f"    falha de rede ({type(erro).__name__}), aguardando {espera}s")
        except ValueError as erro:
            espera = 5
            avisar(f"    resposta invalida ({type(erro).__name__}), repetindo")
        time.sleep(espera)
    raise RuntimeError(f"Sem resposta valida apos {TENTATIVAS} tentativas.")


def executar() -> None:
    load_dotenv(RAIZ / ".env")
    if os.environ.get("PROVEDOR") == "ollama":
        return executar_local()
    chave = os.environ.get("GEMINI_API_KEY", "")
    if not chave or chave.startswith("cole_"):
        raise SystemExit("Crie o arquivo .env a partir do .env.exemplo e coloque sua chave.")
    modelo = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash-lite")
    pausa = float(os.environ.get("PAUSA_SEGUNDOS", "20"))
    rodadas = int(os.environ.get("RODADAS", "3"))
    http = {"timeout": TEMPO_LIMITE_MS}
    if os.environ.get("GEMINI_BASE_URL"):
        http["base_url"] = os.environ["GEMINI_BASE_URL"]
    opcoes = {"http_options": types.HttpOptions(**http)}
    cliente = genai.Client(api_key=chave, **opcoes)

    documentos = pd.read_csv(RESULTADOS / "documentos.csv")
    digitalizados = set(documentos.loc[~documentos.tem_camada_de_texto, "arquivo"])
    EXTRACOES.mkdir(parents=True, exist_ok=True)

    falhas = 0
    seguidas = 0
    for identificador, grupo in ler_fontes().groupby("id", sort=True):
        processo = grupo.iloc[0]["processo"]
        partes, entrada = montar_partes(grupo, digitalizados, processo)
        for rodada in range(1, rodadas + 1):
            destino = EXTRACOES / f"{identificador}_r{rodada}.json"
            if destino.exists():
                if json.loads(destino.read_text(encoding="utf-8")).get("modelo") == modelo:
                    continue
            avisar(f"{identificador} rodada {rodada}")
            inicio = time.time()
            try:
                extracao, uso = chamar(cliente, modelo, partes, semente=rodada)
            except errors.ClientError as erro:
                if erro.code == 429:
                    avisar(f"COTA DO DIA ESGOTADA. Rode de novo amanha; nada se perde. Detalhe: {erro.message}")
                    raise SystemExit(1)
                avisar(f"ERRO DA API ({erro.code}): {erro.message}")
                raise SystemExit("Se o modelo nao existir, troque GEMINI_MODEL no arquivo .env.")
            except RuntimeError as erro:
                avisar(f"    {erro}")
                falhas += 1
                seguidas += 1
                if seguidas >= FALHAS_SEGUIDAS_MAXIMAS:
                    avisar("GOOGLE INSTAVEL: parei para nao gastar tempo. Rode de novo mais tarde; nada se perde.")
                    raise SystemExit(1)
                continue
            seguidas = 0
            destino.write_text(json.dumps({
                "id": identificador, "processo": processo, "rodada": rodada, "modelo": modelo,
                "versao_prompt": VERSAO_PROMPT, "entrada": entrada,
                "segundos": round(time.time() - inicio, 1), "uso": uso,
                "data_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "extracao": extracao.model_dump(mode="json"),
            }, ensure_ascii=False, indent=2), encoding="utf-8")
            time.sleep(pausa)
    if falhas:
        avisar(f"{falhas} extracao(oes) falharam. Rode de novo para tentar apenas essas.")
        raise SystemExit(1)
    avisar("Extracao concluida.")


def executar_local() -> None:
    modelo = os.environ.get("OLLAMA_MODEL", "qwen3:8b")
    rodadas = int(os.environ.get("RODADAS", "2"))
    documentos = pd.read_csv(RESULTADOS / "documentos.csv")
    digitalizados = set(documentos.loc[~documentos.tem_camada_de_texto, "arquivo"])
    if digitalizados:
        raise SystemExit("Ha PDF sem texto; o modelo local precisa de texto extraido.")
    EXTRACOES.mkdir(parents=True, exist_ok=True)
    falhas = 0
    for identificador, grupo in ler_fontes().groupby("id", sort=True):
        processo = grupo.iloc[0]["processo"]
        partes, _ = montar_partes(grupo, digitalizados, processo)
        tamanho = sum(len(p) for p in partes)
        if tamanho > LIMITE_CARACTERES_LOCAL:
            avisar(f"{identificador}: texto selecionado com {tamanho} caracteres; mantendo o final do documento")
            partes = [partes[0], "".join(partes[1:])[-(LIMITE_CARACTERES_LOCAL - len(partes[0])):]]
        for rodada in range(1, rodadas + 1):
            destino = EXTRACOES / f"{identificador}_r{rodada}.json"
            if destino.exists() and json.loads(destino.read_text(encoding="utf-8")).get("modelo") == modelo:
                continue
            avisar(f"{identificador} rodada {rodada} (modelo local {modelo})")
            inicio = time.time()
            try:
                extracao, uso = chamar_ollama(modelo, partes, semente=rodada)
            except RuntimeError as erro:
                # Falha do modelo conta como erro na avaliacao: resposta vazia, sem acertos.
                avisar(f"    {erro} Registrada como extracao vazia (falha do modelo).")
                falhas += 1
                extracao = Extracao(papel="nao_informado", setor="publico", fase="sugerida_no_relatorio",
                                    condutas=[], evidencia_papel="")
                uso = {"tokens_entrada": None, "tokens_saida": None}
            destino.write_text(json.dumps({
                "id": identificador, "processo": processo, "rodada": rodada, "modelo": modelo,
                "versao_prompt": VERSAO_PROMPT, "entrada": "texto_paginas_selecionadas",
                "falha_do_modelo": extracao.condutas == [] and extracao.evidencia_papel == "",
                "segundos": round(time.time() - inicio, 1), "uso": uso,
                "data_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "extracao": extracao.model_dump(mode="json"),
            }, ensure_ascii=False, indent=2), encoding="utf-8")
    if falhas:
        avisar(f"{falhas} extracao(oes) sem resposta valida, registradas como erro do modelo.")
    avisar("Extracao concluida.")


def main() -> None:
    RESULTADOS.mkdir(parents=True, exist_ok=True)
    try:
        executar()
    except SystemExit:
        raise
    except Exception:
        avisar("ERRO INESPERADO:\n" + traceback.format_exc())
        raise SystemExit(1)


if __name__ == "__main__":
    main()

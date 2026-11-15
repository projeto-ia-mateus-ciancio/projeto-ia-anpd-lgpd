"""
Projeto: Extracao estruturada de decisoes sancionadoras da ANPD com LLM
Disciplina: Inteligencia Artificial - Prof. Dr. Leandro Zerbinatti - 7oJ SI Noite
Integrante: Mateus Ciancio - RA 10390145 - 10390145@mackenzista.com.br

Sintese: compara LLM e metodo sem IA com o gabarito humano, calcula precisao,
revocacao e F1, mede a consistencia entre rodadas e gera o dataset final.

Historico de alteracoes:
- 03/11/2026, Mateus Ciancio, criacao do arquivo para a entrega N2
- 06/11/2026, Mateus Ciancio, metricas usam somente rodadas completas
"""
import json
import random
from itertools import combinations

import pandas as pd

import baseline_regex
from comum import (EXTRACOES, GABARITO, RAIZ, RESULTADOS, SANCOES_VALIDAS, canonizar_dispositivo,
                   canonizar_sancao, ler_fontes)

TOLERANCIA_REAIS = 1.0
REAMOSTRAGENS = 2000


def ler_gabarito() -> tuple[dict, pd.DataFrame]:
    processos = pd.read_excel(GABARITO, sheet_name="processos", dtype=str).fillna("")
    sancoes = pd.read_excel(GABARITO, sheet_name="sancoes", dtype=str).fillna("")
    sancoes = sancoes[sancoes.id.str.strip() != ""].copy()
    nao_concluidos = processos[processos.concluido.str.lower() != "sim"].id.tolist()
    if nao_concluidos:
        raise SystemExit(f"Gabarito incompleto. Marque concluido=sim em: {', '.join(nao_concluidos)}")
    gabarito = {}
    for linha in processos.to_dict("records"):
        gabarito[linha["id"]] = {
            "papel": linha["papel"].strip(), "setor": linha["setor"].strip().lower(),
            "fase": linha["fase"].strip(), "dispositivos": set(), "detalhes": set(), "pares": set(),
            "multa_total": 0.0, "corretiva": {},
        }
    for numero, linha in enumerate(sancoes.to_dict("records"), 2):
        canonico = canonizar_dispositivo(linha["dispositivo"])
        tipo = canonizar_sancao(linha["tipo_sancao"])
        if canonico is None or tipo not in SANCOES_VALIDAS or linha["id"] not in gabarito:
            raise SystemExit(f"Linha {numero} da aba sancoes invalida: {linha}")
        item = gabarito[linha["id"]]
        item["dispositivos"].add(canonico[0])
        item["detalhes"].add(canonico[1])
        item["pares"].add((canonico[0], tipo))
        if tipo == "multa_simples" and linha["valor_reais"]:
            item["multa_total"] += float(linha["valor_reais"].replace(",", "."))
        if linha["medida_corretiva"]:
            item["corretiva"][canonico[0]] = linha["medida_corretiva"].strip().lower() == "sim"
    return gabarito, sancoes


def ler_extracao(extracao: dict) -> dict:
    saida = {"papel": extracao["papel"], "setor": extracao["setor"], "fase": extracao["fase"],
             "dispositivos": set(), "detalhes": set(), "pares": set(), "multa_total": 0.0, "corretiva": {}}
    for conduta in extracao["condutas"]:
        canonico = canonizar_dispositivo(conduta["dispositivo"])
        if canonico is None:
            saida["dispositivos"].add("nao_reconhecido:" + conduta["dispositivo"])
            continue
        saida["dispositivos"].add(canonico[0])
        saida["detalhes"].add(canonico[1])
        saida["corretiva"][canonico[0]] = conduta["medida_corretiva"]
        for sancao in conduta["sancoes"]:
            saida["pares"].add((canonico[0], sancao["tipo"]))
            if sancao["tipo"] == "multa_simples" and sancao["valor_reais"]:
                saida["multa_total"] += sancao["valor_reais"]
    return saida


def prf(contagens: list[tuple[int, int, int]]) -> tuple[float, float, float]:
    vp = sum(c[0] for c in contagens)
    fp = sum(c[1] for c in contagens)
    fn = sum(c[2] for c in contagens)
    precisao = vp / (vp + fp) if vp + fp else 0.0
    revocacao = vp / (vp + fn) if vp + fn else 0.0
    f1 = 2 * precisao * revocacao / (precisao + revocacao) if precisao + revocacao else 0.0
    return precisao, revocacao, f1


def contar(previsto: set, correto: set) -> tuple[int, int, int]:
    return len(previsto & correto), len(previsto - correto), len(correto - previsto)


def intervalo_f1(contagens: list[tuple[int, int, int]]) -> tuple[float, float]:
    """Intervalo de 95% por reamostragem de processos."""
    gerador = random.Random(42)
    valores = sorted(prf(gerador.choices(contagens, k=len(contagens)))[2] for _ in range(REAMOSTRAGENS))
    return valores[int(0.025 * REAMOSTRAGENS)], valores[int(0.975 * REAMOSTRAGENS) - 1]


def medir(metodo: str, rodada: int, previsoes: dict, gabarito: dict) -> list[dict]:
    linhas = []
    for campo, nome in (("dispositivos", "artigo infringido"),
                        ("detalhes", "artigo com inciso"),
                        ("pares", "artigo e sancao")):
        contagens = [contar(previsoes[i][campo], gabarito[i][campo]) for i in gabarito if i in previsoes]
        if metodo == "regex" and campo == "detalhes":
            continue
        p, r, f = prf(contagens)
        baixo, alto = intervalo_f1(contagens)
        linhas.append({"metodo": metodo, "rodada": rodada, "metrica": nome, "processos": len(contagens),
                       "precisao": p, "revocacao": r, "f1": f, "f1_ic95_min": baixo, "f1_ic95_max": alto})
    if metodo == "llm":
        for campo in ("papel", "setor", "fase"):
            acertos = [previsoes[i][campo] == gabarito[i][campo] for i in gabarito if i in previsoes]
            linhas.append({"metodo": metodo, "rodada": rodada, "metrica": f"acuracia {campo}",
                           "processos": len(acertos), "acuracia": sum(acertos) / len(acertos)})
        acertos = [abs(previsoes[i]["multa_total"] - gabarito[i]["multa_total"]) <= TOLERANCIA_REAIS
                   for i in gabarito if i in previsoes]
        linhas.append({"metodo": metodo, "rodada": rodada, "metrica": "acuracia multa total",
                       "processos": len(acertos), "acuracia": sum(acertos) / len(acertos)})
        marcados = [previsoes[i]["corretiva"].get(a) == v for i in gabarito if i in previsoes
                    for a, v in gabarito[i]["corretiva"].items()]
        if marcados:
            linhas.append({"metodo": metodo, "rodada": rodada, "metrica": "acuracia medida corretiva",
                           "processos": len(marcados), "acuracia": sum(marcados) / len(marcados)})
    return linhas


def sem_vazios(tabela: dict) -> dict:
    return {nome: {k: v for k, v in linha.items() if pd.notna(v)} for nome, linha in tabela.items()}


def jaccard(a: set, b: set) -> float:
    return 1.0 if not a and not b else len(a & b) / len(a | b)


def main() -> None:
    gabarito, sancoes = ler_gabarito()
    rodadas: dict[int, dict] = {}
    custo = []
    for arquivo in sorted(EXTRACOES.glob("*.json")):
        dados = json.loads(arquivo.read_text(encoding="utf-8"))
        rodadas.setdefault(dados["rodada"], {})[dados["id"]] = ler_extracao(dados["extracao"])
        custo.append({"id": dados["id"], "rodada": dados["rodada"], "modelo": dados["modelo"],
                      "entrada": dados["entrada"], "segundos": dados["segundos"], **dados["uso"]})
    # Rodadas incompletas nao entram nas metricas, para todas cobrirem os mesmos processos.
    rodadas = {n: p for n, p in rodadas.items() if set(gabarito) <= set(p)}
    custo = [c for c in custo if c["rodada"] in rodadas]
    if not rodadas:
        raise SystemExit("Nenhuma rodada completa em resultados/extracoes. Termine a extracao.")

    metricas = []
    for numero, previsoes in sorted(rodadas.items()):
        metricas.extend(medir("llm", numero, previsoes, gabarito))
    regex = {i: baseline_regex.extrair(i) for i in gabarito}
    for item in regex.values():
        item.setdefault("detalhes", set())
    metricas.extend(medir("regex", 0, regex, gabarito))
    tabela = pd.DataFrame(metricas)
    tabela.to_csv(RESULTADOS / "metricas.csv", index=False, encoding="utf-8-sig")

    consistencia = []
    for identificador in gabarito:
        conjuntos = [r[identificador]["pares"] for r in rodadas.values() if identificador in r]
        for a, b in combinations(conjuntos, 2):
            consistencia.append({"id": identificador, "jaccard": jaccard(a, b)})
    consistencia = pd.DataFrame(consistencia, columns=["id", "jaccard"])

    erros = []
    for numero, previsoes in sorted(rodadas.items()):
        for identificador, previsto in previsoes.items():
            correto = gabarito[identificador]
            for par in sorted(previsto["pares"] - correto["pares"]):
                erros.append({"id": identificador, "rodada": numero, "erro": "a mais", "item": " / ".join(par)})
            for par in sorted(correto["pares"] - previsto["pares"]):
                erros.append({"id": identificador, "rodada": numero, "erro": "faltou", "item": " / ".join(par)})
    pd.DataFrame(erros, columns=["id", "rodada", "erro", "item"]).to_csv(
        RESULTADOS / "erros.csv", index=False, encoding="utf-8-sig")

    fontes = ler_fontes().drop_duplicates("id")[["id", "processo", "entidade", "setor", "ano_lista"]]
    papeis = pd.DataFrame([{"id": i, "papel": g["papel"], "fase": g["fase"]} for i, g in gabarito.items()])
    final = sancoes.merge(fontes, on="id").merge(papeis, on="id")
    colunas = ["id", "processo", "entidade", "setor", "ano_lista", "papel", "fase", "dispositivo",
               "tipo_sancao", "valor_reais", "medida_corretiva", "pagina_pdf"]
    final[colunas].to_csv(RAIZ / "dados" / "dataset_final.csv", index=False, encoding="utf-8-sig")

    custo = pd.DataFrame(custo)
    custo.to_csv(RESULTADOS / "custo.csv", index=False, encoding="utf-8-sig")
    llm = tabela[tabela.metodo == "llm"]
    resumo = {
        "modelo": sorted(custo.modelo.unique().tolist()),
        "rodadas": len(rodadas),
        "extracoes": len(custo),
        "consistencia_jaccard_media": None if consistencia.empty else round(consistencia.jaccard.mean(), 4),
        "tokens_entrada_medio": None if custo.tokens_entrada.isna().all() else round(custo.tokens_entrada.mean()),
        "segundos_medio": round(custo.segundos.mean(), 1),
        "llm_media_por_metrica": sem_vazios(
            llm.groupby("metrica")[["precisao", "revocacao", "f1", "acuracia"]].mean().round(4).to_dict("index")),
        "regex": sem_vazios(tabela[tabela.metodo == "regex"].set_index("metrica")[["precisao", "revocacao", "f1"]]
                            .round(4).to_dict("index")),
        "erros_total": len(erros),
    }
    (RESULTADOS / "resumo.json").write_text(json.dumps(resumo, ensure_ascii=False, indent=2, default=str),
                                            encoding="utf-8")
    print(tabela.round(3).to_string())
    print("\nResumo salvo em resultados/resumo.json")


if __name__ == "__main__":
    main()

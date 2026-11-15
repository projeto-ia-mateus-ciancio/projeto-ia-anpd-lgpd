"""
Projeto: Extracao estruturada de decisoes sancionadoras da ANPD com LLM
Disciplina: Inteligencia Artificial - Prof. Dr. Leandro Zerbinatti - 7oJ SI Noite
Integrante: Mateus Ciancio - RA 10390145 - 10390145@mackenzista.com.br

Sintese: gera a planilha de gabarito preenchida manualmente pelo autor.

Historico de alteracoes:
- 03/11/2026, Mateus Ciancio, criacao do arquivo para a entrega N2
"""
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.datavalidation import DataValidation

from comum import GABARITO, SANCOES_VALIDAS, ler_fontes

COR = PatternFill("solid", fgColor="DCE6F1")
LINHAS_SANCOES = 60


def lista(aba, coluna, valores, ultima):
    regra = DataValidation(type="list", formula1='"' + ",".join(valores) + '"', allow_blank=True)
    aba.add_data_validation(regra)
    regra.add(f"{coluna}2:{coluna}{ultima}")


def cabecalho(aba, colunas, larguras):
    aba.append(colunas)
    for indice, largura in enumerate(larguras, 1):
        celula = aba.cell(1, indice)
        celula.font = Font(bold=True)
        celula.fill = COR
        aba.column_dimensions[celula.column_letter].width = largura
    aba.freeze_panes = "A2"


def main() -> None:
    pasta = Workbook()
    instrucoes = pasta.active
    instrucoes.title = "instrucoes"
    instrucoes.column_dimensions["A"].width = 110
    for texto in [
        "GABARITO MANUAL - preencha lendo os PDFs, ANTES de abrir qualquer resultado do LLM.",
        "",
        "Aba processos: uma linha por processo. Ao terminar um processo, coloque concluido = sim.",
        "Aba sancoes: uma linha para cada combinacao de dispositivo e sancao.",
        "",
        "Onde olhar: Secao 'Conclusao' do relatorio. Se existir Despacho Decisorio, ele vale sobre o relatorio.",
        "Isso acontece em P01 (arquivo separado) e P09 (o despacho vem nas primeiras paginas do mesmo PDF).",
        "",
        "dispositivo: escreva 'LGPD art. 48', 'LGPD art. 6, VIII' ou 'RFANPD art. 32'.",
        "Inclua somente dispositivos reconhecidos como infringidos, nao os citados como fundamento.",
        "RFANPD e o Regulamento de Fiscalizacao (Resolucao CD/ANPD no 1/2021).",
        "valor_reais: apenas para multa, com ponto decimal. Ex.: 14400.00",
        "medida_corretiva: sim ou nao.",
        "pagina_pdf: pagina do PDF onde voce achou a informacao.",
        "fase: sugerida_no_relatorio ou aplicada_em_despacho, conforme a ultima peca disponivel.",
    ]:
        instrucoes.append([texto])
    instrucoes["A1"].font = Font(bold=True)

    processos = pasta.create_sheet("processos")
    cabecalho(processos, ["id", "processo", "entidade", "arquivos", "papel", "setor", "fase", "concluido", "observacoes"],
              [6, 24, 44, 30, 24, 10, 24, 11, 40])
    fontes = ler_fontes()
    for identificador, grupo in fontes.groupby("id", sort=True):
        primeiro = grupo.iloc[0]
        processos.append([identificador, primeiro.processo, primeiro.entidade, ", ".join(grupo.arquivo),
                          None, primeiro.setor.lower(), None, None, None])
    ultima = len(processos["A"])
    lista(processos, "E", ["controlador", "operador", "controlador_e_operador", "nao_informado"], ultima)
    lista(processos, "G", ["sugerida_no_relatorio", "aplicada_em_despacho"], ultima)
    lista(processos, "H", ["sim", "nao"], ultima)

    sancoes = pasta.create_sheet("sancoes")
    cabecalho(sancoes, ["id", "dispositivo", "tipo_sancao", "valor_reais", "medida_corretiva", "pagina_pdf", "observacoes"],
              [6, 24, 24, 16, 17, 11, 40])
    lista(sancoes, "A", sorted(fontes.id.unique()), LINHAS_SANCOES)
    lista(sancoes, "C", sorted(SANCOES_VALIDAS), LINHAS_SANCOES)
    lista(sancoes, "E", ["sim", "nao"], LINHAS_SANCOES)
    for aba in (processos, sancoes):
        for linha in aba.iter_rows(min_row=1, max_row=1):
            for celula in linha:
                celula.alignment = Alignment(vertical="center")

    GABARITO.parent.mkdir(parents=True, exist_ok=True)
    pasta.save(GABARITO)
    print(f"Gabarito criado em {GABARITO}")


if __name__ == "__main__":
    main()

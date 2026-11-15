"""
Projeto: Extracao estruturada de decisoes sancionadoras da ANPD com LLM
Disciplina: Inteligencia Artificial - Prof. Dr. Leandro Zerbinatti - 7oJ SI Noite
Integrante: Mateus Ciancio - RA 10390145 - 10390145@mackenzista.com.br

Sintese: define o esquema de saida exigido do LLM e o prompt de extracao.

Historico de alteracoes:
- 03/11/2026, Mateus Ciancio, criacao do arquivo para a entrega N2
"""
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

VERSAO_PROMPT = "v1"


class Papel(str, Enum):
    controlador = "controlador"
    operador = "operador"
    controlador_e_operador = "controlador_e_operador"
    nao_informado = "nao_informado"


class Setor(str, Enum):
    publico = "publico"
    privado = "privado"


class Fase(str, Enum):
    sugerida_no_relatorio = "sugerida_no_relatorio"
    aplicada_em_despacho = "aplicada_em_despacho"


class TipoSancao(str, Enum):
    advertencia = "advertencia"
    multa_simples = "multa_simples"
    multa_diaria = "multa_diaria"
    publicizacao = "publicizacao"
    bloqueio = "bloqueio"
    eliminacao = "eliminacao"
    suspensao_banco = "suspensao_banco"
    suspensao_tratamento = "suspensao_tratamento"
    proibicao_tratamento = "proibicao_tratamento"


class Sancao(BaseModel):
    tipo: TipoSancao
    valor_reais: Optional[float] = Field(None, description="Valor em reais; nulo se nao houver valor.")


class Conduta(BaseModel):
    dispositivo: str = Field(description="Ex.: 'LGPD art. 48' ou 'LGPD art. 6, VIII' ou 'RFANPD art. 32'.")
    descricao: str = Field(description="Conduta em ate 25 palavras, sem nome de pessoa fisica.")
    sancoes: list[Sancao]
    medida_corretiva: bool
    evidencia: str = Field(description="Trecho literal copiado do documento, de 10 a 40 palavras.")


class Extracao(BaseModel):
    papel: Papel
    setor: Setor
    fase: Fase
    condutas: list[Conduta]
    evidencia_papel: str = Field(description="Trecho literal que sustenta o papel do agente.")


PROMPT = """Voce extrai dados de processos sancionadores da Agencia Nacional de Protecao de Dados.
Responda somente com base no documento abaixo.

Regras:
1. Considere apenas as infracoes reconhecidas ao final do documento, nao as hipoteses afastadas nem os
   dispositivos citados apenas como fundamento procedimental ou de dosimetria.
2. Se houver um Despacho Decisorio, use as sancoes dele (fase aplicada_em_despacho). Se houver apenas
   Relatorio de Instrucao, use as sancoes recomendadas (fase sugerida_no_relatorio).
3. Crie uma conduta por dispositivo infringido. Se um dispositivo tiver mais de uma sancao, liste todas.
4. "dispositivo" comeca com LGPD ou, para o Regulamento de Fiscalizacao, com RFANPD.
5. "evidencia" deve ser copiada literalmente do documento. Nao resuma, nao corrija e nao invente.
6. Nunca inclua nome de pessoa fisica, CPF ou e-mail.
7. Se a informacao nao estiver no documento, use nao_informado ou nulo, sem deduzir.

DOCUMENTO DO PROCESSO {processo}:
"""

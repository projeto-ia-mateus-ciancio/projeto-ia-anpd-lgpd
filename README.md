# Extração estruturada de decisões sancionadoras da ANPD com LLM

Projeto da disciplina de Inteligência Artificial, Prof. Dr. Leandro Zerbinatti, 7ºJ SI Noite, Universidade Presbiteriana Mackenzie.

**Integrante:** Mateus Ciancio, RA 10390145, 10390145@mackenzista.com.br
**Repositório:** https://github.com/projeto-ia-mateus-ciancio/projeto-ia-anpd-lgpd
**Vídeo:** LINK_DO_YOUTUBE

## O que o projeto faz

Modelo avaliado: Qwen3 8B (qwen3:8b), executado localmente pelo Ollama. Rode `2_rodar_local.bat` para reproduzir.

Avalia com que confiabilidade um modelo de linguagem extrai, dos 10 processos sancionadores publicados pela ANPD, o papel do agente de tratamento, os dispositivos infringidos e as sanções. A referência é um gabarito humano, e a comparação é feita com um método sem IA.

## Estrutura

| Caminho | Conteúdo |
|---|---|
| `relatorio/` | Artigo final e relatório da N1 |
| `dados/fontes.csv` | Processos e links oficiais |
| `dados/dataset_final.csv` | Dataset validado |
| `dados/gabarito/` | Gabarito manual |
| `dados/legado_n1/` | Arquivos da primeira entrega, mantidos para rastreabilidade |
| `src/` | Pipeline em Python |
| `notebooks/` | Análise exploratória |
| `resultados/` | Extrações, validação, métricas e figuras |
| `tests/` | Teste com dados fictícios e API simulada |

## Como reproduzir no Windows

1. Instale o Ollama (ollama.com) e execute `1_instalar.bat`.
2. Execute `2_rodar_local.bat`.
3. Preencha `dados/gabarito/gabarito_manual.xlsx`.
4. Execute `3_avaliar.bat`.

## Observações

- Os PDFs não são redistribuídos: o repositório guarda os links e o hash SHA-256 de cada arquivo.
- As saídas do modelo são resultados de pesquisa e não constituem análise jurídica.

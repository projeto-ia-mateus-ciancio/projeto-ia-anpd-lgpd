# Passo a passo da N2

Faça nesta ordem. Sempre que algo der erro, mande a mensagem no chat.

## Parte 1: preparar (15 min)

1. Extraia este zip em uma pasta simples, como `C:\projeto-ia-anpd-lgpd`.
2. Se ainda não tiver Python, instale em python.org e marque **Add python.exe to PATH**.
3. Crie a chave em https://aistudio.google.com/apikey, usando sua conta Google.
4. Dê dois cliques em `1_instalar.bat`.
5. Abra o arquivo `.env` no Bloco de Notas, troque `cole_sua_chave_aqui` pela chave e salve.

Nunca mande a chave no chat e nunca envie o arquivo `.env` ao GitHub.

## Parte 2: extrair (de 30 min a 1 h, sem precisar acompanhar)

1. Dê dois cliques em `2_rodar_extracao.bat`.
2. Se faltar algum PDF, a janela diz qual é. Baixe pelo navegador em
   https://www.gov.br/anpd/pt-br/centrais-de-conteudo/decisoes-em-processos-sancionadores,
   salve em `dados\pdfs` com o nome indicado e rode de novo.
3. Se a cota do dia acabar, rode de novo no dia seguinte. O que já foi feito não se perde.
4. Se aparecer erro de modelo inexistente, ou cota zero para o modelo, troque `GEMINI_MODEL` no `.env`
   por um modelo Flash disponível na sua conta e rode de novo.

**Não abra `resultados\extracoes`.** Olhar as respostas antes do gabarito invalida a comparação.

## Parte 3: gabarito (cerca de 2 h, pode dividir em vários dias)

1. Abra `dados\gabarito\gabarito_manual.xlsx` e leia a aba **instrucoes**.
2. Abra cada PDF em `dados\pdfs` e vá direto à seção **Conclusão**. Em P01 e P09, siga também o Despacho Decisório.
3. Preencha as abas **processos** e **sancoes**, marcando `concluido = sim` em cada processo.

## Parte 4: avaliar (5 min)

1. Dê dois cliques em `3_avaliar.bat`.
2. Mande no chat o arquivo `resultados_para_o_claude.zip`.

Com ele, completo os trechos em amarelo do artigo e preparo o roteiro do vídeo.

## Parte 5: GitHub e vídeo (depois do artigo pronto)

1. Grave o vídeo, publique no YouTube e coloque o link no artigo e no `README.md`.
2. No GitHub, abra sua foto > **Organizations** > **New organization** > plano **Free**.
3. No repositório `projeto-ia-anpd-lgpd`, vá em **Settings** > **Danger Zone** > **Transfer ownership** e escolha a organização.
4. Dê dois cliques em `4_preparar_github.bat`.
5. Envie ao repositório **somente o conteúdo da pasta `para_github`**.
6. Abra o link em uma aba anônima para confirmar que está público.

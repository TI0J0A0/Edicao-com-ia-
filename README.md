# Edicao-com-ia-TI0J0A0

Backup das ferramentas de edição do canal TiojoaoYT (lives da Twitch → séries de episódios no YouTube).

- `Scripts/` — sistema de edição V4 (rodar da raiz: `python Scripts/<script>.py`): análise audiovisual, memória narrativa, bordas que não cortam fala, transições, validador, render paralelo, QC, revisor independente, memória editorial, testes (`Scripts/testes/`), benchmark e comparação de métodos. Relatório da V4: `Scripts/RELATORIO_V4.md`. Configuração central em `Scripts/config/`; geradores de plano em `Scripts/planos/`; registro de links em `Scripts/links_processados.json`.
- `Estilo/` — guia único dos vídeos longos (`ESTILO - video longo V4.md`), guia dos Shorts e artes de encerramento.
- `.claude/skills/` — skills do Claude Code (`video-longo` = roteiro curto da V4, transcrição, plano de edição etc.).

Vídeos, brutos, transcrições e entregas (`Bruto/`, `Trabalho/`, `videos_longos/`, `Final/`, `shorts/`) ficam fora do repositório de propósito.

Para restaurar: clonar este repositório dentro da pasta do projeto.

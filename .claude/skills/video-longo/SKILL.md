---
name: video-longo
description: Edita uma live inteira do TiojoaoYT (Twitch/arquivo, 1–9 h) numa SÉRIE de episódios de 50–60 min para o YouTube com o sistema V4 — análise multimodal, memória narrativa, plano com bordas que nunca cortam fala, transições por contexto, render paralelo, QC e revisor independente. Use sempre que o João mandar um link de live/VOD ou pedir "vídeo longo", "série", "partes", "editar a live".
---

# Vídeo longo V4 — roteiro curto

Regras completas: `Estilo/ESTILO - video longo V4.md`. Ler só as seções necessárias. Números ficam em `Scripts/config/`. Tudo roda da raiz: `python Scripts/<script>.py`.

## Antes de tudo
1. `python Scripts/checar_link.py <link>`: se der **JÁ PROCESSADO**, avisar o João e parar.
2. `python Scripts/checar_ambiente.py`
3. `python Scripts/registrar_feedback.py resumo`: erros e preferências anteriores. Respeitar sempre.

## Fluxo
1. **Baixar** a fonte 1080p60 para `Bruto/`, mais o áudio e o proxy 160p para `Trabalho/longo_<jogo>_<vod>/` (yt-dlp do `%USERPROFILE%\whisper-env`). Rodar `silencedetect=n=-50dB:d=20` para achar os blocos mudos da Twitch.
2. **Transcrever:** `transcrever_longo.py` (blocos com checkpoint; dá para planejar com a transcrição parcial).
3. **Analisar:** `analisar_live.py <proxy> <cache> --facecam auto --fonte-wh 1920x1080 --transcricao <T> --quadros <fonte>`. Conferir `facecam.jpg`, porque a posição da câmera muda entre lives.
4. **Entender a live (economia de tokens):** ler primeiro o `resumo_ia.txt` (1 linha/min). Só depois abrir a transcrição e os painéis de `quadros/` nos trechos marcados. Preencher o `narrativa.json` (`memoria_narrativa.py iniciar` → preencher → `checar`) com eventos, evidência e `depende_de`.
5. **Plano:** copiar o gerador modelo `Scripts/planos/plano_gta_2938905930_gerar.py` (bordas V4 via `Bordas`). Decisões: PRESERVAR INTEGRALMENTE / MANTER / CONDENSAR / REMOVER / REVISAR. Escolher o `perfil` do jogo. Remoções relevantes vão para `removidos_relevantes` com o motivo. Mostrar o plano ao João e **esperar o "Aprovado"**.
6. `transicoes.py <plano>` → `validar_plano.py <plano>` (0 erros) → se for útil, `montar_episodios.py --plano <plano> --previa-emendas`.
7. `renderizar_serie.py --plano <plano>`: 3 partes em paralelo, QC e revisor (`revisao.md`).
8. **Corrigir** o que o QC ou o revisor apontar (local, causa, correção) e rodar de novo. Só os pedaços alterados são recodificados. **Não entregar** com PROBLEMAS nem com revisor REPROVADO/PENDENTE.
9. **Entregar** em `videos_longos/<Jogo>/`: `GTA VI - VOD (DD-MM-AAAA) PARTE - N.mp4`, o relatório (`relatorio_longo.py`) e os títulos com a descrição fixa (seção 7 do guia). Acrescentar a live ao `links_processados.json`.
10. **Feedback** do João: `registrar_feedback.py add ...`. Se for recorrente, vira regra em script e teste em `Scripts/testes/`.

## Nunca
- Postar ou agendar sem ordem explícita.
- Cortar fala ou diálogo do jogo, principalmente no fim do episódio.
- Entregar trecho travado.
- Gerar thumbnail.
- Usar blur fora de nudez real.
- Apagar `Scripts/` ou os originais.
- Inventar evento ou timestamp.

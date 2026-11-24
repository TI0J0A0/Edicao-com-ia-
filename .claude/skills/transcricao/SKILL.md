---
name: transcricao
description: Transcreve localmente (Whisper, grátis, offline) o vídeo da pasta bruto/ em português e salva em trabalho/ o texto com o tempo de início e fim de cada frase, cada palavra e as pausas. Use sempre que o usuário pedir para transcrever, legendar, "tirar o texto", gerar SRT ou preparar um vídeo bruto para edição — mesmo que não diga "transcrição" — e antes de montar um plano de edição se ainda não houver transcrição em trabalho/.
---

# Transcrição de vídeo (Whisper local)

Esta skill transforma o vídeo bruto em texto com tempos, que é a base de toda a edição (cortes, letreiros, zooms). Tudo roda no computador do usuário, sem custo.

## Ambiente já instalado

- Python com faster-whisper: `%USERPROFILE%\whisper-env\Scripts\python.exe`
- FFmpeg (winget, Gyan.FFmpeg)
- Script: `.claude/skills/transcricao/scripts/transcrever.py` (relativo à raiz do projeto)

Se o Python acima não existir, avise o usuário e reinstale: `py -3.13 -m venv %USERPROFILE%\whisper-env` e depois `pip install faster-whisper "av<16"` (o av 16+ quebra o faster-whisper 1.2.x).

## Passos

1. **Escolher o vídeo.** Liste os arquivos de vídeo/áudio em `bruto/` (mp4, mov, mkv, webm, m4a, mp3, wav). Se o usuário indicou um arquivo, use esse. Se houver só um, use-o. Se houver vários, pergunte qual (mostrando nome e data) — transcrever o errado custa minutos.
2. **Rodar a transcrição** (PowerShell, a partir da raiz do projeto; use timeout longo ou rode em segundo plano, porque leva mais ou menos o tempo do vídeo em CPU):
   ```powershell
   & "$env:USERPROFILE\whisper-env\Scripts\python.exe" ".claude\skills\transcricao\scripts\transcrever.py" "bruto\<arquivo>" "trabalho"
   ```
   - Modelo padrão `turbo` (bom em português e rápido; ~1,6 GB baixados na primeira vez). Se o usuário quiser mais rapidez, `--modelo small`; mais precisão, `--modelo large-v3`.
   - `--idioma pt` já é o padrão.
3. **Conferir o resultado.** Abra o `.txt` gerado e verifique se o texto faz sentido (não está em outro idioma, não tem frases repetidas em loop). Se estiver ruim, tente de novo com `--modelo large-v3`.
4. **Mostrar ao usuário**, em linguagem simples: duração do vídeo, número de frases, número de pausas longas, as 5 primeiras frases como amostra, e onde os arquivos ficaram. Sugira o próximo passo: a skill `plano-de-edicao`.

## Arquivos gerados em `trabalho/`

- `<nome>_transcricao.txt` — legível: `[00:00:01.200 -> 00:00:04.000] frase`
- `<nome>_transcricao.json` — para as outras skills: `frases` (id, inicio, fim, texto, palavras com tempo), `pausas` (silêncios ≥ 0,7 s entre palavras, com a palavra antes e depois), `duracao`.
- `<nome>_transcricao.srt` — legenda pronta para o YouTube.

Tempos estão em segundos. Não edite nem mova o vídeo original em `bruto/`.

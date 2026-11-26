# Comparação de métodos — coletor10

Vídeo: `Trabalho/teste_v4/trecho10.mp4` · perfil soulslike_acao+narrativo · 6 trechos

## Bordas (tempo na live)

| Trecho | Bruto | A (v3) | corta fala? | B (V4) | corta fala? |
|---|---|---|---|---|---|
| 1 fim | 0:00:28.50 | 0:00:28.58 | SIM — dentro da frase 28.06–29.06 | 0:00:29.46 | não |
| 2 início | 0:00:33.00 | 0:00:33.00 | não | 0:00:32.85 | não |
| 2 fim | 0:03:40.00 | 0:03:40.00 | não | 0:03:40.35 | não |
| 3 início | 0:04:12.00 | 0:04:12.00 | não | 0:04:11.85 | não |
| 3 fim | 0:05:18.00 | 0:05:17.88 | SIM — dentro da frase 316.10–318.92 | 0:05:19.32 | não |
| 4 início | 0:05:25.00 | 0:05:24.56 | SIM — dentro da frase 324.14–325.34 | 0:05:23.44 | não |
| 4 fim | 0:05:48.00 | 0:05:47.96 | SIM — dentro da frase 346.18–350.38 | 0:05:51.83 | não |
| 5 início | 0:06:09.00 | 0:06:09.00 | não | 0:06:08.85 | não |
| 5 fim | 0:09:08.50 | 0:09:08.50 | SIM — voz no áudio na borda (+35 dB acima do fundo) — diálogo do jogo? | 0:09:11.25 | SIM — fala recomeça logo depois |
| 6 início | 0:09:45.00 | 0:09:45.00 | não | 0:09:44.85 | não |
| 6 fim | 0:09:57.00 | 0:09:57.02 | SIM — dentro da frase 596.50–598.12 | 0:09:58.52 | SIM — voz no áudio na borda (+19 dB acima do fundo) — diálogo do jogo? |

## Transições escolhidas no V4

- trecho 2: **corte** — cena parecida (dif 10): corte invisível; ATENÇÃO: voz dos dois lados — mover a borda (Bordas.fim) em vez de sobrepor falas
- trecho 3: **corte** — corte com crossfade (dif 23, salto 32s)
- trecho 4: **corte** — corte com crossfade (dif 29, salto 4s)
- trecho 5: **corte** — corte com crossfade (dif 25, salto 17s)
- trecho 6: **corte** (audio_desloc +0.80s) — cena parecida (dif 11): corte invisível; L-cut 0.8s: a fala de A continua depois do corte e B começa sem voz

Validação do plano V4: 7 erro(s), 0 aviso(s)
- Parte 1 trecho 5 fim 0:09:12.05: dentro da frase 551.58–552.84 -> usar 0:09:18.48 (Bordas.fim)
- Parte 1 FIM DO EPISÓDIO 0:09:58.52: voz no áudio na borda (+19 dB acima do fundo) — diálogo do jogo? -> usar 0:09:58.87 (Bordas.fim)
- travamento da live 0:08:29 (2s) dentro de trecho mantido — cortar ou cobrir
- travamento da live 0:08:39 (2s) dentro de trecho mantido — cortar ou cobrir
- travamento da live 0:08:45 (2s) dentro de trecho mantido — cortar ou cobrir
- travamento da live 0:08:50 (1s) dentro de trecho mantido — cortar ou cobrir
- travamento da live 0:08:55 (2s) dentro de trecho mantido — cortar ou cobrir

## Resultado

| | A (v3) | B (V4) |
|---|---|---|
| Duração | 493.0s | 505.5s |
| FPS | 60/1 | 60/1 |
| Problemas no QC | 6 | 6 |
| Avisos no QC | 12 | 9 |
| Falas cortadas (QC) | 4 | 2 |
| Travamentos (QC) | 14 | 13 |
| Revisor: problemas | 12 | 8 |
| Revisor: avisos | 13 | 10 |
| Veredito do revisor | REPROVADO | REPROVADO |
| Tempo: plano | 0.01s | 14.48s |
| Tempo: render | 54s | 303s |
| Tempo: QC | 44s | 42s |

Problemas de QC — A: TRAVAMENTO 442.60s–443.62s (1.02s): jogo e facecam parados juntos — lag da live ou render; cortar/cobrir ou re-renderizar; TRAVAMENTO 452.60s–453.62s (1.02s): jogo e facecam parados juntos — lag da live ou render; cortar/cobrir ou re-renderizar; TRAVAMENTO 458.60s–459.62s (1.02s): jogo e facecam parados juntos — lag da live ou render; cortar/cobrir ou re-renderizar; TRAVAMENTO 462.60s–463.62s (1.02s): jogo e facecam parados juntos — lag da live ou render; cortar/cobrir ou re-renderizar; TRAVAMENTO 468.60s–469.62s (1.02s): jogo e facecam parados juntos — lag da live ou render; cortar/cobrir ou re-renderizar; possível FALA CORTADA no FIM do episódio (493.0s): voz +32 dB acima do fundo até o corte — o fim do episódio não pode cortar fala

Problemas de QC — B: TRAVAMENTO 450.72s–451.73s (1.02s): jogo e facecam parados juntos — lag da live ou render; cortar/cobrir ou re-renderizar; TRAVAMENTO 460.72s–461.73s (1.02s): jogo e facecam parados juntos — lag da live ou render; cortar/cobrir ou re-renderizar; TRAVAMENTO 466.72s–467.73s (1.02s): jogo e facecam parados juntos — lag da live ou render; cortar/cobrir ou re-renderizar; TRAVAMENTO 470.72s–471.73s (1.02s): jogo e facecam parados juntos — lag da live ou render; cortar/cobrir ou re-renderizar; TRAVAMENTO 476.72s–477.73s (1.02s): jogo e facecam parados juntos — lag da live ou render; cortar/cobrir ou re-renderizar; possível FALA CORTADA no FIM do episódio (505.5s): voz +38 dB acima do fundo até o corte — o fim do episódio não pode cortar fala

Revisões completas: `Trabalho\comparacao_coletor10/A_v3_revisao.md` e `Trabalho\comparacao_coletor10/B_v4_revisao.md`. Vídeos: `Trabalho\comparacao_coletor10/A_v3.mp4` e `Trabalho\comparacao_coletor10/B_v4.mp4`.

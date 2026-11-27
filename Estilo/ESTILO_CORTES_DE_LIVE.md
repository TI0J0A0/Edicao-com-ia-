# Estilo dos clipes curtos — "cortes de live" (desde 2026-11-20)

Mesmo visual do projeto `cortes-de-live` (referências: `esqueleto-tela.png`, `layout-esperado.webp`, `encerramento-exemplo.png`).
Substitui `antigos/ESTILO_CORTES_TIOJOAO_CLAUDE.md`. Script: `C:\Python314\python.exe Trabalho/montar_cortes.py --plano ... --saida "shorts/..."`.

## Tela 1080 × 1920, layout fixo do começo ao fim
- **Facecam em cima**: y 0–760, largura total, recorte proporcional em volta do rosto (sem esticar, sem zoom exagerado).
- **Degradê**: os últimos 160 px da facecam somem suavemente sobre a gameplay. Sem linha dura nem faixa.
- **Gameplay embaixo**: de y=600 até o fim da tela. A ação, o personagem e o HUD importante ficam visíveis.
- Nunca troca de enquadramento no meio do vídeo (sem tela cheia do jogo, sem close, sem horizontal).

## Título
- Selo amarelo arredondado (#FFD60A), texto preto em MAIÚSCULAS (fonte Anton), centrado na emenda (y=760), até 2 linhas.
- 4 a 9 palavras, com curiosidade e tensão, sem entregar o final. Fica na tela até o card final.

## Legenda
- 3 palavras por vez, MAIÚSCULAS, Arial Bold 76, branca com contorno preto; a palavra que está sendo dita fica amarela.
- Centro em y=1574. Segue o tempo de cada palavra da transcrição.
- Falas do jogo audíveis também entram (traduzidas se forem em inglês). Risadas e sons não viram legenda.
- Nada inventado: só o que dá para ouvir.

## Barra de progresso
- Amarela, 12 px, no rodapé, enchendo da esquerda para a direita.

## Encerramento
- Nos últimos 5 s (no máximo 40% do vídeo): o vídeo desfoca e escurece, e o card `encerramento-ao-vivo.png`
  ("Venha assistir ao vivo" com Twitch, Kick e YouTube) entra com fade e zoom leve.
- Título e legenda somem nesse trecho. Tudo termina com fade out de vídeo e áudio (0,6 s).
- Por isso o momento principal do clipe tem que acontecer antes dos últimos 5 s.

## Áudio e qualidade
- Só o áudio original (jogo + voz), normalizado a -14 LUFS. Sem música nem efeitos.
- H.264 crf 16 preset slow, 60 fps, AAC 256 kbps. Saída em `shorts/`.

## Escolha do momento (de `cortes-de-live/referencias/como-escolher.md`)
- A ação precisa ser entendida nos 3 primeiros segundos; a história tem preparação → ação → reação.
- Normalmente 18 a 50 s. Prioridade: jogada decisiva, boss, susto, falha engraçada, descoberta, reação a história.
- Sempre mostrar o plano e esperar "Aprovado" antes de renderizar.

## Estilo novo: reação dinâmica (referência Paulinho LOKO — João 2026-11-26, SÓ para vídeos curtos e Shorts)
Opcional: usar quando o João pedir ou indicar no plano (`"estilo": "reacao_dinamica"`). **Nunca** na série longa.
Medido num corte de 15 min do canal de referência: ~3,7 cortes por minuto, tomada típica de ~5 s e nenhuma pausa muda.
- **Facecam que cresce na reação:** em reação forte (susto, risada, grito, surpresa), a câmera aumenta (~2x) por 1 a 3 s e depois volta. No Short, o mesmo vira um zoom de ~1,15 dentro da área da facecam.
- **Zoom de ênfase:** zoom rápido (punch-in) no detalhe do jogo que causou a reação (carro raro, item, placa, mapa).
- **Cortes secos frequentes:** sai toda pausa e toda espera; só fica preparação → ação → reação.
- **Título chamativo:** CAIXA ALTA com o fato e um emoji no fim (ex.: "ACHEI UM CARRO SUPER RARO NO GTA 6 😱"), sem mentir sobre o conteúdo.
- **Continuam iguais:** só o áudio original, sem música, e a mesma tela final.
- **Situação:** documentado; os efeitos (facecam que cresce e zoom de ênfase) entram no `montar_cortes.py` no primeiro vídeo curto que usar este estilo, com teste antes.

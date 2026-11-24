# TiojoaoYT | Padrão de edição de Shorts gamers

**Versão:** 2.0 — perfil "Reel de perseguição"  
**Referência:** https://www.instagram.com/reel/Df8Ef2wj2Fn/  
**Fonte da análise da referência:** descrição detalhada fornecida pelo criador. O vídeo original **não foi visualizado diretamente** nesta revisão. Use o que está descrito aqui; não invente frames, timecodes, transições, falas ou detalhes não documentados.

> **ORDEM PRINCIPAL PARA O CLAUDE:** edite a partir das gravações reais da live. Reproduza a *linguagem de edição* deste Reel, não necessariamente os mesmos acontecimentos. A história, os diálogos, a risada e a emoção do jogo comandam a edição. Não acrescente elementos que não existiam nem transforme o gameplay em um podcast.

## 1. O padrão observado na referência (reproduzir com fidelidade)

| Item | Característica informada | Regra para outros Shorts |
|---|---|---|
| Formato | Vídeo vertical; duração aproximada de **65 segundos** | Exportar 9:16; **não** forçar limite de 30–40 s. A duração depende da sequência real. |
| Layout habitual | **Facecam superior ~28%** e **gameplay inferior ~72%** | Usar como enquadramento **base** da maior parte do clipe. |
| Divisão | **Corte reto, sem moldura ou borda** | Separação simples, sem barra decorativa, cantos arredondados, sombra ou fundo chamativo. |
| Exceções visuais | Gameplay em tela cheia em **dois picos**: perseguição da Shirley e queda dela na grama | Em novos clipes, tela cheia nos picos decisivos **quando a gameplay precisar de destaque**; não exigir dois picos em toda história. |
| Reação facial | **Zoom fechado da facecam perto do fim**, no auge da reação | Dar destaque ao rosto quando houver reação genuína que justifique o zoom. Não forçar o efeito em toda cena. |
| Legendas | Legendas **queimadas**, em todas as falas do jogo e do streamer | Legendar vozes audíveis dos dois, sincronizando com a fala. |
| Aparência da legenda | **Sans bold branca, contorno preto**, centralizada no rodapé, **até 2 linhas** | Legenda de frase/bloco completo, natural. **Não** usar legenda dinâmica palavra a palavra ou pílulas vermelhas. |
| Ênfase | Termos como **"Shirley"** e **"scooter de mobilidade"** aparecem **em vermelho inline** | Destacar somente nomes, objetivos ou expressões realmente presentes e relevantes na fala. |
| Objetivo | **Linha menor do objetivo da missão logo abaixo** | Usar apenas quando o texto do objetivo existir no jogo/fonte e for relevante. Não inventar objetivos. |
| Áudio | Som do jogo + voz e risada do streamer. **Sem trilha extra ou efeitos sonoros adicionados** | A reação real é o conteúdo. Preservar risadas, silêncios e sons originais. |
| Ritmo | **Uma sequência contínua**, sem saltar entre momentos diferentes | Preservar geografia, cronologia e causa/consequência. Cortar apenas interrupções sem valor narrativo. |
| Abertura | Começa **direto na ação**, sem cartela ou título | Começar no primeiro instante compreensível e forte, com o mínimo de contexto necessário. |
| Encerramento | Acaba **no meio da fuga**, sem tela final | Aceitar final aberto quando a interrupção for natural/engraçada. Não impor moral, CTA nem encerramento fabricado. |
| Marca | **Sem marca d'água** @tiojoaoyt | **Desativar por padrão neste perfil de referência**. Só adicionar por opção explícita do criador. |

### Estrutura narrativa específica do Reel (EXEMPLO, NÃO TEMPLATE OBRIGATÓRIO)

**Setup → perseguição → queda → pausa cômica em pé sobre ela → fuga.**

O humor nasce do próprio acontecimento e da risada do streamer. A continuidade deixa a situação se tornar cada vez mais engraçada. A pausa sobre a personagem faz parte da piada e **não deve ser removida para acelerar o Short**. A fuga começa antes do fim, e o corte final deixa a história em aberto.

**Não copiar "Shirley", "scooter de mobilidade", perseguição ou queda para outros jogos** se esses acontecimentos não estiverem na gravação. Copiar a lógica: **situação reconhecível → complicação crescente → reação verdadeira → payoff ou interrupção natural**.

## 2. Geometria e enquadramento

**Tela de saída recomendada:** 1080 × 1920 (9:16), MP4; manter o FPS real da fonte (até 60 fps quando existir 60 fps original). Layout de referência:

- **Facecam:** 28% da altura = aproximadamente **538 px** (região vertical `y=0…537`).
- **Gameplay:** 72% da altura = aproximadamente **1382 px** (região `y=538…1919`).
- **Divisão:** uma linha de encontro reta entre os dois vídeos, **sem borda gráfica**.
- Os percentuais são **aproximados**, não uma exigência de correspondência pixel a pixel. A legibilidade prevalece.

**Facecam:**

- Usar crop inteligente da **câmera real da live**, centralizando rosto e expressões de forma natural. Não esticar, alterar a proporção do rosto nem fazer crop agressivo na boca, testa ou queixo.
- **Não destruir a nitidez:** se a webcam estiver pequena e comprimida dentro do VOD, não ampliar indiscriminadamente; usar a fonte separada quando existir. Se só houver webcam embutida, respeitar seus limites, ajustar o enquadramento e apontar perda inevitável de definição.
- O enquadramento deve ficar estável na maior parte do vídeo. Não usar zooms automáticos por batida, palavra ou cronômetro.

**Gameplay:**

- Manter personagem, perseguidor, alvo, ação principal e informações relevantes do HUD visíveis no espaço vertical.
- Ao ampliar para tela cheia, mostrar **a gameplay** (não a webcam), salvo no momento específico de close da reação.
- Priorizar cortes secos entre os estados **split → gameplay full-screen → split**, usando a continuidade visual e sonora. Fade não é regra do Reel descrito; só utilizar se for justificado por uma transição real de cena e não quebrar o ritmo.
- Usar **close de facecam** breve quando a reação tiver valor próprio. Não fabricar uma expressão a partir de um frame ou trecho desconectado.

### Estados visuais para implementação

- `SPLIT_BASE`: facecam 28% superior / gameplay 72% inferior, sem moldura.
- `GAMEPLAY_FOCUS`: gameplay ocupa a tela toda, com crop/reframe que preserve a ação.
- `FACECAM_REACTION`: close da webcam apenas durante a reação decisiva, sem esticar ou inventar pixels.

**Transições entre estados são motivadas por eventos**, não por duração fixa. Se nenhuma mudança ajuda a narrativa, permanecer no `SPLIT_BASE`.

## 3. Legendas obrigatórias

**Regra central deste perfil:** **todas as falas inteligíveis do streamer E dos personagens do jogo recebem legendas queimadas**. Se vozes se sobrepuserem, priorizar legibilidade e atribuição correta, sem inventar palavras.

### Estilo

- Fonte **sans-serif bold** legível; usar Inter Bold, Montserrat Bold ou equivalente se disponível.
- **Branco** (`#FFFFFF`) com **contorno preto** (`#000000`) suficientemente nítido; evitar caixa/pílula/placa de fundo permanente.
- Texto **centralizado na parte inferior**, até **duas linhas**.
- Legendar em **frases ou blocos de sentido**, sem animação de uma palavra por vez.
- Preservar pontuação natural, tom coloquial, risada quando vocalizada e nomes próprios corretos.
- **Vermelho inline** (`#DC2626`, ajustável para legibilidade) em nomes importantes ou objetos de missão quando efetivamente presentes. As outras palavras permanecem brancas com contorno preto.
- **Linha adicional de objetivo** com fonte menor, logo abaixo da legenda principal **somente quando houver um objetivo real a exibir**. Essa linha é um complemento informativo, não uma terceira linha de fala. Não acrescentá-la em vídeos sem objetivo mostrado ou citado.
- Manter margens de segurança para interfaces de Reels, TikTok e Shorts. Ajustar a altura do bloco quando necessário para não encobrir personagem, HUD ou informação essencial.

### Exemplo de comportamento (apenas ilustrativo)

- Fala do jogo: `A Shirley está vindo!` → legenda completa, com **Shirley** em vermelho dentro da frase.
- Fala do streamer: `Eu não acredito que isso aconteceu!` → mesmo padrão tipográfico, sem cor especial por obrigação.
- Objetivo real presente na gravação: legenda normal + **objetivo menor abaixo**. A frase exata deve ser extraída da origem, **nunca inventada**.

**Não fazer:** texto de uma palavra por vez, karaokê automático, caixa vermelha em cada palavra, títulos gigantes, emoticons automáticos, legenda genérica de podcast, palavras adivinhadas ou atribuição incorreta de fala.

## 4. Áudio: a risada É a narrativa

1. Manter **som original do jogo**, diálogos, voz e **risadas reais** do streamer.
2. **Não adicionar** música de fundo, whooshes, pop sounds, risadas enlatadas, meme sounds ou efeitos externos.
3. Ajustar níveis somente para que as falas sejam entendidas. Não comprimir tanto que a risada perca dinâmica e pareça artificial.
4. Preservar os micro-silêncios, respirações e pausas que criam timing cômico, inclusive a pausa depois da queda.
5. Evitar cortes de áudio no meio de uma reação e verificar sincronização entre voz, facecam e ação.
6. Se o jogo já contiver música, essa música é **parte do áudio original** e pode permanecer; a regra é não adicionar trilha nova.

## 5. Ritmo e seleção dos momentos da live

- Identificar **múltiplos momentos fortes** do VOD, sem limite arbitrário de três clipes. Cada Short é uma **única história compreensível**, preferencialmente um mesmo acontecimento contínuo.
- **Não** montar uma sequência de acontecimentos desconectados como se fossem um único evento, nem reorganizar a cronologia para criar reações falsas.
- Cortes internos são aceitáveis para remover espera ou repetição **quando não destruírem a sensação de continuidade**. No Reel de referência, a percepção é de uma cena contínua.
- Abertura sem título: entrar direto no acontecimento. Não colocar "VOCÊ NÃO VAI ACREDITAR", abertura de canal, contagem regressiva ou bumper.
- Manter build-up, reação, consequência e pausas cômicas. O silêncio ou o personagem parado podem ser fundamentais.
- **Duração variável**, incluindo Shorts em torno de **65 s** quando a história precisar. Nem todo clipe precisa ter 65 s; não reduzir automaticamente para 30–40 s.
- Final sem tela de encerramento e **sem marca d'água** neste perfil. Permitir final aberto/abrupto no meio da ação quando isso reproduzir o timing real.
- Para chefes, sustos, cenas emocionais e reviews, usar a mesma identidade gráfica, mas adaptar narrativa e intensidade; não exigir perseguição, queda nem zoom de reação em todos os jogos.

## 6. Compatibilidade com o ESTILO.md do canal

O `ESTILO.md` geral define personalidade, naturalidade, foco na gameplay e ausência de efeitos gratuitos. **Este arquivo é um perfil específico de edição para Shorts**, que tem precedência sobre regras gerais **somente quando houver conflito visual explícito**:

| Tema | Guia geral do canal | Perfil deste Reel |
|---|---|---|
| Layout | Enquadramento flexível | Split 28/72 como estado principal; tela cheia nos picos. |
| Legendas | Discretas, curtas, pouco contorno | Falas completas, **bold branca com contorno preto**, até duas linhas. |
| Destaques | Vermelho pontual | Vermelho **inline** em nomes e objetivos reais, sem pílula. |
| Duração | Dependente da narrativa | Referência com ~65 s; nenhum teto artificial de 30–40 s. |
| Marca d'água | Não é exigida pelo guia geral | **Desligada** por padrão para reproduzir o Reel. |
| Trilha e efeitos | Apenas quando ajudarem | **Nenhuma música ou SFX extra** neste perfil. |

**Invariantes dos dois guias:** preservar fatos reais, timing das reações, qualidade técnica, contexto narrativo e gameplay legível. Não criar momentos falsos. A edição não deve chamar mais atenção do que o conteúdo.

### Opções para personalização futura (DESLIGADAS no padrão fiel)

- `watermark_enabled = false` → se **ativado explicitamente**, usar @tiojoaoyt com transparência e posição que não cubra jogo nem legenda.
- `duration_target_seconds = null` → se o criador pedir vídeos de 30–40 s, tratar como preferência editorial, não como corte compulsório que destrói a história.
- `external_music_enabled = false` e `external_sfx_enabled = false`.
- `word_by_word_captions = false`, `red_pill_style = false`.

## 7. Configuração funcional sugerida para os scripts

É uma **especificação de comportamento**, não uma afirmação sobre as APIs do projeto atual. Antes de implementar, Claude deve ler os arquivos reais, preservar o fluxo existente e mapear parâmetros aos nomes já utilizados.

```yaml
profile: tiojoaoyt_reel_continuo_v2
output:
  folder: shorts
  format: mp4
  width: 1080
  height: 1920
  fps: preserve_source_up_to_60
  duration_target_seconds: null
  max_clips_per_vod: null
layout:
  default_state: SPLIT_BASE
  camera_position: top
  camera_height_ratio: 0.28
  gameplay_position: bottom
  gameplay_height_ratio: 0.72
  divider: straight
  border: none
  facecam_crop: preserve_aspect_ratio_and_face
  prioritize_facecam_source_quality: true
  change_states_only_for_story_beats: true
  fullscreen_gameplay_on_key_action: true
  facecam_closeup_on_genuine_reaction: true
captions:
  burned_in: true
  include_streamer: true
  include_game_dialogue: true
  segmentation: phrase
  max_dialogue_lines: 2
  font_style: sans_bold
  color: '#FFFFFF'
  outline_color: '#000000'
  align: bottom_center_safe_area
  inline_highlight_color: '#DC2626'
  highlight_only_verified_entities: true
  optional_mission_objective_smaller_line: true
  word_by_word: false
  red_pills: false
audio:
  original_game_audio: true
  original_streamer_voice: true
  preserve_laughter_and_comedic_pauses: true
  add_external_music: false
  add_external_sfx: false
editing:
  preserve_original_chronology: true
  prefer_single_continuous_event: true
  opening_title: false
  forced_zoom_interval: null
  forced_cut_interval: null
  fade_in_by_default: false
  allow_natural_cliffhanger: true
  end_card: false
  watermark: false
quality:
  avoid_facecam_upscale_damage: true
  preserve_gameplay_readability: true
  subtitles_must_match_actual_speech: true
  check_audio_video_sync: true
```

## 8. Processo obrigatório do Claude

1. **Inspecionar as fontes:** vídeo do VOD, webcam separada (se houver), áudio, scripts existentes e `ESTILO.md`. Registrar problemas de resolução e se diálogos de jogo podem ser capturados com precisão.
2. **Encontrar histórias completas:** selecionar todos os momentos fortes independentes; registrar tempo inicial/final, pico de ação e reação real.
3. **Montar continuidade primeiro:** escolher o trecho e manter setup, escalada, payoff ou cliffhanger real, sem efeitos nem títulos.
4. **Definir estados do layout:** `SPLIT_BASE` como padrão; `GAMEPLAY_FOCUS` no ponto de ação que pede tela cheia; `FACECAM_REACTION` somente quando merecido.
5. **Transcrever falas de jogo e streamer:** transcrever e sincronizar todos os diálogos inteligíveis, com nomes corretos. Se áudio estiver duvidoso, **não inventar** a transcrição; sinalizar para revisão.
6. **Renderizar legendas completas:** texto branco bold com contorno preto, destaques inline verificados e objetivo menor quando houver evidência.
7. **Preservar áudio original:** nivelamento cuidadoso sem adicionar trilha ou efeitos novos.
8. **Exportar múltiplos cortes:** todos os aprovados para `shorts/`, com nomes únicos e uma pequena descrição por arquivo. Não limitar a três.
9. **Verificar cada Short:** começo, momentos de gameplay em tela cheia, zoom facial se existir, legibilidade de legendas, nitidez da webcam, sincronização, fim e ausência de elementos extras.
10. **Documentar exceções:** quando a origem não permitir reproduzir a câmera em 28% com qualidade, ou quando a fala do jogo não puder ser distinguida, explicar e adotar a solução menos destrutiva.

### Checklist de aprovação

- [ ] A gravação mostra um evento real e compreensível; sem colagem de acontecimentos desconectados.
- [ ] Webcam normalmente em cima (~28%) e gameplay embaixo (~72%), sem moldura.
- [ ] Gameplay em tela cheia **somente** nos picos em que melhora a compreensão.
- [ ] Close de webcam **somente** para uma reação real que justifique o destaque.
- [ ] Todas as falas inteligíveis do jogo e do streamer estão legendadas corretamente.
- [ ] Legendas brancas bold com contorno preto, centralizadas no rodapé, até duas linhas de fala.
- [ ] Nomes e objetivos pertinentes destacados em vermelho **dentro** da frase; objetivo menor só quando real.
- [ ] Só áudio original do jogo e streamer; risada preservada, sem música/SFX extras.
- [ ] Começo direto na ação; sem título de abertura.
- [ ] Final orgânico, inclusive cliffhanger; sem end card ou marca d'água.
- [ ] Webcam e gameplay não ficaram borradas ou esticadas; proporções preservadas.
- [ ] Saída em `shorts/`; todos os bons momentos selecionados, sem teto de três clipes.

## 9. Comando direto para o Claude

> **Analise meu projeto de geração de cortes gamers e implemente o perfil `tiojoaoyt_reel_continuo_v2` deste arquivo, mantendo `ESTILO.md` como identidade editorial geral. Use o padrão fiel descrito pelo criador: split vertical com webcam superior ~28% e gameplay inferior ~72%, sem molduras; gameplay em tela cheia nos picos da ação; close da facecam só numa reação genuína; legendas queimadas em todas as falas do jogo e do streamer, brancas bold com contorno preto e até duas linhas, nomes/objetivos em vermelho inline; apenas áudio original, sem música nem efeitos adicionais; narrativa contínua, começo direto na ação, final orgânico sem marca d'água nem tela final. Encontre quantos momentos fortes a live oferecer, sem limitar a três, e exporte para `shorts/`. Preserve o FPS e a nitidez original da webcam e verifique cada saída. Inspecione meus scripts antes de editar, não quebre recursos existentes, explique alterações e liste qualquer limitação da origem. Não invente conteúdo que não esteja gravado.**

---

**Decisão editorial desta revisão:** priorizar a **reprodução fiel do Reel como descrito**, não mesclar automaticamente com uma versão de 30–40 s nem com marca d'água. Esses recursos ficam opcionais e desativados até serem solicitados. 

# TIOJOAOYT | EDITOR INTELIGENTE DE GAMEPLAY LONGA — V4 (2026-11-26)

> **Documento único dos vídeos longos.** Substitui `ESTILO - video longo - Claude Code v2.md` (v3) e o antigo `ESTILO - video longo.md` (v1), que ficam em `Estilo/antigos/` só como histórico.
> Números de regras (limites de tempo morto, pausas, crossfades, faixa de duração) ficam em `Scripts/config/` e **não** são repetidos aqui. Shorts e cortes verticais têm guia próprio: `ESTILO_CORTES_DE_LIVE.md`.
> Princípio central: **a história, a gameplay e a personalidade do João vêm antes de efeitos ou de métricas artificiais de retenção.**

## 1. Prioridades e regras inegociáveis

**Ordem de decisão em conflitos:** qualidade narrativa > momentos importantes preservados > fluidez > dinamismo > quantidade de episódios > duração exata. A fidelidade aos acontecimentos é pré-requisito de tudo, e a qualidade audiovisual nunca pode piorar.

1. Episódios de **~50 a 60 min**. Até ~62 min só para não partir uma sequência. Lives longas viram uma **série** cronológica: nunca seis arquivos de uma hora "cortados no relógio".
2. **Nunca cortar fala do João nem diálogo do jogo**, principalmente no fim do episódio. Ver a seção 4.
3. Nenhum corte seco perceptível entre trechos descontínuos.
4. Não sacrificar cena essencial pela duração, e não encher episódio para chegar a 50 min. A última parte pode ser curta.
5. Edição **clean e dinâmica**: tirar o vazio, não picotar a história. Ver a seção 5.
6. Nada de trecho travado (live ou render) no vídeo entregue.
7. Não inventar fatos, falas, reações, timestamps nem recursos técnicos.
8. Nunca postar nem agendar sem ordem explícita do João.
9. Nunca apagar os originais nem a pasta `Scripts/`.

## 2. Identidade e tom por tipo de cena

Canal TiojoaoYT: gameplays narrativas, ação, terror, desafios, exploração e reações espontâneas. O tom é natural e próximo, com humor orgânico. Os protagonistas são o jogo, o que acontece nele e a reação autêntica do João. **Não substituir a interpretação do criador pela do editor.**

O **perfil editorial** de cada live fica no plano (`"perfil": [...]`, com os valores em `Scripts/config/perfis.json`). Dá para combinar perfis, e vale sempre o limite mais protetor.

| Perfil | Prioriza | Condensa |
|---|---|---|
| `narrativo` | história, diálogos, personagens, cutscenes inteiras, emoção | só o repetitivo |
| `mundo_aberto` | descobertas, encontros, imprevistos, contexto geográfico e de missão | deslocamento vazio (sem eliminar a viagem: ver sair e chegar) |
| `soulslike_acao` | dificuldade, erros que importam, evolução da estratégia, vitória e reação depois | tentativas iguais |
| `terror` | suspense, silêncio, preparação do susto; sem efeitos que quebrem a tensão | pouco: o silêncio é conteúdo |
| `competitivo` | decisões, jogadas, erros, comunicação relevante | esperas, lobbies, intervalos |

## 3. Classificação dos segmentos

Cada trecho do plano recebe uma decisão:

- **PRESERVAR INTEGRALMENTE**: entendimento da história, diálogos, reviravoltas, chefes (primeira aparição e vitória), clímax, silêncio emocional.
- **MANTER**: exploração com contexto, preparação, tentativas diferentes, interação que mostra a personalidade do João.
- **CONDENSAR**: o mesmo conteúdo, mais curto, mostrando "como chegamos de A a B". `ENCURTAR` vale como sinônimo antigo.
- **REMOVER**: espera, AFK, ajuste técnico, repetição sem novidade, papo administrativo ou pessoal, outra pessoa jogando.
- **REVISAR**: baixa confiança ou possível importância. **Bloqueia o render** até a segunda análise (quadros densos e fala) decidir.

Nenhum detector decide sozinho e nenhuma pontuação elimina cena. Silêncio não é tempo morto. Toda remoção relevante vai para `removidos_relevantes` com o motivo. Remover reação, cutscene ou pico de intensidade sem motivo vira aviso **REVISAR** no validador.

**Memória narrativa** (`narrativa.json`): registra a história, os objetivos, os personagens e os eventos com `depende_de`. Evento de importância 3 não pode sair. Evento mantido não pode perder o contexto do qual depende, nem que esteja horas antes. Cada evento precisa de evidência copiada da transcrição, e o script confere (anti-invenção).

## 4. Proteção absoluta de diálogos

Valem as falas do João, de personagens, diálogos em outra língua, conversa encadeada, cutscenes e a reação logo depois de um diálogo.

- Bordas sempre por `Scripts/bordas.py` (`Bordas.inicio` / `Bordas.fim`), que combina as frases da transcrição com a **energia de voz do áudio**. A energia pega a fala do jogo que o Whisper não transcreve.
- **Conversa encadeada** (próxima frase em menos de 0,7 s) é uma fala só. **Pausa curta entre palavras não é pausa**: o corte exige uma pausa real.
- **Fim de episódio**: a cena e a conversa terminam, com pausa de 1,5 s, mesmo que o episódio fique mais longo. Na dúvida, estender.
- Cutscene sem barra preta e legendas do jogo: conferir nos quadros densos (`analisar_live.py --quadros`).
- O validador bloqueia borda em cima de fala. O QC acusa "FALA CORTADA" nas emendas (aviso) e no fim (problema). O revisor confere de novo o fim do episódio (cutscene, reação ou fala logo depois).

## 5. Clean, natural e dinâmico

- Tirar o tempo morto sem destruir a ambientação. Os limites por perfil ficam em `perfis.json`: `tempo_morto_max_s`, `menu_max_s`.
- Menus, mapa e inventário: curtos, salvo se houver conversa ou história ali.
- Repetições: fica só a melhor versão. O revisor compara as falas dos trechos mantidos.
- Papo administrativo da live (PSN, qualidade da live, agenda, sub, thumb) sai, a não ser que seja engraçado.
- Preservar a preparação e a consequência das piadas, a evolução das lutas e as reações inteiras. Não virar montagem de highlights.
- Efeitos, zooms (teto 1,15), textos, replays curtos e efeitos sonoros só entram com função clara. No perfil `terror`, praticamente nenhum.

## 6. Emendas e transições

`Scripts/transicoes.py` escolhe a emenda de cada junção pelo contexto e registra o motivo no plano:

- **corte** (padrão): imagem corta com crossfade curto de áudio. O crossfade é adaptativo ao degrau de som de fundo. É a escolha quando a cena é parecida ou quando um lado é carregamento ou tela escura (transição do próprio jogo).
- **dissolve**: só para elipse real (troca de ambiente com salto de mais de 8 min). Nunca dois seguidos, e há um teto por episódio.
- **L-cut / J-cut** (`audio_desloc`): o som atravessa o corte para uma frase terminar, ou entra antes da imagem para uma fala começar. **Nunca sobrepor falas.**
- Para escolher na mão, usar `"transicao_forcada": true` no trecho.
- Emenda difícil: gerar a prévia leve (`montar_episodios.py --previa-emendas`). Se não convencer, procurar outro ponto de corte.
- O revisor acusa **possível jump cut** (mesma cena com salto curto).

## 7. Episódios, títulos e entrega

- **Estrutura de cada parte:** começo com ação ou gancho real (sem spoiler), contexto, desenvolvimento, clímax e fechamento natural. Sem recapitulação longa. Continuidade entre as partes, sem buraco nem repetição.
- **Título no vídeo (cartão):** `FRASE FORTE REAL!`, e `| Parte N` no título interno. Sempre gerar também um alternativo.
- **Título no YouTube:** `GTA 6 #N - | FRASE | Grand Theft Auto VI | Português PT-BR | PS5 Pro`, com no máximo 100 caracteres. O N segue a ordem das lives no canal. Para outro jogo, trocar o nome e perguntar o console.
- **Thumbnail:** não gerar imagem (o João dispensou).
- **Arquivos:** `videos_longos/<Jogo>/GTA VI - VOD (DD-MM-AAAA) PARTE - N.mp4`, junto com `... - relatorio.md` e `... - titulos e descricao.md`.
- **Descrição fixa:**

```
PARA A COMPANHAR NOSSOS CONTEÚDOS AO VIVO SIGA NOSSAS LIVES.

💜LIVE:  /tiojoaoyt
🖤Tiktok: @tiojoaooficial  
📷Instagram: @tiojoaoyt

#tiojoãoyt 💜
```

- **Tela final:** GTA 6 usa `Estilo/encerramento_gta6.png` por 10 s. Para outro jogo, usar `Estilo/encerramento_<jogo>.png`; se não existir, perguntar ao João. Nunca usar o card vertical de Shorts em vídeo longo. O último trecho termina na despedida, antes da vinheta de fim de stream.
- **Registro:** depois de cada entrega, acrescentar a live a `Scripts/links_processados.json`. Antes de qualquer link novo, rodar `python Scripts/checar_link.py <link>`; se der "JÁ PROCESSADO", avisar o João e não refazer.

## 8. Imagem, áudio e casos especiais

- **Imagem:** resolução e **FPS exatos da fonte** (o render usa o FPS racional; 59,94 continua 59,94). Uma única codificação (h264_amf CQP 18/20/22). Nunca renderizar a partir do proxy. Sem sharpening nem interpolação.
- **Facecam:** **não presumir a posição.** Já houve `[1400,126,506,284]` e `[26,111,454,257]`. Rodar `analisar_live.py --facecam auto` e conferir o `facecam.jpg`.
- **Áudio:** voz, diálogo e música do jogo em primeiro plano. Crossfade em toda emenda. Normalizar a -14 LUFS. Nunca piorar o áudio para "dinamizar".
- **Mudo da Twitch** (blocos de 180 s sem som): detectar com `silencedetect` antes do plano e pular com dissolve.
- **Blur de nudez:** só nudez de fato (seios à mostra, genitais, personagem pelado, como no lap dance com o sutiã tirado). Biquíni, lingerie e "quase nu" **não** levam blur. Marcar em `"censura"` no tempo da fonte. A facecam continua nítida.
- **Outra pessoa jogando** (irmão menor): o trecho sai inteiro e vira elipse.

## 9. Pipeline V4 (rodar da raiz do projeto)

| # | Etapa | Comando |
|---|---|---|
| 0 | Ambiente e link | `python Scripts/checar_ambiente.py` e `python Scripts/checar_link.py <link>` |
| 1 | Baixar (fonte 1080p60 + áudio + proxy 160p) | `yt-dlp` do `whisper-env` → `Bruto/` e `Trabalho/longo_<jogo>_<vod>/` |
| 2 | Transcrever | `python Scripts/transcrever_longo.py <audio> <cache> Trabalho --nome ...` (blocos com checkpoint) |
| 3 | Analisar (multimodal) | `python Scripts/analisar_live.py <proxy_160p> <cache> --facecam auto --fonte-wh 1920x1080 --transcricao <T.json> --quadros Bruto/<fonte>` → `analise.json`, `resumo_ia.txt`, `facecam.jpg`, `quadros/` |
| 4 | Memória editorial | `python Scripts/registrar_feedback.py resumo` (ler antes de decidir) |
| 5 | Narrativa | `python Scripts/memoria_narrativa.py iniciar ...`; a IA preenche lendo o `resumo_ia.txt` (barato) e só depois abre a transcrição e os quadros nos trechos marcados; `... checar ...` |
| 6 | Plano | gerador em `Scripts/planos/plano_<serie>_gerar.py` (modelo: `plano_gta_2938905930_gerar.py`, com bordas V4). Status `aguardando_aprovacao`; mostrar ao João |
| 7 | Transições | `python Scripts/transicoes.py Trabalho/plano_x.json` |
| 8 | Validar | `python Scripts/validar_plano.py Trabalho/plano_x.json` (precisa dar 0 erros; grava o hash) |
| 9 | Prévias (opcional) | `python Scripts/montar_episodios.py --plano ... --previa-emendas` |
| 10 | Render + QC + revisão | `python Scripts/renderizar_serie.py --plano Trabalho/plano_x.json` (3 partes em paralelo, QC de cada uma, revisor no fim → `revisao.md`) |
| 11 | Corrigir | ajustar o plano e rodar de novo; só os pedaços alterados são recodificados |
| 12 | Entregar | `relatorio_longo.py`, títulos e descrição, `links_processados.json`, e registrar o feedback do João |

**Aprovação:** o plano só renderiza com o "Aprovado" do João e com a validação em dia. **Testes:** `python -m unittest Scripts/testes/test_v4.py -v` depois de mexer em qualquer script. **Benchmark:** `python Scripts/benchmark.py <video>` antes de mudar alguma configuração técnica.

## 10. Controle de qualidade (o que é automático e o que não é)

| Checagem | Onde |
|---|---|
| Sincronia A/V, resolução, FPS, decodificação completa, pretos, silêncios, degrau de volume | `verificar_episodio.py` |
| Travamento (jogo e facecam parados juntos), fala cortada nas emendas e no fim | `verificar_episodio.py` |
| Borda em cima de fala, REVISAR pendente, contexto narrativo, cutscene ou reação removida, ritmo por perfil, travamento da live mantido, dissolves | `validar_plano.py` |
| Fim abrupto, começo fraco, jump cut, ritmo arrastado, repetição, momento forte removido, contexto ausente, buraco entre as partes, excesso de efeitos | `revisor_editorial.py` |
| Blur de nudez, títulos, spoiler, humor e personalidade | **manual** (olhar os quadros e ler) |

Uma parte só está aprovada com o QC sem PROBLEMAS **e** o revisor dizendo APROVADO. Arquivo renderizado não é sinônimo de vídeo aprovado.

## 11. Memória editorial e aprendizado

Todo feedback do João vai para `Scripts/memoria_editorial.json` (`registrar_feedback.py add`). Etiqueta repetida avisa RECORRENTE: vira regra verificável em script **e** teste em `Scripts/testes/`, com confirmação do João. Regras fundamentais nunca mudam por interpretação da IA a partir de um único comentário.

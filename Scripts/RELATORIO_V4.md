# Sistema de edição V4: relatório de implementação (2026-11-26)

O pedido "Evolução do sistema de edição inteligente V4" foi executado no próprio projeto, sem recomeçar do zero. Estava tudo em `git` antes das mudanças (commit `d9306f9`).

Material de teste disponível:
- **real:** `Final/Coletor de Marionetes_longo.mp4` (Phantom Blade Zero, 70 min, 1080p60, com facecam). Um trecho de 10 min foi transcrito para os testes;
- **sintético:** gerado pelos próprios testes, com falas reais da voz do Windows.

`Bruto/` está vazio (as lives já foram apagadas). Por isso, nada foi testado numa live inteira de 4 a 9 h (ver "Pendente de validação").

---

## 1. Problemas encontrados na auditoria

| # | Problema | Onde | Gravidade |
|---|---|---|---|
| 1 | Fim de episódio e bordas no meio de fala. O `snap()` só tirava a borda de dentro de **uma palavra**, não da frase nem da conversa. Era a causa provável das falas cortadas no fim dos episódios postados. Na comparação real, o método antigo cortou fala em **7 bordas** de 11. | gerador de plano v3 | crítica |
| 2 | Diálogo do jogo fora da transcrição (inglês, música por cima) era invisível para o sistema. | todo o pipeline | crítica |
| 3 | O render arredondava o FPS (`round(59,94)` = 60). Em fonte de 59,94, isso duplica 1 quadro a cada ~17 s, uma micro-travada no vídeo final. | `montar_episodios.py` | alta |
| 4 | O detector de travamento (24/11) olhava o quadro inteiro. A facecam ocupa ~6% da tela, então menu parado com o João mexendo virava "travamento", e a webcam de 30 fps dentro de 60 fps repete quadros. **Medido num vídeo real:** dezenas de falsos positivos. | `verificar_episodio.py` | alta |
| 5 | Regras do guia sem execução em script: J/L-cut (seção 5), prévia das emendas (18.2), análise visual além da transcrição (seção 3), continuidade entre partes (18.1), edição clean/dinâmica (20B), checklist de QC (17). | guia × scripts | alta |
| 6 | Conflitos entre documentos: | `Estilo/` | média |
|   | • `ESTILO - video longo.md` (v1: live de 1–2 h → 1 vídeo) contradizia a v3 (série); | | |
|   | • dentro da v3, a seção 16 usava outro nome de arquivo (`<Jogo> - Parte 01.mp4`) e outra pasta de plano que a seção 19; | | |
|   | • a facecam `[1400,126,506,284]` estava fixa no texto, mas a live de 24/11 tinha `[26,111,454,257]`; | | |
|   | • o texto citava `frases_entre.py`, que não existe mais; | | |
|   | • a descrição fixa tinha 3 linhas em branco num lugar e 1 em outro. | | |
| 7 | Nada impedia renderizar um plano com borda ruim: o `checar_bordas.py` era opcional. | fluxo | média |
| 8 | O render usa ~3 dos 16 núcleos, e as partes saíam uma de cada vez. | fluxo | média (velocidade) |
| 9 | Uma checagem de QC que falha podia passar como aprovada. O teste novo pegou isso: o ffmpeg falhava em silêncio. | `verificar_episodio.py` (V4) | alta, corrigida |
| 10 | Tokens: a IA lia a transcrição inteira (JSON ~25 mil tokens a cada 10 min) e painéis fixos de 30 s. | fluxo | média |
| 11 | `montar_longo.py` e `thumb_base.py` são redundantes ou sem uso (mantidos; só para planos antigos ou se pedido). O guia dos Shorts cita `Trabalho/montar_cortes.py`, que **não existe mais** (sumiu na limpeza de 23/11). | — | baixa (fora do escopo dos vídeos longos) |

## 2. Arquitetura V4 (módulos)

| Módulo | Arquivo(s) | Função |
|---|---|---|
| Base comum | `comum.py`, `config/projeto.json`, `config/perfis.json` | caminhos, limiares e perfis num lugar só, gravação atômica (checkpoint seguro) |
| Ambiente | `checar_ambiente.py` | valida ffmpeg, h264_amf, filtros, Python, whisper, fontes, espaço — antes de começar |
| 1. Analista audiovisual | `analisar_live.py` | grade 96×54 a 2 amostras/s, diferença calculada pelo ffmpeg, áudio por segundo. Blocos de 30 min com checkpoint, 3 em paralelo. Detecta facecam automaticamente, cortes de cena, letterbox (cutscene), menu/tela parada, travamento da live, reações (câmera e voz), tempo morto. Gera `resumo_ia.txt` compacto e painéis adaptativos |
| 2. Diretor narrativo | `memoria_narrativa.py` | `narrativa.json` com eventos, importância e `depende_de`. A evidência é conferida na transcrição (anti-invenção) |
| 3. Editor | `bordas.py`, `transicoes.py`, `validar_plano.py`, gerador modelo em `planos/` | bordas por frase, conversa e voz do áudio. Transição por contexto (corte, dissolve, J/L). Validador que **bloqueia** o render (REVISAR, fala na borda, contexto ausente, cutscene removida, travamento mantido) e avisa sobre ritmo por perfil |
| 4. Motor de render | `montar_episodios.py` (V4), `renderizar_serie.py` | FPS exato, J/L no áudio, prévia de emendas, portão de validação. Série em paralelo (3), retomada por pedaço |
| 5. Revisor independente | `verificar_episodio.py` (técnico), `revisor_editorial.py` (editorial) | local, causa e correção. Veredito APROVADO / REPROVADO / PENDENTE |
| 6. Memória editorial | `memoria_editorial.json`, `registrar_feedback.py` | 16 aprendizados reais já registrados. Feedback recorrente vira regra e teste |
| Testes e medição | `testes/test_v4.py`, `benchmark.py`, `comparar_metodos.py`, `legado/` | 18 testes de regressão, benchmark, comparação A/B do método antigo com o V4 |
| Documentação | `Estilo/ESTILO - video longo V4.md`, skill `.claude/skills/video-longo` | um guia só (os antigos em `Estilo/antigos/`), roteiro curto para gastar menos tokens |

## 3. Arquivos

**Novos:**
- `Scripts/`: `comum.py`, `checar_ambiente.py`, `analisar_live.py`, `memoria_narrativa.py`, `transicoes.py`, `validar_plano.py`, `revisor_editorial.py`, `registrar_feedback.py`, `renderizar_serie.py`, `benchmark.py`, `comparar_metodos.py`, `memoria_editorial.json`, `config/projeto.json`, `config/perfis.json`, `testes/test_v4.py`, `legado/montar_episodios_v3.py`, `benchmarks/benchmark_2026-11-26.json`, `RELATORIO_V4.md`;
- `Estilo/ESTILO - video longo V4.md`;
- `.claude/skills/video-longo/SKILL.md`.

**Modificados:**
- `Scripts/montar_episodios.py`: FPS exato, J/L, prévias, portão de validação, facecam no `juncoes.json`;
- `Scripts/verificar_episodio.py`: travamento jogo + facecam com tolerâncias medidas, fala cortada respeitando J/L, falha alta se a checagem não rodar;
- `Scripts/bordas.py`: fronteiras de frase, frases coladas, pausa real, fundo de 30 s, iteração transcrição ↔ áudio;
- `Scripts/planos/plano_gta_2938905930_gerar.py`: chaves V4 e `transicao_forcada`;
- `README.md`.

**Arquivados (não apagados):** `Estilo/antigos/ESTILO - video longo (v1).md` e `ESTILO - video longo - Claude Code v2 (v3, ate 2026-11-24).md`.

## 4. Antes × depois

| Aspecto | Antes (v3) | V4 |
|---|---|---|
| Borda de corte | fora de 1 palavra | fora da frase e da conversa encadeada, pausa real, voz do áudio (diálogo do jogo), fim do episódio com pausa de 1,5 s |
| Entendimento da live | transcrição + painel fixo de 30 s | + sinais por segundo (movimento do jogo/câmera, letterbox, menus, reações, travamentos, tempo morto), resumo compacto, painéis adaptativos, memória narrativa |
| Decisões | MANTER / ENCURTAR | PRESERVAR / MANTER / CONDENSAR / REMOVER / **REVISAR** (bloqueia) e perfis por jogo combináveis |
| Transição | `corte` ou `dissolve` marcado à mão | escolhida por contexto, com motivo; J/L-cut; dissolve só para elipse, nunca em série |
| Antes do render | `checar_bordas` opcional | `validar_plano` **obrigatório** (o hash da montagem libera o render) e prévias leves das emendas |
| Render | 1 parte por vez; FPS arredondado | 3 partes em paralelo; FPS exato; retomada por pedaço |
| Revisão | QC técnico | QC técnico mais preciso e revisor editorial independente com veredito |
| Aprendizado | memória do Claude | `memoria_editorial.json`; recorrente vira regra e teste |
| Testes | nenhum automatizado | 18 testes de regressão, benchmark, comparação A/B |
| Documentação | 4 guias com conflitos | 1 guia V4, configuração central e skill curta |

## 5. Resultados reais dos testes

**Testes automatizados** (`python -m unittest Scripts/testes/test_v4.py`): **18/18 passando**, em ~20 s. Cobrem:
- bordas: conversa encadeada, fala do jogo fora da transcrição, ponto limpo, fim de episódio;
- validador: REVISAR, borda ruim, contexto ausente;
- memória narrativa: recusa evidência inventada;
- perfis;
- L-cut: escolhido e mantendo a fala inteira no render;
- render: FPS 59,94 exato, sincronia, portão de validação, prévias;
- QC: travamento real, pessoa parada em webcam de 30 fps não é travamento, fala cortada no fim;
- análise: facecam, cortes, travamento de 1 s da live;
- revisor.

Os testes também pegaram 3 bugs meus durante a implementação (falha silenciosa do QC, amostras insuficientes de facecam, borda parando entre palavras de uma fala) antes de chegar a uma live.

**Comparação A/B num vídeo real** (`benchmarks/comparacao_coletor10_2026-11-26.md`). Trecho de 10 min de Phantom Blade Zero, 6 trechos marcados à mão como um editor faria, com bordas brutas:

| | método v3 | V4 |
|---|---|---|
| Bordas cortando fala (de 11) | **7** (inclusive o fim do episódio e uma fala sem transcrição) | **2**, as duas acusadas e bloqueadas pelo validador (fala que continua além do fim do clipe de teste e papo corrido) |
| Travamentos da live dentro do vídeo | não detectados antes do render | **5 acusados antes do render** (8:28–8:57), confirmados quadro a quadro na fonte |
| Revisor: problemas | 12 | 8 (os restantes: os travamentos da live que ficaram de propósito no teste) |

**Ciclo completo com correção** (`benchmarks/demo_ciclo_v4_revisao_2026-11-26.md`). O "editor" respondeu ao validador (tirou o trecho travado e terminou na pausa natural), e o ciclo rodou: transições → validação com **0 erros** → render + QC **sem problemas** (7,3 min, 59,94 → 60/1 exato, A/V com diferença de 0,009 s) → **revisor: APROVADO**, com 2 avisos para conferir ouvindo.

**Detecção de travamento, conferida na fonte:** o clipe real tem 5 trechos de quadros idênticos (8:28–8:57).
- Analisador (antes do plano): **5 de 5**, sem nenhum falso positivo em 10 min.
- QC (no FPS nativo): todos.
- O detector antigo do quadro inteiro gerava **dezenas** de falsos positivos nesse vídeo; o V4 gera zero.

**Facecam automática:** acertou a câmera do Phantom Blade (`[40,120,440,240]`, conferido na imagem) e a do teste sintético (sobreposição > 0,5).

## 6. Desempenho medido (`benchmarks/benchmark_2026-11-26.json`)

| Medida | Resultado | Decisão |
|---|---|---|
| Decodificar 60 s de 1080p60 | CPU 5,3 s (31,9 s de CPU) · d3d11va 8,3 s · amf 4,2 s (1,8 s de CPU) | — |
| Render de 60 s (cadeia real) | CPU 17,4 s · com d3d11va 16,8 s (1,04×, SSIM 1,000) · amf não funciona com os filtros | **mantida a decodificação na CPU** (ganho < 10%) |
| Render em paralelo | 1 por vez: 22,7 s por min de vídeo · 2: 15,2 s · **3: 11,7 s** | **3 em paralelo (1,94×)**: série de 4 partes de ~55 min ≈ 83 → 43 min de render |
| Qualidade do render | SSIM fonte × render = 0,993 (CQP 18/20/22, uma única codificação) | mantido |
| Análise multimodal | HD 4,6× tempo real · **proxy 160p 13,7×** | rodar no proxy: live de 4 h ≈ 18 min |
| Tokens para entender 10 min | transcrição JSON ~24,8 mil · texto ~1,7 mil · **resumo_ia ~480** | ler primeiro o resumo (3,6× menos que o texto, ~50× menos que o JSON) e abrir a transcrição só nos trechos marcados |
| Custo extra da V4 | plano +10–15 s (medições de áudio) · QC +~50% em trechos curtos (passada da facecam) | aceitável |

Memória: maior pico medido de 387 MB por processo de render. GPU: o encoder AMF aguentou 3 sessões simultâneas.

## 7. Limitações e pendências

**Pendente de validação** (sem material disponível):
- live inteira de 4 a 9 h (checkpoints e paralelismo testados em blocos de 30 min e em 1 parte);
- detecção de cutscene por letterbox (o jogo de teste não usa barras);
- blur de nudez no V4 (lógica antiga, inalterada).

**Limitações conhecidas:**
- **Cutscene sem barra preta e menu animado** (ex.: a tela de título do Phantom Blade) não são reconhecidos automaticamente. Por isso as regiões duvidosas ganham quadros densos para a IA olhar, e o guia manda conferir.
- **Legenda do jogo** não é lida (não há OCR instalado). A proteção de diálogo do jogo usa a energia de voz do áudio.
- **"Humor, tensão, surpresa"** são aproximados por sinais (pico de voz + movimento da câmera = reação; intensidade). Quem interpreta é a IA lendo o resumo e a transcrição; nenhum detector decide sozinho.
- **Voz que o Whisper não transcreve** (canto, fala do jogo): quando não há pausa real por perto, a borda é **acusada** (o validador bloqueia) em vez de corrigida sozinha. Um humano decide.
- **Transcrição:** continua na CPU (faster-whisper turbo int8, 3 blocos em paralelo). O CTranslate2 não tem aceleração para GPU AMD no Windows.
- **Revisor:** jump cut e repetição são heurísticas, por isso saem como **aviso** para conferir, não como reprovação.
- **Guia dos Shorts:** cita `Trabalho/montar_cortes.py`, que não existe mais. Recriar quando o João voltar a pedir Shorts.

## 8. Como usar

Roteiro completo na seção 9 do `Estilo/ESTILO - video longo V4.md` (ou na skill `video-longo`). Resumo:

```text
python Scripts/checar_link.py <link>          # já processado? avisa
python Scripts/checar_ambiente.py
python Scripts/registrar_feedback.py resumo
(baixar → Bruto/ + Trabalho/longo_x/)  ·  python Scripts/transcrever_longo.py ...
python Scripts/analisar_live.py <proxy> <cache> --facecam auto --fonte-wh 1920x1080 --transcricao T --quadros <fonte>
python Scripts/memoria_narrativa.py iniciar|checar ...
(gerador do plano em Scripts/planos/ → mostrar ao João → "Aprovado")
python Scripts/transicoes.py Trabalho/plano_x.json
python Scripts/validar_plano.py Trabalho/plano_x.json
python Scripts/renderizar_serie.py --plano Trabalho/plano_x.json
python -m unittest Scripts/testes/test_v4.py   # depois de mexer em qualquer script
python Scripts/comparar_metodos.py ...         # antes de aplicar uma mudança de método numa live longa
```

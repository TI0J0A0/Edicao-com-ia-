"""Gera Trabalho/plano_gta_2940902491.json — live de GTA 6 (Twitch 2940902491, 26/11/2026, 4h09, 2560x1440 60 fps
— fonte ORIGINAL da pasta chunked/, ver Trabalho/longo_gta_2940902491/fontes.md). Primeira série feita no sistema V4.

Cada episódio = trechos MANTIDOS (capítulo, início, fim, decisão, motivo). Trechos colados formam capítulos.
Bordas por Scripts/bordas.py (frases + voz do áudio; fim de episódio com pausa de 1,5 s).
Travamentos REAIS da live (medidos na fonte: jogo + facecam parados juntos, 69 trechos / 102 s) viram micro-cortes
automáticos; a borda colada no travamento é marcada "corte_travamento" (o validador avisa em vez de bloquear).
"""
import json
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(RAIZ)
sys.path.insert(0, os.path.join(RAIZ, "Scripts"))
from bordas import Bordas  # noqa: E402
import ritmo  # noqa: E402

VOD = "2940902491"
TR = f"Trabalho/GTA live {VOD}_transcricao.json"
CACHE = f"Trabalho/longo_gta_{VOD}"
AUDIO = f"{CACHE}/audio_{VOD}.mp4"
TRAV = f"{CACHE}/travamentos_fonte.json"
JOGO = "GTA 6"
DATA_VOD = "26-11-2026"
NUM_YT_INICIAL = 24       # 19/11 #4–#10, 20/11 #11–#16, 22/11 #17–#19, 24/11 #20–#23
STATUS = "aprovado"   # João: "Aprovado" em 2026-11-26
d = json.load(open(TR, encoding="utf-8"))
DUR = d["duracao"]
B = Bordas(TR, AUDIO)
PERFIL = ["mundo_aberto", "narrativo"]
# Ritmo V4.1 (João 2026-11-26, referência Funky): corta silêncio real de mapa/menu/carregamento e abre o episódio
# direto no jogo. RITMO=0 reproduz o plano entregue; PLANO_TESTE=1 grava num plano de teste (vídeos em Trabalho/).
USAR_RITMO = os.environ.get("RITMO", "1") == "1"
TESTE = os.environ.get("PLANO_TESTE") == "1"
R = ritmo.Ritmo(AUDIO, TR, analise=f"{CACHE}/analise/analise.json", cache=CACHE, perfil=PERFIL) if USAR_RITMO else None


def t(s):
    p = [float(x) for x in str(s).split(":")]
    return p[0] * 3600 + p[1] * 60 + p[2] if len(p) == 3 else (p[0] * 60 + p[1] if len(p) == 2 else p[0])


# travamentos da fonte, agrupados (vãos < 2,5 s viram um bloco só: nada de pedacinho de 1 s entre travadas)
TRAVS = []
for a, b in sorted(json.load(open(TRAV, encoding="utf-8"))):
    if TRAVS and a - TRAVS[-1][1] < 2.5:
        TRAVS[-1][1] = max(TRAVS[-1][1], b)
    else:
        TRAVS.append([a, b])

# travamentos cobertos pela gravação do YouTube (Scripts/remendar_travamentos.py): o trecho fica CONTÍNUO, som da
# Twitch, imagem do YouTube só nos segundos travados — nada de micro-corte em cima de fala (2026-11-26: os
# micro-cortes removiam palavras, ex. "Colocou o dela na reta..." em 1:15:30). Sem remendo, continua o micro-corte.
REM_P = f"{CACHE}/remendos/remendos.json"
REMENDOS = json.load(open(REM_P, encoding="utf-8")) if os.path.exists(REM_P) else []
TRAVS = [tv for tv in TRAVS if not any(r["ini"] - 0.05 <= tv[0] and tv[1] <= r["fim"] + 0.1 for r in REMENDOS)]
# travamentos SEM remendo (alinhamento recusado / YouTube bloqueou o download) com fala do João por cima: ficam no
# vídeo (som inteiro) e cada travada de até 2 s ganha um zoom suave — a imagem nunca fica parada >= 1 s e nenhuma
# palavra some. 0:30:32 ("Vamos dar uma olhada") e 2:32:28 ("Nossa, a gente tem...").
COBRIR_ZOOM = [tv for tv in TRAVS if any(abs(tv[0] - x) < 0.5 for x in (1832.0, 9148.0))]
TRAVS = [tv for tv in TRAVS if tv not in COBRIR_ZOOM]
# fim de episódio decidido à mão (ouvido/medido): fim original -> borda exata
FIM_MANUAL = {
    # Parte 1: termina no comentário da explosão ("...quando ele estivesse falando", fala até 1:06:19.1; som
    # digitalmente mudo 1:06:19.2–1:06:20.2). A pergunta seguinte "qual que a gente vende?" é do assunto removido
    # (vender carro) e ficava colada no corte (QC 2026-11-26: fala no fim do episódio).
    "1:06:19": 3979.85,
}

P, M, C = "PRESERVAR INTEGRALMENTE", "MANTER", "CONDENSAR"
EPISODIOS = [
    {"parte": 1, "frase": "O CARRO EXPLODIU COM O CARA DENTRO!", "alternativo": "ASSALTEI UMA LOJA E PERDI MEU CARRO",
     "resumo": "Quase 40 horas de jogo e o João quer seguir a história: a ligação do Brian, o carro bomba que quebra, "
               "a operação policial aleatória, o carro rosa que some da garagem ('eu sou meio burro também'), o assalto "
               "à loja de conveniência e a fuga pro pântano, a descoberta do código do carro (era a data no formato "
               "americano), a casa do tráfico com quatro bolsas, a casa nova da Andy — e o acidente na estrada em que o "
               "carro explode com o motorista conversando com o Jason.",
     "trechos": [
         ("Quase 40 horas de jogo", "0:00:00", "0:00:33.2", M, "Abertura: 40 horas e ainda no capítulo 3, 'Deus abençoe a Rockstar'"),
         ("O plano do Brian", "0:04:01", "0:07:58", M, "Ligação do Brian/Laurie (diálogo do jogo) e o 'final perfeito' na opinião do João"),
         ("Carro bomba", "0:08:47.5", "0:16:59.5", M, "O carro quebra, operação policial aleatória com bolsa de dinheiro, garagens"),
         ("Cadê o carro rosa?", "0:21:20.5", "0:27:18.5", M, "Perdeu o carro rosa da Lucia: 'é o Growler?', 'eu sou meio burro também'"),
         ("O roubo da loja", "0:30:02.5", "0:38:00", P, "Missão do Jason, depósito, loja de penhores e o assalto rápido com fuga"),
         ("De volta ao pântano", "0:38:00", "0:44:05", M, "Jet ski nos Swamps e o código do carro: era a data no formato americano"),
         ("A casa do tráfico", "0:44:05", "0:57:00", M, "Invadem a casa do tráfico (oitão), cartas colecionáveis, quatro bolsas"),
         ("A casa nova da Andy", "0:57:00", "0:57:42.8", M, "Ligação da Andy: 'eu tenho uma casa nova!' (diálogo do jogo)"),
         ("O carro explodiu", "1:02:02.3", "1:06:19", P, "Acidente na estrada: o motorista preso, o carro explode — 'que jogo de maluco'"),
     ]},
    {"parte": 2, "frase": "A MISSÃO DO TRAILER PARECE FILME!", "alternativo": "O DUBLÊ FANTASMA PULOU DA RAMPA",
     "resumo": "A Mia tem planos pra ganhar dinheiro, o homem queimado do acidente manda mensagem prometendo uma parte "
               "do processo, e começa a missão do trailer — 4 estrelas, 'que cena de cinema'. Depois, a loja de "
               "penhores, o dublê fantasma da Audacity e a rampa de fogo ('esse jogo tá me surpreendendo'), a caçada ao "
               "Charles e o viciado que se joga.",
     "trechos": [
         ("O plano da Mia", "1:10:03", "1:10:50", M, "Ligação da Mia com planos pra ganhar dinheiro (diálogo do jogo)"),
         ("O homem queimado", "1:13:06", "1:15:00", P, "Mensagem do motorista do acidente: vai processar e mandar a parte deles"),
         ("A missão do trailer", "1:15:00", "1:26:27.9", P, "Missão do trailer: tiroteio, 4 estrelas, 'cena de cinema'"),
         ("Loja de penhores", "1:28:54.4", "1:32:30", M, "Loja de penhores e o acrobata desconhecido no mapa"),
         ("O dublê fantasma", "1:32:30", "1:44:00", P, "Papa Audacity, o dublê fantasma: a rampa de fogo e o 'diálogo maravilhoso'"),
         ("Atrás do Charles", "1:44:00", "1:54:07", M, "Missões liberadas, Dray e a procura pelo Charles"),
         ("O viciado se jogou", "1:56:01.5", "2:02:56", M, "O apartamento do Charles, o viciado que se joga e a decisão de não avançar a história"),
     ]},
    {"parte": 3, "frase": "ACHEI A CAMINHONETE MAIS LINDA!", "alternativo": "CAÇADA NO PÂNTANO COM A LUCIA",
     "resumo": "O segredo de North Mariana com segurança pesada (a Lucia se joga do prédio), o recrutamento da Audacity, "
               "a caminhonete mais linda do jogo que a concessionária não aceita registrar ('tô cheio de ódio'), três "
               "estrelas de graça e a caçada no pântano com a Lucia. Fecha com a opinião do João sobre o final do jogo.",
     "trechos": [
         ("O segredo de North Mariana", "2:02:58.8", "2:20:00", M, "Exploração de North Mariana, segurança pesada, a Lucia se joga"),
         ("Recrutando pra Audacity", "2:20:00", "2:27:00", C, "Missão da Audacity e os inimigos derrubados em silêncio"),
         ("A caminhonete mais linda", "2:27:00", "2:40:00", M, "A caminhonete linda, o registro negado e as três estrelas"),
         ("Caçada com a Lucia", "2:40:00", "2:53:20.5", M, "Garage Junk, caçada no pântano com a Lucia e o cachorro"),
         ("O final do jogo", "2:58:12", "3:01:12", M, "O jacaré, a 'imaculada' e 'o final que aparecer vai ser esse'"),
     ]},
    {"parte": 4, "frase": "VOLTEI NA CASA QUE EXPLODIU!", "alternativo": "A MISSÃO DO KIRK NÃO FUNCIONA",
     "resumo": "Jason e Lucia voltam à casa que explodiu (fotos, fundo de emergência — e a iguana viva com os filhotes), "
               "sobem a torre atrás de cartas colecionáveis, caçam no pântano esperando a noite ('National Geographic'), "
               "veem a rede social do crime no celular e tentam começar a missão do Kirk até o fim da live.",
     "trechos": [
         ("A casa que explodiu", "3:07:07.3", "3:17:00", P, "A casa destruída, as fotos e a iguana viva com os filhotes"),
         ("A torre e as cartas", "3:17:00", "3:24:13.8", M, "O trailer do Dunk, a torre, cartas e o fuzil que era mentira"),
         ("Esperando a noite", "3:30:03.6", "3:50:00", C, "Caçada no pântano esperando a noite: jacaré albino, 'National Geographic'"),
         ("A rede social do crime", "3:50:00", "3:55:00", M, "Halifax, a rede social do crime no celular (diálogos do jogo)"),
         ("A missão do Kirk", "3:55:00", "4:09:22.5", M, "A missão do Kirk que não ativa, o airboat e a despedida da live"),
     ]},
]

REMOVIDOS = [
    "0:00:33–0:04:01: papo de Thanksgiving, fone e ajustes da live",
    "0:07:58–0:08:48: ajuste de tela e papo sobre viewers",
    "0:16:59–0:21:20: 7 travamentos da live em 2 min + conversa sobre garagens com o chat",
    "0:27:10–0:30:02: indecisão no menu de missões",
    "0:57:32–1:02:02: papo sobre PC, 60 fps e RP com o chat",
    "1:06:19–1:10:03: escolher qual carro vender",
    "1:10:50–1:13:06: AFK (banheiro) com o carro rodando sozinho",
    "1:26:28–1:28:54: 35 travamentos da live em 2 min + despedida do Kleber",
    "1:54:13–1:56:01: agradecimento de sub e recapitulação do dia pro Will",
    "2:53:20–2:58:12: conversa com amigo (viagem, spoilers do final visto em outra live)",
    "3:01:12–3:07:07: Valorant/PC, anúncio na live e papo",
    "3:24:13–3:30:04: pedindo comida no Uber Eats",
    "Micro-cortes de travamento da live (1–15 s): 0:30:32, 0:42:38, 0:42:44, 0:44:00, 0:45:48–0:46:04, 0:47:36, "
    "0:50:52, 0:52:02, 0:52:42, 0:55:00–0:55:14, 1:15:30–1:15:40, 2:32:28",
]


def dentro_trav(x):
    return next(((a, b) for a, b in TRAVS if a - 0.05 <= x <= b + 0.05), None)


plano_eps = []
for ep in EPISODIOS:
    segs = []
    tr = ep["trechos"]
    for k, (cap, a, b, dec, mot) in enumerate(tr):
        ra, rb = t(a), t(b)
        colado_antes = k > 0 and t(tr[k - 1][2]) == ra
        colado_depois = k + 1 < len(tr) and t(tr[k + 1][1]) == rb
        final = k == len(tr) - 1
        marca = []
        # início
        if colado_antes:
            ia = segs[-1]["origem_fim"]
        elif ra < 1:
            ia = 0.0
        elif dentro_trav(ra) or any(abs(ra - bb) < 1.0 for _, bb in TRAVS):
            ia, marca = round(max(ra, (dentro_trav(ra) or (0, ra))[1] + 0.03), 2), ["ini"]
        else:
            ia = B.inicio(ra)
        # fim
        if colado_depois:
            ib = rb
        elif any(abs(rb - aa) < 1.0 for aa, _ in TRAVS) or dentro_trav(rb):
            ib, marca = round(min(rb, (dentro_trav(rb) or (rb, 0))[0] - 0.03), 2), marca + ["fim"]
        elif b in FIM_MANUAL:
            ib = FIM_MANUAL[b]
        else:
            ib = B.fim(rb, final=final)
            tv = next(((aa, bb) for aa, bb in TRAVS if ra < aa < ib), None)
            if tv and tv[0] > rb - 0.05:      # a borda andou para dentro de um travamento: para antes dele
                ib, marca = round(tv[0] - 0.03, 2), marca + ["fim"]
        ib = min(ib, round(DUR - 0.05, 2))
        if segs and not colado_antes and ia < segs[-1]["origem_fim"] + 0.3:
            ia = segs[-1]["origem_fim"]
        # micro-cortes nos travamentos dentro do trecho
        pedacos, cur, cur_marca = [], ia, [m for m in marca if m == "ini"]
        for aa, bb in TRAVS:
            if cur + 0.5 < aa and bb < ib - 0.5:
                pedacos.append((cur, round(aa - 0.03, 2), cur_marca + ["fim"]))
                cur, cur_marca = round(bb + 0.03, 2), ["ini"]
        pedacos.append((cur, ib, cur_marca + [m for m in marca if m == "fim"]))
        for j, (x, y, mk) in enumerate(pedacos):
            if y - x < 0.8:
                continue
            segs.append({"capitulo": cap, "origem_inicio": round(x, 2), "origem_fim": round(y, 2), "decisao": dec,
                         "motivo": mot + (" (continua depois de um travamento da live)" if j else ""),
                         "transicao": "corte", "corte_travamento": sorted(set(mk)) or None})
    if R:
        segs = R.abertura(R.enxugar(R.abertura(segs)))
    # imagem com paradas por cima de fala (remendo cujo YouTube também para em pedaços, ou travamento sem remendo):
    # UM zoom contínuo e lento cobrindo o intervalo todo — a imagem nunca fica parada e nenhuma palavra some
    cobrir = [(r["ini"], r["fim"], 1.10) for r in REMENDOS if r.get("paradas")] + [(a_, b_, 1.06) for a_, b_ in COBRIR_ZOOM]
    for sg in segs:
        for ca, cb, esc in cobrir:
            za, zb = ca - 0.05, cb + 0.7
            # parada encostada na borda do trecho (ex.: fim da missão do trailer, som do jogo até 1:26:29.95 com o
            # YouTube parado — QC 2026-11-26): o zoom é recortado no trecho, se alguma parada cair dentro dele
            paradas = next((r.get("paradas") for r in REMENDOS if r["ini"] == ca), None) or [[ca, cb]]
            if not any(sg["origem_inicio"] < y and x < sg["origem_fim"] for x, y in paradas):
                continue
            za, zb = max(za, sg["origem_inicio"]), min(zb, sg["origem_fim"])
            if zb - za >= 1.0:
                sg.setdefault("zooms", []).append({"inicio": round(za - sg["origem_inicio"], 2),
                                                   "fim": round(zb - sg["origem_inicio"], 2), "escala": esc,
                                                   "cx": 0.5, "cy": 0.5, "continuo": True,
                                                   "motivo": "cobre parada da imagem com fala por cima"})
    pos, caps = 0.0, []
    for s in segs:
        s["editado_inicio"] = round(pos, 2)
        pos += s["origem_fim"] - s["origem_inicio"]
        if not caps or caps[-1]["titulo"] != s["capitulo"]:
            caps.append({"titulo": s["capitulo"], "inicio_editado": s["editado_inicio"]})
    n_yt = NUM_YT_INICIAL + ep["parte"] - 1
    tit_yt = f"GTA 6 #{n_yt} - | {ep['frase']} | Grand Theft Auto VI | Português PT-BR | PS5 Pro"
    assert len(tit_yt) <= 100, (len(tit_yt), tit_yt)
    nome = f"GTA VI - VOD ({DATA_VOD}) PARTE - {ep['parte']}"
    plano_eps.append({
        "parte": ep["parte"], "titulo": f"{ep['frase']} | Parte {ep['parte']}",
        "titulo_alternativo": f"{ep['alternativo']} | Parte {ep['parte']}", "titulo_card": ep["frase"],
        "titulo_youtube": tit_yt, "resumo": ep["resumo"], "status": STATUS, "thumb": [],
        "arquivo": f"Trabalho/teste_ritmo/{nome}.mp4" if TESTE else f"videos_longos/{JOGO}/{nome}.mp4",
        "origem_inicio": segs[0]["origem_inicio"], "origem_fim": segs[-1]["origem_fim"],
        "duracao_estimada": round(pos + 10.0, 1), "montagem": segs, "capitulos": caps,
    })

plano = {
    "video": f"Bruto/live_{VOD}_1440p60.mp4", "jogo": JOGO, "vod": f"https://www.twitch.tv/videos/{VOD}",
    "vod_youtube": "https://www.youtube.com/watch?v=_WKY4GFmZ7Q (mesma live; tempo Twitch = YouTube + 281,9 s)",
    "transcricao": TR, "audio": AUDIO, "analise": f"{CACHE}/analise/analise.json",
    "narrativa": f"{CACHE}/narrativa.json", "travamentos_fonte": TRAV, "perfil": PERFIL,
    "estilo": "Estilo/ESTILO - video longo V4.md", "status": STATUS,
    "formato": "16:9 2560x1440 60 fps (igual à fonte original)",
    "encerramento": {"arquivo": "Estilo/encerramento_gta6.png", "duracao": 10.0},
    "facecam": [53, 160, 587, 320],     # detectada automaticamente (analise/facecam.jpg) e conferida
    "censura": [],                       # conferido: TV/loja em 0:32 = lingerie/biquíni; post em 3:53 = sem camisa
    "removidos_relevantes": REMOVIDOS,
    "remendos_video": REMENDOS,
    "bordas_conferidas": [
        {"t": 3979.85, "nota": "fim da Parte 1 no silêncio digital depois de '...quando ele estivesse falando' (medido: -75 dB de 3979.2 a 3980.2)"},
        {"t": 7376.0, "nota": "fim da Parte 2 na animação de troca de personagem (zoom de satélite): o 'som' é o efeito da troca, sem diálogo"},
        {"t": 7378.8, "nota": "começo da Parte 3 no fim da troca para a Lucia (zoom de satélite), sem diálogo"},
    ],
    "episodios": plano_eps, "duracao_original": DUR,
}
SAIDA = f"Trabalho/plano_gta_{VOD}{'_teste_ritmo' if TESTE else ''}.json"
json.dump(plano, open(SAIDA, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
if R:
    print(R.resumo())
for e in plano_eps:
    print(f"Parte {e['parte']}: {e['duracao_estimada'] / 60:.1f} min | {len(e['montagem'])} trechos | {e['titulo_youtube']} ({len(e['titulo_youtube'])})")

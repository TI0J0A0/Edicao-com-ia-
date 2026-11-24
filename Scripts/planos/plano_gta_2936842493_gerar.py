"""Gera Trabalho/plano_gta_2936842493.json — live de GTA 6 (Twitch 2936842493, 22/11/2026, 2h51,
"Ah shit, here we go again") dividida em uma SÉRIE de episódios (regras v3 do Estilo). Vem DEPOIS da série de 20/11.

Cada episódio = lista de trechos MANTIDOS (capítulo, início, fim, decisão, motivo[, "dissolve"]).
Tudo fora deles é removido. Bordas ajustadas para cair numa pausa entre palavras.
Mapa feito com a transcrição completa (longo_gta_2936842493/transcricao_por_minuto.txt) + painéis de 30 s.
"""
import json
import os

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # Scripts/planos/ -> raiz
os.chdir(RAIZ)
TR = "Trabalho/GTA live 2936842493_transcricao.json"
d = json.load(open(TR, encoding="utf-8"))
palavras = [w for f in d["frases"] for w in f["palavras"]]
JOGO = "GTA 6"
DATA_VOD = "22-11-2026"   # data da live (Twitch), DD-MM-AAAA — entra no nome do arquivo
NUM_YT_INICIAL = 17       # continua a numeração: 19/11 = #4–#10, 20/11 = #11–#16 — CONFIRMAR com o João
STATUS = "aguardando aprovação"


def t(s):
    p = [float(x) for x in s.split(":")]
    return p[0] * 3600 + p[1] * 60 + p[2] if len(p) == 3 else p[0] * 60 + p[1]


def snap(x, lado):
    """tira a borda de dentro de uma palavra (recua no início, avança no fim), com respiro"""
    for i, w in enumerate(palavras):
        if w["inicio"] - 0.15 <= x <= w["fim"] + 0.15:
            if lado == "ini":
                ant = palavras[i - 1]["fim"] if i else 0
                return round(max(w["inicio"] - 0.2, (ant + w["inicio"]) / 2), 2)
            prox = palavras[i + 1]["inicio"] if i + 1 < len(palavras) else d["duracao"]
            return round(min(w["fim"] + 0.25, (w["fim"] + prox) / 2), 2)
        if w["inicio"] > x + 1:
            break
    return round(x, 2)


P = "PRESERVAR INTEGRALMENTE"
M = "MANTER"
E = "ENCURTAR"
EPISODIOS = [
    {"parte": 1, "titulo": "FOMOS ABDUZIDOS NO GTA 6! | Parte 1",
     "alternativo": "O LABORATÓRIO SECRETO DO PÂNTANO | Parte 1",
     "resumo": "A live começa no motel da Vicky e, na primeira volta de carro à noite, o Jason é abduzido por uma "
               "nave. Depois vêm a notícia dos corpos no porta-malas, a caçada com o Vogel, a viagem até a cidade, "
               "os malucos fantasiados de frango e a cabana do pântano com o laboratório de caranguejos mutantes, "
               "o cofre do 'double success' e o dono maluco que perdeu os braços.",
     "trechos": [
        ("Abduzidos", "0:00:00", "0:09:16", P, "Abertura no motel e a abdução pela nave — 'a gente foi abduzido, mano'"),
        ("Abduzidos", "0:09:16", "0:17:44", M, "Notícia dos corpos no porta-malas, missões no celular e a estrada pro norte"),
        ("Caçada com o Vogel", "0:17:44", "0:24:00", P, "Cutscene com o Vogel e a caçada — termina antes do áudio mutado"),
        # 0:24:00–0:27:00: áudio da VOD silenciado pela Twitch (180 s exatos) — elipse com dissolve
        ("Rumo à cidade", "0:27:00.1", "0:30:59", M, "Missão de caça liberada, vender os animais, 'vou na casa da Mandy'", "dissolve"),
        ("Rumo à cidade", "0:31:12", "0:32:58", M, "Entra no túnel escuro — 'só a gente não bater que a gente não morre'"),
        ("Rumo à cidade", "0:33:09", "0:34:17", E, "O carro bonitinho e a dúvida sobre Orlando no mapa"),
        ("Os caras do frango", "0:34:42", "0:39:25", P, "Os malucos fantasiados de frango e o gerente do restaurante — 'thank you nada, mano'"),
        ("O laboratório do pântano", "0:40:18", "0:50:00", M, "Barco até o pântano, o pé grande, a cabana trancada e o laboratório de caranguejos"),
        ("O código", "0:50:00", "1:00:00", P, "O código do cofre: 'double success' — a matemática até o 0-2-12"),
        ("O código", "1:00:00", "1:01:32", P, "O dono maluco sem os braços e a submetralhadora (fechamento)"),
     ]},
    {"parte": 2, "titulo": "A MANDY É UMA PSICOPATA?! | Parte 2",
     "alternativo": "OS SEGREDOS MAIS BIZARROS DO PÂNTANO | Parte 2",
     "resumo": "O João mostra os segredos do pântano que o pessoal do trabalho contou: o vídeo esquisito no rio, os "
               "jacarés albinos de 3 mil, o assentamento hostil, o 'movimento sem descarga' e o homem que morreu em "
               "pé. Na cidade, quase é roubado na loja, escuta a Dra. Nita no rádio e investiga a casa e o "
               "porta-malas da Mandy — cutelo, ácido, corda, pá e serra — até a polícia chegar com 4 estrelas.",
     "trechos": [
        ("Segredos do pântano", "1:03:31", "1:04:56", M, "Por que explorar: o que o pessoal do trabalho contou + localização da sidequest"),
        ("Segredos do pântano", "1:05:08", "1:06:23", M, "'Jason, filha da mãe' — a bolsa de espólio"),
        ("Segredos do pântano", "1:07:00", "1:07:41", M, "Explica como liberar a venda da caça (3 mil por jacaré)"),
        ("Segredos do pântano", "1:09:03", "1:10:27", M, "A fita misteriosa: 'tô até com medo de dar play'"),
        ("Jacarés albinos", "1:11:29", "1:22:00", M, "Jacaré gigante, os albinos de 3 mil, o helicóptero e o assentamento armado"),
        ("Jacarés albinos", "1:22:00", "1:26:00", M, "'Só queria ver o que tava rolando' — o incêndio e os gators"),
        ("Movimento sem descarga", "1:26:00", "1:30:31", P, "A fazenda adubada com a própria bosta e o maluco que morreu em pé (blur nos genitais)"),
        ("Movimento sem descarga", "1:30:31", "1:33:01", M, "Marcadores do pé grande e o plano: Mandy e a casa dela"),
        ("Quase roubado", "1:34:29", "1:39:59", M, "Loja de roupas: 'o cara ia me roubar — que bom que eu não fui no banheiro'"),
        # 1:39:59–1:45:57: o João saiu da frente da câmera (live parada) — removido
        ("A casa da Mandy", "1:45:57", "1:46:47", M, "'Ninguém roubou nós, não, né?'", "dissolve"),
        ("A casa da Mandy", "1:47:09", "1:53:15", P, "A Abuela Sucia, a investigação na casa e o porta-malas da Mandy"),
        ("A casa da Mandy", "1:53:15", "2:01:11", M, "Dra. Nita (Anitta) no rádio, o bar e as 4 estrelas — 'é um pouco too much, não?' (gancho)"),
     ]},
    {"parte": 3, "titulo": "FUGI DE AVIÃO COM CAÇAS ATRÁS! | Parte 3",
     "alternativo": "FINALMENTE CHEGAMOS EM VICE CITY | Parte 3",
     "resumo": "Procurado com 4 estrelas, o João troca de carro, invade o aeroporto, rouba um avião e foge com dois "
               "caças atrás até saltar de paraquedas — 'foi cinema isso aqui'. Depois do stalker do motel, o "
               "capítulo avança: o amigo morto, a fuga com a Lucia, a boate do DreQuan em Vice City e o novo "
               "apartamento (capítulo 'Tits Ass Drug Money'), até a despedida da live.",
     "trechos": [
        ("Fuga com 4 estrelas", "2:01:11", "2:02:04", M, "Troca de carro e a decisão de não fazer viagem rápida"),
        ("Fuga com 4 estrelas", "2:03:08", "2:05:00", M, "'Igualzinho o Civic' — o rádio da polícia e a ideia de ir pra Vice City"),
        ("O aeroporto", "2:05:00", "2:19:50", P, "Invade o aeroporto, rouba o avião e foge dos caças — 'foi cinema isso aqui'"),
        ("O aeroporto", "2:19:50", "2:23:56", M, "A bolsa perdida e a missão atrás do motel"),
        ("O stalker", "2:23:56", "2:27:00", M, "A câmera no quarto do stalker e o início da missão"),
        ("Rumo a Vice City", "2:27:00", "2:36:00", P, "O amigo morto, o tiroteio e a fuga com a Lucia — 'é cinema demais'"),
        ("Rumo a Vice City", "2:36:00", "2:44:00", P, "DreQuan, a boate em Vice City e a chegada à cidade"),
        ("O apartamento", "2:44:00", "2:51:34.2", P, "O apartamento da Trina, 'Tits Ass Drug Money' e a despedida da live"),
     ]},
]

# intervalos com NUDEZ de fato (tempo da live) — imagem do jogo borrada, facecam e áudio normais.
# Regra do João: só nudez (seios à mostra, genitais, pelado); biquíni/fio-dental/tapa-mamilo NÃO.
# Conferido quadro a quadro: a dançarina da boate (2:39) usa tapa-mamilo e o apartamento (2:46–2:51) é roupa íntima.
CENSURA = [
    ("1:27:27", "1:27:44", "o maluco do 'movimento sem descarga' sem calça, genitais à mostra (binóculo) — Parte 2"),
    ("1:29:53", "1:30:04", "o mesmo homem pelado da cintura pra baixo, de perto, até cair no chão — Parte 2"),
    ("2:49:43", "2:49:45", "foto de homem pelado (de costas) no celular do jogo — Parte 3 (opcional, a decidir com o João)"),
]

FOLGA_DISSOLVE = 8 * 60
plano_eps = []
for ep in EPISODIOS:
    segs = []
    for cap, a, b, dec, mot, *forcar in ep["trechos"]:
        ia, ib = snap(t(a), "ini"), min(snap(t(b), "fim"), round(d["duracao"] - 0.05, 2))
        if segs and ia < segs[-1]["origem_fim"] + 0.3:
            ia = segs[-1]["origem_fim"]
        tr = "corte"
        if segs and (ia - segs[-1]["origem_fim"] > FOLGA_DISSOLVE or forcar == ["dissolve"]):
            tr = "dissolve"
        segs.append({"capitulo": cap, "origem_inicio": ia, "origem_fim": ib, "decisao": dec, "motivo": mot,
                     "transicao": tr})
    pos, caps = 0.0, []
    for s in segs:
        s["editado_inicio"] = round(pos, 2)
        pos += s["origem_fim"] - s["origem_inicio"]
        if not caps or caps[-1]["titulo"] != s["capitulo"]:
            caps.append({"titulo": s["capitulo"], "inicio_editado": s["editado_inicio"]})
    nome = f"GTA VI - VOD ({DATA_VOD}) PARTE - {ep['parte']}"
    frase = ep["titulo"].split("|")[0].strip()
    plano_eps.append({
        "parte": ep["parte"], "titulo": ep["titulo"], "titulo_alternativo": ep["alternativo"],
        "titulo_card": frase,
        "titulo_youtube": f"GTA 6 #{NUM_YT_INICIAL + ep['parte'] - 1} - | {frase} | Grand Theft Auto VI | Português PT-BR | PS5 Pro",
        "resumo": ep["resumo"], "status": STATUS, "thumb": [],
        "arquivo": f"videos_longos/{JOGO}/{nome}.mp4",
        "origem_inicio": segs[0]["origem_inicio"], "origem_fim": segs[-1]["origem_fim"],
        "duracao_estimada": round(pos + 10.0, 1),
        "montagem": segs, "capitulos": caps,
    })

plano = {
    "video": "Bruto/live_2936842493_1080p60.mp4", "jogo": JOGO,
    "vod": "https://www.twitch.tv/videos/2936842493", "transcricao": TR,
    "estilo": "Estilo/ESTILO - video longo - Claude Code v2.md (v3)",
    "status": STATUS,
    "formato": "16:9 1920x1080 60 fps (igual à fonte)",
    "encerramento": {"arquivo": "Estilo/encerramento_gta6.png", "duracao": 10.0},
    "facecam": [26, 111, 454, 257],   # nesta live a câmera fica no canto superior esquerdo
    "censura": [{"ini": t(x), "fim": t(y), "nota": n} for x, y, n in CENSURA],
    "removidos_relevantes": [
        "0:24–0:27: áudio da VOD silenciado pela Twitch (direitos autorais) — virou elipse",
        "0:31, 0:33, 0:34, 1:33, 1:46, 2:02: estrada sem fala",
        "0:39:25–0:40:18: quase 1 min sem fala",
        "1:01:32–1:03:31: configurando a transmissão no YouTube ('por que tá como não listado?')",
        "1:04:56–1:05:08, 1:06:23–1:07:00, 1:10:27–1:11:29: papo sobre cortes, vídeos viralizados e postagens (assunto do canal)",
        "1:07:41–1:09:03: conversa sobre o monitor OLED",
        "1:39:59–1:45:57: o João saiu da frente da câmera (live parada)",
    ],
    "episodios": plano_eps,
    "duracao_original": round(d["duracao"], 2),
}
json.dump(plano, open("Trabalho/plano_gta_2936842493.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def hms(x):
    x = int(round(x))
    return f"{x // 3600}:{x % 3600 // 60:02d}:{x % 60:02d}"


tot = 0
for e in plano_eps:
    tot += e["duracao_estimada"]
    print(f"Parte {e['parte']}: {hms(e['origem_inicio'])}–{hms(e['origem_fim'])} -> {e['duracao_estimada'] / 60:.1f} min"
          f" | {len(e['montagem'])} trechos | dissolves {sum(s['transicao'] == 'dissolve' for s in e['montagem'])}"
          f" | {e['titulo']}")
print(f"Total: {tot / 60:.1f} min de {d['duracao'] / 60:.1f} min")

"""Gera Trabalho/plano_gta_2938905930.json — live de GTA 6 (Twitch 2938905930, 24/11/2026, 4h28,
"Ah shit, here we go again") dividida em uma SÉRIE de episódios (regras v3 do Estilo). Vem DEPOIS da série de 22/11.

Cada episódio = lista de trechos MANTIDOS (capítulo, início, fim, decisão, motivo[, "dissolve"]).
Tudo fora deles é removido. Bordas ajustadas para cair numa pausa entre palavras.
Mapa feito com a transcrição completa (longo_gta_2938905930/transcricao_por_minuto.txt) + painéis de 30 s.
Sem blocos mudos da Twitch nesta VOD (silencedetect: só uma pausa de 21 s em 1:01:18).
"""
import json
import os

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # Scripts/planos/ -> raiz
os.chdir(RAIZ)
TR = "Trabalho/GTA live 2938905930_transcricao.json"
d = json.load(open(TR, encoding="utf-8"))
palavras = [w for f in d["frases"] for w in f["palavras"]]
JOGO = "GTA 6"
DATA_VOD = "24-11-2026"   # data da live (Twitch), DD-MM-AAAA — entra no nome do arquivo
NUM_YT_INICIAL = 20       # continua a numeração: 19/11 = #4–#10, 20/11 = #11–#16, 22/11 = #17–#19
STATUS = "aprovado"   # João aprovou o plano inteiro em 2026-11-24


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
    {"parte": 1, "titulo": "INVADI A MANSÃO DE UM RAPPER! | Parte 1",
     "alternativo": "VIRAMOS TRAFICANTES DO DREQUAN | Parte 1",
     "resumo": "A live abre com a história do instalador que queria pôr o modem no banheiro. No jogo, o Jason "
               "invade a mansão de um rapper, tenta salvar o relacionamento com a Lucia, faz a missão do "
               "estúdio do DreQuan ('Tits, Ass, Drug Money'), a venda que vira tiroteio e fuga, o hacker que "
               "não consegue abrir o pendrive e a estátua de bronze levada ao golpista Halifax — 'a gente "
               "vai tomar um golpe?'.",
     "trechos": [
        ("O modem no banheiro", "0:00:00", "0:08:16", P, "Abertura em Vice City, o barco de 4 motores e a história do instalador de internet"),
        ("A mansão do rapper", "0:08:16", "0:14:00", P, "'Holy moly' — a mansão do rapper, o cachorro e o clonador de chave"),
        ("A Lucia não fala comigo", "0:14:00", "0:24:20", M, "Corrida até a Lucia, 'manter relacionamento é difícil no videogame' e o papo do clube de strip"),
        ("O estúdio do DreQuan", "0:24:20", "0:36:00", P, "Missão do DreQuan: o estúdio, 'Tits, Ass, Drug Money' e o encontro com o rapper"),
        ("Venda que deu ruim", "0:36:00", "0:44:00", P, "A venda na quebrada, a armadilha, tiroteio e fuga com 2 estrelas"),
        ("O hacker", "0:44:00", "0:49:00", P, "A Lucia, o Brian e o hacker que não abre o pendrive — 'criptografia militar'"),
        ("A estátua de bronze", "0:49:00", "0:57:53", P, "A estátua de bronze, o golpista Halifax e o relógio — 'a gente vai tomar um golpe?' (gancho)"),
     ]},
    {"parte": 2, "titulo": "ACHEI UM CARRO ESCONDIDO NA MANSÃO! | Parte 2",
     "alternativo": "O CARRO CAPOTOU SOZINHO NO MEIO DA RUA | Parte 2",
     "resumo": "Com a dica do Will, o João revira todas as mansões azuis atrás de um carro registrável — e ele "
               "estava na última casa. No caminho: o evento do carro capotando, o carro verde que vira de "
               "ponta-cabeça sem o Jason ajudar, o Jason dirigindo melhor que a Lucia, o cara que cai da ponte "
               "('a culpa é minha?'), o registro no Mose, a gasolina que acaba e a fuga da polícia. Fecha com "
               "roupa nova pra Lucia.",
     "trechos": [
        ("A dica do Will", "1:01:06", "1:15:00", M, "O carro que o Will mandou achar: mansão por mansão — 'eu tô entrando em todas as mansões'"),
        ("Era a última casa", "1:15:00", "1:21:30", P, "'Que carro lindo!' — o carro estava na última casa, registro barato e o evento do carro capotando"),
        ("Capotei o carro", "1:21:30", "1:30:31", P, "O carro vira, 'Jason, ajuda!', o Jason no volante e o papo sobre a Lucia ambiciosa"),
        ("O cara da ponte", "1:32:52", "1:36:43", M, "'O cara caiu sozinho e a culpa é minha ainda' — o evento aleatório da ponte"),
        ("Registrando no Mose", "1:38:02", "1:50:00", M, "Estrada, o veado, o carro registrado, a gasolina que acaba e a fuga da polícia"),
        ("Roupa nova pra Lucia", "1:51:28", "1:58:48", M, "Procurado em todo lugar, a loja de roupas e o maiô novo da Lucia"),
     ]},
    {"parte": 3, "titulo": "ASSALTEI A JOALHERIA E FUI ABDUZIDO! | Parte 3",
     "alternativo": "SONHEI COM ALIENS E UM MONTE DE VACAS | Parte 3",
     "resumo": "Silenciador e lanterna nas armas, assalto à joalheria (o cofre sem senha, a segunda tentativa com "
               "0638 e quase nada no saco), fuga com cachorros e mato pegando fogo. O Jason vai dormir e acorda "
               "abduzido: planetas, botões, três portas, vacas e o leite pro bebê alien. Depois, a caça ao ET "
               "pela região industrial, a pasta 'XXX' no computador do maluco e a ponte levadiça que o carro "
               "destrói.",
     "trechos": [
        ("Loja de armas", "1:59:14", "2:03:10", M, "'Pra começar, eu tenho que ir numa loja de arma' — silenciador e fuzil"),
        ("Loja de armas", "2:07:06", "2:09:00", M, "Personaliza o fuzil e passa a arma pra Lucia"),
        ("Assalto à joalheria", "2:09:00", "2:24:30", P, "Reconhecimento, energia, cofre sem senha, segunda tentativa (0638) e a fuga"),
        ("Fuga no mato", "2:24:30", "2:29:44", M, "Cães da polícia, o mato pegando fogo e vender os espólios"),
        ("Abduzido", "2:33:21", "2:44:43", P, "Vai dormir e acorda abduzido: planetas, botões, três portas, vacas e o leite — 'apareceu a missão'", "dissolve"),
        ("Caçando o ET", "2:46:23", "2:46:31", M, "'Vamos lá nesse tal do ET aí'"),
        ("Caçando o ET", "2:50:51", "2:53:25", E, "Chapéu de cowboy pra virar Arthur Morgan e os estilos das lojas"),
        ("Caçando o ET", "2:54:05", "2:57:59", E, "Procurando no mapa — 'tem 75 mil lagos no jogo' — e o táxi pra região industrial"),
        ("Caçando o ET", "2:59:09", "3:05:50", M, "A areia, o galpão e a sala do maluco: a pasta 'XXX' no computador"),
        ("Caçando o ET", "3:06:33", "3:07:06", M, "A pista do ET: final de estrada, baía, construção"),
        ("A ponte levadiça", "3:08:32", "3:14:55", P, "Abre a ponte, o carro buga tudo e 'esse carro não tem mais salvação' (fechamento)"),
     ]},
    {"parte": 4, "titulo": "RESGATEI UM ET NUM BUNKER SECRETO! | Parte 4",
     "alternativo": "O MISTÉRIO DA FAZENDA SEM CÓDIGO | Parte 4",
     "resumo": "Uma garagem trancada numa fazenda vira um quebra-cabeça: o fazendeiro que manda embora, as cabras, "
               "o trator, a revista com números e o código que nunca aparece — com o chat ajudando. O João "
               "desiste ('não é perda de tempo'), acha o bunker do ET perto do pântano, desce com a Lucia no "
               "escuro, acerta a sequência do painel e sai carregando o ET no colo até a nave. Fecha com a "
               "despedida da live.",
     "trechos": [
        ("A fazenda trancada", "3:15:00", "3:19:50", M, "Carro off-road, o celeiro com senha, o fazendeiro 'frutinho' e o petting zoo"),
        ("A fazenda trancada", "3:21:00", "3:24:53", E, "Número do ônibus, explodir o bujão, 'vai ser uma coisa idiota' e a ideia da Lucia"),
        ("O código", "3:27:05", "3:31:58", M, "'O Kleber foi gênio': sobe no trator, a revista e o 361982 que não funciona"),
        ("O código", "3:32:46", "3:34:57", E, "Foto dos números e o sangue em cima da garagem"),
        ("O código", "3:37:20", "3:39:32", E, "'Você tá vendo alguma coisa que eu não tô vendo?' — o resumo de tudo que ele tentou"),
        ("O código", "3:49:12", "3:52:03", E, "Vegetais frescos, marca no mapa e desiste — 'não vou considerar perda de tempo'"),
        ("O bunker do ET", "3:55:21", "3:55:33", M, "'Vou olhar o bagulho do alien'", "dissolve"),
        ("O bunker do ET", "3:56:16", "4:08:00", P, "A dica do chat, o táxi, a antena perto do pântano e a descida no bunker com a Lucia"),
        ("O resgate", "4:08:00", "4:21:00", P, "O painel de luzes, a sequência certa e o ET no colo até a nave — 'que sidequest deliciosa'"),
        ("Despedida", "4:21:00", "4:28:29", P, "O jacaré e a despedida da live"),
     ]},
]

# Nudez: nada nesta live (conferido na fonte: provador da Lucia = maiô; sala do maluco em 3:04 = pôsteres cobertos
# e vídeo de fio-dental/meia arrastão; quarto rosa em 2:33 = ele indo dormir).
CENSURA = []

FOLGA_DISSOLVE = 8 * 60
plano_eps = []
# Bordas (regra 2026-11-24): NUNCA cortar fala nem diálogo do jogo — usa frases da transcrição + energia de
# voz do áudio. Fim de episódio fecha a cena inteira (pausa de 1,5 s). Trechos colados na fonte não são cortes.
import sys  # noqa: E402
sys.path.insert(0, os.path.join(RAIZ, "Scripts"))
from bordas import Bordas  # noqa: E402
AUDIO = next((os.path.join(r, f) for r, _, fs in os.walk("Trabalho") for f in fs
              if f.startswith("audio_") and f.endswith((".mp4", ".m4a", ".wav"))), None)
BORDAS = Bordas(TR, AUDIO)
for ep in EPISODIOS:
    segs = []
    tr_ep = ep["trechos"]
    for k, (cap, a, b, dec, mot, *forcar) in enumerate(tr_ep):
        colado_antes = k > 0 and t(tr_ep[k - 1][2]) == t(a)
        colado_depois = k + 1 < len(tr_ep) and t(tr_ep[k + 1][1]) == t(b)
        ia = segs[-1]["origem_fim"] if colado_antes else BORDAS.inicio(t(a))
        ib = t(b) if colado_depois else BORDAS.fim(t(b), final=(k == len(tr_ep) - 1))
        ib = min(ib, round(d["duracao"] - 0.05, 2))
        if segs and ia < segs[-1]["origem_fim"] + 0.3:
            ia = segs[-1]["origem_fim"]
        tr = "corte"
        if segs and (ia - segs[-1]["origem_fim"] > FOLGA_DISSOLVE or forcar == ["dissolve"]):
            tr = "dissolve"
        segs.append({"capitulo": cap, "origem_inicio": ia, "origem_fim": ib, "decisao": dec, "motivo": mot,
                     "transicao": tr, "transicao_forcada": forcar == ["dissolve"]})
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
    "video": "Bruto/live_2938905930_1080p60.mp4", "jogo": JOGO,
    "vod": "https://www.twitch.tv/videos/2938905930", "transcricao": TR,
    "estilo": "Estilo/ESTILO - video longo V4.md",
    # V4: fontes usadas por transicoes.py / validar_plano.py / revisor_editorial.py
    "audio": AUDIO, "analise": "Trabalho/longo_gta_2938905930/analise.json",
    "narrativa": "Trabalho/longo_gta_2938905930/narrativa.json", "perfil": ["mundo_aberto", "narrativo"],
    "status": STATUS, "aprovado_em": "2026-11-24 (João: \"Aprovado\")",
    "formato": "16:9 1920x1080 60 fps (igual à fonte)",
    "encerramento": {"arquivo": "Estilo/encerramento_gta6.png", "duracao": 10.0},
    "facecam": [26, 111, 454, 257],   # câmera no canto superior esquerdo (conferido em 3:04)
    "censura": [{"ini": t(x), "fim": t(y), "nota": n} for x, y, n in CENSURA],
    "removidos_relevantes": [
        "0:57:53–1:01:06: apresenta o Opa pro Jason/Lucia e anda até o carro (sem história)",
        "1:30:31–1:32:52: papo sobre a Catarina e a viagem dos sonhos pro Japão",
        "1:36:43–1:38:02: live na vertical, TikTok e restrição",
        "1:50:00–1:51:28: ligação com amigo sobre trabalho e agenda da semana",
        "2:03:10–2:07:06: adicionando amigo na PSN, privacidade e conta antiga banida",
        "2:29:44–2:33:21: nome do Porsche rosa, contagem de vídeos postados e qualidade da live",
        "2:44:43–2:50:51: papo com o chat (PS5/PC, vazamento), 'Jamal' e procura sem rumo no mapa",
        "2:53:25–2:54:05: abastecer e o YouTube travando",
        "2:57:59–2:59:09: 'eu vim aqui à toa' (repetição)",
        "3:05:50–3:06:33 e 3:07:06–3:08:32: restrição no TikTok, missão do hotel e aviso de blur nos vídeos",
        "3:19:50–3:21:00, 3:24:53–3:27:05, 3:31:58–3:32:46, 3:34:57–3:37:20, 3:39:32–3:49:12: voltas repetidas na fazenda sem achar o código (~16 min)",
        "3:52:03–3:55:21 e 3:55:33–3:56:16: live do YouTube caindo e agradecimento de sub",
    ],
    "episodios": plano_eps,
    "duracao_original": round(d["duracao"], 2),
}
json.dump(plano, open("Trabalho/plano_gta_2938905930.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)


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

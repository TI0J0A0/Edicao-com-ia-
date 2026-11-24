"""Gera Trabalho/plano_gta_2935010407.json — live de GTA 6 (Twitch 2935010407, 20/11/2026, 6h57)
dividida em uma SÉRIE de episódios (regras v3 do Estilo).

Cada episódio = lista de trechos MANTIDOS (capítulo, início, fim, decisão, motivo). Tudo fora deles é removido.
Bordas ajustadas para cair numa pausa entre palavras. Junções com salto grande na fonte (> 8 min) viram
"dissolve" (elipse de tempo), assim como trechos marcados com 6º campo "dissolve"
(ex.: pular áudio silenciado pela Twitch); o resto é "corte" (crossfade de áudio, imagem corta no meio).
Mapa de eventos feito com a transcrição completa + painéis visuais de 30 s (Trabalho/longo_gta_2935010407/).
"""
import json
import os

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # Scripts/planos/ -> raiz
os.chdir(RAIZ)
TR = "Trabalho/GTA live 2935010407_transcricao.json"
d = json.load(open(TR, encoding="utf-8"))
palavras = [w for f in d["frases"] for w in f["palavras"]]
JOGO = "GTA 6"
DATA_VOD = "20-11-2026"   # data da live (Twitch), DD-MM-AAAA — entra no nome do arquivo
STATUS = "aprovado"   # João aprovou o plano inteiro em 2026-11-22


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
EPISODIOS = [
    {"parte": 1, "titulo": "UM TIGRE NO MEIO DO PÂNTANO?! | Parte 1",
     "alternativo": "EXPLORANDO O PÂNTANO MAIS PERIGOSO DE LEONIDA | Parte 1",
     "resumo": "O João sai com o Jason para explorar os pântanos antes de deixar a primeira região do mapa: pesca de "
               "madrugada, carro 'horroroso', tapa na cara, fuga da polícia ('Oh shit, here we go again'), compra de "
               "armas, invasão de cabanas no airboat, o ataque do tigre, os jacarés e o cofre de 5 dígitos que ele "
               "demora para decifrar até achar a carta rara.",
     "trechos": [
        ("Rumo ao pântano", "0:33.4", "0:46.4", "MANTER", "Abertura real: 'vamos fazer uma exploração no Swamp' — contexto do episódio"),
        ("Rumo ao pântano", "3:02.0", "3:35.0", "MANTER", "Exploração dos pântanos, rolê de noite, pega a moto"),
        ("Rumo ao pântano", "4:07.5", "4:21.0", "MANTER", "Humor: o guaxinim atropelado"),
        ("Rumo ao pântano", "4:57.5", "6:10.0", "ENCURTAR", "Barco atracado, susto com jacaré, peixe gigante, barco iluminado"),
        ("Rumo ao pântano", "7:26.5", "9:02.0", "MANTER", "Missões abertas, pescaria — 'pesca é resiliência' — e o peixe fisgado"),
        ("Rumo ao pântano", "9:40.5", "10:49.5", "MANTER", "Opinião sobre o jogo: 'é um jogo para ser jogado devagar', 14 horas e só essa parte do mapa"),
        ("Rumo ao pântano", "12:32.0", "14:14.0", "MANTER", "Humor: 'esse carro é horroroso', anda de lado como carro de drift"),
        ("Rumo ao pântano", "15:14.0", "15:36.0", "MANTER", "Elogia os eventos aleatórios da rua"),
        # 15:37–17:50: ligação telefônica da vida real (removida por privacidade)
        ("Rumo ao pântano", "17:51.5", "19:06.0", "MANTER", "Papo do Pé Grande e a briga com 'tapa na cara' — 'é humilhante'"),
        ("Rumo ao pântano", "19:20.0", "19:46.0", "ENCURTAR", "Loja: procura roupa de caça"),
        ("Procurado", "20:15.0", "21:05.0", "MANTER", "Tudo dá errado de repente — 'tava de boa' — e vira perseguição"),
        ("Procurado", "21:34.0", "22:12.0", "ENCURTAR", "Foge pela água — 'será que eles vêm na água?'"),
        ("Procurado", "22:50.0", "24:12.0", "MANTER", "Barco da polícia, susto com 'tubarão', escapa da perseguição"),
        ("Procurado", "24:42.0", "25:46.0", "MANTER", "'Esse jogo tá muito lindo' + dá pra ficar gordo igual no San Andreas + John Cena"),
        ("Procurado", "26:02.0", "27:08.0", "ENCURTAR", "Veículo apreendido; 'vamos vir pro pântano'"),
        ("Procurado", "27:46.0", "28:25.0", "MANTER", "'Oh shit, here we go again' — a frase que dá nome à live"),
        ("Armado até os dentes", "30:17.0", "31:15.0", "ENCURTAR", "Loja de armas: colete e o 'fuzilzão'"),
        ("Armado até os dentes", "31:26.0", "32:23.0", "ENCURTAR", "Personaliza o fuzil — 'os caras foram além'"),
        ("Armado até os dentes", "33:10.0", "33:23.0", "MANTER", "'Sou apaixonado na 1911'"),
        ("Armado até os dentes", "36:39.0", "38:32.0", "MANTER", "Explica o plano (explorar antes de sair da cidade) + encontro com os caras do dinheiro sujo e o helicóptero"),
        ("Armado até os dentes", "40:11.0", "40:52.0", "MANTER", "Testa o coquetel molotov"),
        ("O tigre", "42:38.0", "44:12.0", "PRESERVAR INTEGRALMENTE", "Procura o airboat e é atacado por um TIGRE — 'como é que tem um tigre aqui?'"),
        ("O tigre", "44:22.0", "45:48.0", "ENCURTAR", "Sobe o pântano de airboat — 'esse barquinho é difícil de controlar'"),
        ("Cabanas do pântano", "45:50.0", "48:06.0", "PRESERVAR INTEGRALMENTE", "Tiroteio nas cabanas e o crocodilo pega o inimigo"),
        ("Cabanas do pântano", "48:48.0", "50:24.0", "MANTER", "Saque das cabanas e o atirador escondido"),
        ("Cabanas do pântano", "50:32.0", "52:27.0", "MANTER", "Baseado 'pra Lucia', limite de armas, a retaliação dos jacarés"),
        ("Cabanas do pântano", "52:36.0", "54:20.0", "ENCURTAR", "Revira as cabanas — 'só tinha isso? não é possível'"),
        ("Cabanas do pântano", "55:46.0", "56:06.0", "MANTER", "Vende o barco: 1400 — 'esperava mais'"),
        ("Cabanas do pântano", "56:34.0", "57:12.0", "MANTER", "'Trabalhar não me dá experiências como essas' + a 'bomba'"),
        ("Cabanas do pântano", "57:45.0", "58:40.0", "ENCURTAR", "Área proibida de óleo — 'olha esse maluco'"),
        ("Cabanas do pântano", "58:58.0", "1:01:05.0", "MANTER", "Onde aconteceu a treta com a mulher do chefe; os Kingfishers voltam"),
        ("Cabanas do pântano", "1:01:48.0", "1:02:34.0", "MANTER", "Ideia de alimentar os jacarés — 'seria muita crueldade'"),
        ("Cabanas do pântano", "1:03:32.0", "1:04:46.0", "MANTER", "Barcos abandonados, procura a base do exército (Forte Zancudo)"),
        ("Cabanas do pântano", "1:05:06.0", "1:05:50.0", "ENCURTAR", "Encontro com jacaré"),
        ("O cofre impossível", "1:07:16.0", "1:08:41.0", "MANTER", "Contexto: a próxima missão leva para Vice City; medo de perder as missões"),
        ("O cofre impossível", "1:09:00.0", "1:09:37.0", "MANTER", "Esperança de achar algo nas cabanas"),
        ("O cofre impossível", "1:10:30.0", "1:11:27.0", "ENCURTAR", "Revista os trailers"),
        ("O cofre impossível", "1:11:27.0", "1:12:53.0", "MANTER", "Acha um cofre e tenta o código"),
        ("O cofre impossível", "1:14:18.0", "1:14:46.0", "ENCURTAR", "Pede dica ao chat 'sem falar onde tá'"),
        ("O cofre impossível", "1:15:50.0", "1:16:06.0", "MANTER", "'Tô até pensando que tenho que começar a usar óculos'"),
        ("O cofre impossível", "1:16:27.0", "1:17:44.0", "PRESERVAR INTEGRALMENTE", "Descobre o 4 escondido — 44017 — e ganha a carta rara; 'o Jason parece um mercenário'"),
        ("O cofre impossível", "1:18:40.0", "1:19:00.0", "MANTER", "Curiosidade: o crocodilo tem a 'pálpebra dupla'?"),
        ("O cofre impossível", "1:19:00.0", "1:20:10.0", "MANTER", "A Lucia apressando + balanço: 3 mil em itens e a carta rara"),
        ("O cofre impossível", "1:20:55.0", "1:21:30.0", "MANTER", "'O cara me chama de psicopata'"),
        ("O cofre impossível", "1:22:03.0", "1:24:30.0", "MANTER", "Volta pra casa com o saque — teoria dos códigos randomizados (fechamento natural)"),
     ]},
    {"parte": 2, "titulo": "O PRIMEIRO SERVIÇO DEU TODO ERRADO! | Parte 2",
     "alternativo": "UM POLICIAL CORRUPTO ACABOU COM A NOSSA VIDA | Parte 2",
     "resumo": "De volta pra casa, o Jason vende o saque e aceita o serviço do Matia com a Lucia. A entrega era uma "
               "armação: presos, interrogados, salvos por um policial corrupto (Mendes) que executa os colegas. "
               "Fuga a tiros, o Jason é baleado, a casa da Lucia é invadida e ela foge de jet ski. Hospital, "
               "nova fuga e o casal acaba escondido num motel de beira de estrada, sem dinheiro.",
     "trechos": [
        ("Fim do capítulo", "1:24:56.0", "1:25:20.0", "MANTER", "A bolsa sumiu?"),
        ("Fim do capítulo", "1:26:20.0", "1:27:18.0", "MANTER", "'Em Leonida a posse de arma é liberada'"),
        ("Fim do capítulo", "1:28:16.0", "1:29:10.0", "ENCURTAR", "Tira o carro do pátio — confusão"),
        ("Fim do capítulo", "1:29:32.0", "1:30:26.0", "ENCURTAR", "O carro vai explodir — polícia"),
        ("Fim do capítulo", "1:32:52.0", "1:34:42.0", "MANTER", "Reclama que o jogo bloqueia roubar carro dos vizinhos; a Mandy sumiu"),
        ("Fim do capítulo", "1:34:42.0", "1:35:58.0", "MANTER", "Entregou o saque; o 'textão' da vizinha e o ciúme da Lucia"),
        # 1:36–1:39: trecho sem fala (pausa) removido
        ("O bar", "1:39:01.0", "1:42:36.0", P, "Cutscene no bar com o Cal — personagens e humor"),
        ("O bar", "1:43:28.0", "1:44:20.0", "ENCURTAR", "Procurando o amigo bêbado"),
        ("O bar", "1:44:50.0", "1:45:52.0", "MANTER", "Fim da missão do Carl — 'que cara, mano'"),
        ("O serviço", "1:46:24.0", "1:47:16.0", "MANTER", "Matia tem um serviço bem pago — vai falar com a Lucia"),
        ("O serviço", "1:47:56.0", "1:50:30.0", P, "Começa o serviço: 'isso vai ser muito ruim pra nós'"),
        ("O serviço", "1:51:22.0", "1:56:54.0", P, "A entrega era armação: presos, interrogatório, o policial Mendes"),
        ("O serviço", "1:56:54.0", "2:02:24.0", P, "Mendes executa os policiais — tiroteio e fuga até o barco"),
        ("Baleado", "2:02:24.0", "2:06:20.0", P, "Jason sangrando no barco; Lucia liga pro Cal levar ele ao hospital"),
        ("Baleado", "2:06:32.0", "2:10:20.0", P, "Casa da Lucia invadida: luta, 'bota no jiu-jitsu', drones"),
        ("Baleado", "2:10:14.0", "2:12:35.0", "MANTER", "Foge de jet ski — 'a vida tranquila que o Jason tinha acabou'"),
        ("Hospital", "2:13:06.0", "2:16:36.0", P, "Lucia no hospital: 'eles tentaram me matar'"),
        ("Hospital", "2:16:36.0", "2:22:00.0", P, "Fuga do hospital"),
        ("Hospital", "2:23:00.0", "2:27:00.0", P, "Perseguição — 'isso é coisa de cinema'"),
        ("Motel de beira de estrada", "2:27:00.0", "2:31:18.6", P, "Escondidos no motel: noticiário, a estatueta misteriosa, 'a gente perdeu tudo'"),
     ]},
    {"parte": 3, "titulo": "A LUCIA FAZ DE TUDO PRA SALVAR O JASON! | Parte 3",
     "alternativo": "SEM DINHEIRO, SEM CARRO E COM O JASON FERIDO | Parte 3",
     "resumo": "Agora com a Lucia: a gerente do motel toma o colar como garantia, ela precisa de remédio para o "
               "Jason e acaba conhecendo a Vicky, o Dunk e o mundo do Delights. Primeiro assalto a loja, o roubo de "
               "carros com o Moe, a confusão com os policiais e, no fim, o colar recuperado e a chamada com o Jason.",
     "trechos": [
        ("Sem nada", "2:31:18.6", "2:34:52.0", P, "A gerente do motel exige o aluguel e fica com o colar"),
        ("Sem nada", "2:35:00.0", "2:36:40.0", "ENCURTAR", "Coloca a máscara 'para cometer delitos' — 'olha a treta que a gente entrou'"),
        ("Remédios", "2:37:00.0", "2:41:00.0", P, "Zach e a vizinha Vicky — os analgésicos"),
        ("Remédios", "2:41:00.0", "2:44:12.0", P, "A briga com a Vicky e a carona até o Dunk"),
        ("Delights", "2:44:12.0", "2:49:02.0", P, "Delights: Frankie, Martin e a Vicky stripper"),
        ("Delights", "2:49:02.0", "2:53:20.0", P, "Conversa com a Vicky: os Colton Associates e as casas de estoque"),
        ("Delights", "2:55:00.0", "3:01:10.0", P, "O namorado da Vicky, perseguição, os remédios falsos e a indicação do Moe"),
        ("Roubando carros", "3:01:10.0", "3:01:52.0", "ENCURTAR", "'A corrida dela tá esquisitinha'"),
        ("Roubando carros", "3:02:00.0", "3:04:00.0", "MANTER", "Leva o carro discreto para o Moe"),
        ("Roubando carros", "3:04:00.0", "3:09:22.0", P, "Moe ensina o roubo de carros — 'é muita mecânica nova de RP'"),
        ("Primeiro assalto", "3:10:00.0", "3:14:10.0", P, "O Delights por fora e o primeiro assalto a loja — 'this is my first robbery'"),
        ("Primeiro assalto", "3:15:00.0", "3:15:42.0", "ENCURTAR", "Mais roubos: 'o posto de gasolina também?'"),
        ("Primeiro assalto", "3:17:00.0", "3:18:00.0", "ENCURTAR", "A limpa e o carro de polícia ao lado"),
        ("Primeiro assalto", "3:20:20.0", "3:21:00.0", "MANTER", "'Tudo que a gente roubou não serviu pra nada'"),
        ("Primeiro assalto", "3:23:00.0", "3:24:46.0", "MANTER", "Interceptação — 'pegou um dinheiro bom' — e a polícia que se comunica"),
        ("Primeiro assalto", "3:25:00.0", "3:28:32.0", "MANTER", "Medicamentos para o Jason; a missão que buga — 'aí é osso'"),
        ("Primeiro assalto", "3:29:30.0", "3:31:32.0", "MANTER", "O armlock absurdo e a plantação de laranja"),
        ("O colar de volta", "3:33:00.0", "3:36:12.0", P, "Paga o motel e recupera o colar; notícias"),
        ("O colar de volta", "3:36:12.0", "3:41:32.0", P, "Chamada com o Jason, remédios e o noticiário (fechamento)"),
     ]},
    {"parte": 4, "titulo": "ESSE MÉDICO ERA UMA ARMADILHA! | Parte 4",
     "alternativo": "A LUCIA SE METEU EM ENCRENCA DE NOVO | Parte 4",
     "resumo": "A Lucia ajuda o Wyman a regular o Dominator, fica sem carro, desce o rio de barco, rouba carros "
               "para o Moe e desconfia de traição numa foto. No Delights ela volta a encontrar o Dunk, e a ida ao "
               "Dr. Bill vira um sequestro: perseguição noturna, o médico em pânico e a fuga com os remédios.",
     "trechos": [
        ("O Dominator", "3:41:40.0", "3:46:12.0", P, "Wyman e o Dominator 67 — regulando o motor"),
        ("A pé", "3:46:12.0", "3:47:30.0", "MANTER", "Fica sem gasolina; balanço do dinheiro"),
        ("A pé", "3:48:20.0", "3:49:02.0", "ENCURTAR", "'Não é possível que não tenha um carrinho aqui'"),
        ("A pé", "3:50:00.0", "3:50:32.0", "ENCURTAR", "Vai pegar o jet ski"),
        ("A pé", "3:51:30.0", "3:52:32.0", "ENCURTAR", "Região abandonada, trator, sem gasolina"),
        ("Pelo rio", "3:52:32.0", "3:54:12.0", "MANTER", "'Esse rio vai até onde?'"),
        ("Pelo rio", "3:56:00.0", "3:58:42.0", "MANTER", "NPC entra no barco, as rádios do jogo"),
        ("Serviços pro Moe", "3:59:00.0", "4:03:22.0", "MANTER", "Máscara, tiro e o carro roubado"),
        ("Serviços pro Moe", "4:04:00.0", "4:05:32.0", "ENCURTAR", "Caminhonete de 14 mil — 'me amarro numa F-250'"),
        ("Serviços pro Moe", "4:07:00.0", "4:08:02.0", "ENCURTAR", "Oficina e transferência de cripto"),
        ("Serviços pro Moe", "4:09:00.0", "4:10:20.0", "MANTER", "Capinha de celular no jogo e a cena do crime"),
        ("Serviços pro Moe", "4:11:20.0", "4:13:22.0", "MANTER", "Briga com o guincheiro e a venda por 1850"),
        ("Serviços pro Moe", "4:14:00.0", "4:16:12.0", "MANTER", "A foto: 'a Lucia tá traindo o Jason!'"),
        ("Serviços pro Moe", "4:16:20.0", "4:18:42.0", "MANTER", "Cancela o táxi sem querer; 'debuff de direção com a Lucia'"),
        ("Serviços pro Moe", "4:20:30.0", "4:24:32.0", "ENCURTAR", "Invade o porto e leva o carro"),
        ("Dr. Bill", "4:25:00.0", "4:28:22.0", P, "Trailer do Dunk: a consulta com o Dr. Bill"),
        ("Dr. Bill", "4:34:40.0", "4:47:00.0", P, "A emboscada ao Dr. Bill — 'a Lucia se mete em tudo'"),
        ("Dr. Bill", "4:47:00.0", "4:57:32.0", P, "Resumo do João, perseguição, fuga com os remédios e 'o capítulo 2 é o Jason na cama'"),
     ]},
    {"parte": 5, "titulo": "O JASON VOLTOU E JÁ FOI ASSALTO! | Parte 5",
     "alternativo": "A DUPLA ESTÁ DE VOLTA | Parte 5",
     "resumo": "Com os remédios garantidos, a Lucia resolve pendências: acidente, briga de rua, roupas novas, a "
               "invasão de uma casa e um carro roubado. O Jason finalmente se levanta, aceita o plano da Lucia e os "
               "dois partem para o assalto à lanchonete e à loja de bebidas, terminando o dia no motel planejando o "
               "próximo passo.",
     "trechos": [
        ("Pendências", "4:57:32.0", "5:03:32.0", "MANTER", "Fim das missões do capítulo 1 (o trailer vira ponto de entrega), o coiote, a briga e o carro destruído"),
        ("Pendências", "5:03:32.0", "5:05:02.0", "ENCURTAR", "'Esse carro é lindo' e os eventos na rua"),
        ("Pendências", "5:06:50.0", "5:08:42.0", "ENCURTAR", "Compras: 'uma mulher de moletom é uma coisa linda'"),
        ("Pendências", "5:09:00.0", "5:12:12.0", P, "'Ela fez cagada de novo, Jason' + cena: 'temos que fazer algo'"),
        ("A invasão", "5:12:12.0", "5:15:32.0", "MANTER", "Invasão da casa — sem silenciador, sem munição, 'vamos fazer barulho'"),
        ("A invasão", "5:15:32.0", "5:18:00.0", "ENCURTAR", "Revista a casa, a polícia chamada"),
        ("A invasão", "5:18:00.0", "5:19:42.0", "MANTER", "'Pegamos nada' — só opioides"),
        ("A invasão", "5:20:00.0", "5:24:22.0", "MANTER", "Ajuda uma mulher e descobre que ela era ladra; o carro detonado"),
        ("O Jason de pé", "5:28:00.0", "5:35:12.0", P, "Vicky e Frankie; o Jason se levanta — 'agora o maluco tá igual um criminoso'"),
        ("Bonnie & Clyde", "5:35:12.0", "5:36:00.0", P, "Assalto à lanchonete"),
        # 5:36:00–5:39:00: áudio da VOD silenciado pela Twitch (180 s exatos, sem som algum) — elipse com dissolve
        ("Bonnie & Clyde", "5:39:00.1", "5:43:02.0", P, "Assalto à loja de bebidas, fuga da polícia", "dissolve"),
        ("Bonnie & Clyde", "5:43:02.0", "5:49:52.0", P, "Motel: Wyman, café e o plano no mapa"),
        ("Bonnie & Clyde", "5:49:52.0", "5:52:21.2", P, "Ligação com o DreQuan — próximos passos (fechamento)"),
     ]},
    {"parte": 6, "titulo": "VIRAMOS BONNIE E CLYDE! | Parte 6",
     "alternativo": "O ASSALTO QUE DEU ERRADO E A NOITE NO DELIGHTS | Parte 6",
     "resumo": "Jason e Lucia juntos no crime: Buckme, troca de tiros, o clube onde a Lucia não sente ciúme, o "
               "assalto em que o cofre escapa e a fuga pelo mato. Fecham negócio com a Vicky, vivem a Ladies Night "
               "do Delights e terminam com o golpe na boate, o dinheiro e a despedida do João.",
     "trechos": [
        ("Juntos no crime", "5:52:24.5", "5:56:02.0", "MANTER", "'O jeito que esses caras falam é muito foda', Buckme e a troca de tiros"),
        ("Juntos no crime", "5:57:00.0", "6:00:42.0", "MANTER", "Polícia no radar; 'essa dinâmica é interessante'"),
        ("Juntos no crime", "6:01:00.0", "6:07:02.0", "MANTER", "Ponto de venda e a dança — 'a Lucia gosta', ganha ponto de relacionamento"),
        ("Juntos no crime", "6:07:00.0", "6:07:42.0", "MANTER", "O Sultan apreendido?"),
        ("Juntos no crime", "6:08:00.0", "6:09:42.0", "ENCURTAR", "Descendo para outra cidade"),
        ("O cofre que escapou", "6:11:00.0", "6:21:52.0", P, "O assalto: a Lucia larga o carro, o cofre não sai e a fuga pelo mato"),
        ("O cofre que escapou", "6:22:00.0", "6:25:02.0", "MANTER", "Monumento de Leonida, o urso na lixeira e a proposta da Vicky"),
        ("O cofre que escapou", "6:26:30.0", "6:27:42.0", "MANTER", "Missão de caça do Brett — 'por isso minha mãe largou meu pai'"),
        ("Ladies Night", "6:28:00.0", "6:35:02.0", P, "Delights: o escritório, Mario e o plano"),
        ("Ladies Night", "6:35:02.0", "6:39:00.6", "MANTER", "Ladies Night — 'o que eu tô tendo que assistir?'"),
        # 6:39:01–6:42:11: áudio da VOD silenciado pela Twitch — elipse com dissolve
        ("Ladies Night", "6:42:11.0", "6:44:42.0", "MANTER", "'O Jason já achou a profissão' e a fuga", "dissolve"),
        ("Ladies Night", "6:45:00.0", "6:50:32.0", P, "O dinheiro, a Vicky e o encontro no parque"),
        ("Ladies Night", "6:51:00.0", "6:56:44.6", P, "O robocall, 'é o Bonnie e Clyde' e a despedida da live (corta antes da vinheta e da tela \"stream terminando\")"),
     ]},
]

# momentos para a imagem-base da thumbnail (thumb_base.py); escolhidos nos painéis de candidatos, o 1º é o principal
THUMBS = {}
THUMBS_DISPENSADO = {  # João dispensou imagem de thumb (2026-11-22); fica só como referência

    1: [('0:43:11', 'o tigre atacando o Jason no pântano'), ('0:43:14', 'o tigre em cima do Jason (alternativa)')],
    2: [('1:52:56', 'o serviço dá errado: Jason rendido no chão pelo policial'), ('1:53:00', 'Jason preso (alternativa)')],
    3: [('3:11:47.0', 'close da Lucia de frente, se preparando para o primeiro assalto', 0.12), ('3:11:42.0', 'Lucia no salão (alternativa)', 0.12)],
    4: [('4:49:44', 'a armadilha: tiroteio e a Lucia saltando no escuro'), ('4:49:40', 'explosão no tiroteio (alternativa)')],
    5: [('5:35:09', 'Jason e Lucia no carro antes do assalto à lanchonete'), ('5:36:24.0', 'Lucia de bandana apontando a arma (alternativa; o trecho ficou fora do episódio por áudio mutado)', 0.15)],
    6: [('6:12:44', 'Jason e Lucia entrando armados juntos — Bonnie e Clyde'), ('6:12:48', 'Jason e Lucia no assalto (alternativa)')],
}

# intervalos com nudez do jogo (tempo da live) — a imagem do jogo fica borrada, facecam e áudio normais
CENSURA = [
    # só NUDEZ de fato (João, 2026-11-22: "apenas nudez extrema como no lapdance"; biquíni, fio-dental,
    # tapa-mamilo e "quase nu" NÃO levam blur). Conferido quadro a quadro em todas as cenas de clube.
    ("6:03:38", "6:04:04", "lap dance: a dançarina tira o sutiã (Parte 6)"),
]

FOLGA_DISSOLVE = 8 * 60
plano_eps = []
for ep in EPISODIOS:
    segs = []
    for cap, a, b, dec, mot, *forcar in ep["trechos"]:
        ia, ib = snap(t(a), "ini"), min(snap(t(b), "fim"), round(d["duracao"] - 0.05, 2))
        if segs and ia < segs[-1]["origem_fim"] + 0.3:       # colado ou sobreposto: continua sem corte
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
    nome = f"GTA VI - VOD ({DATA_VOD}) PARTE - {ep['parte']}"   # padrão de nome do João (2026-11-22)
    plano_eps.append({
        "parte": ep["parte"], "titulo": ep["titulo"], "titulo_alternativo": ep["alternativo"],
        "titulo_card": ep["titulo"].split("|")[0].strip(),
        "resumo": ep["resumo"], "status": STATUS,
        "thumb": [{"origem": t(m[0]), "nota": m[1], "janela": m[2] if len(m) > 2 else 1.0}
                  for m in THUMBS.get(ep["parte"], [])],  # vazio = sem imagem de thumb
        "arquivo": f"videos_longos/{JOGO}/{nome}.mp4",
        "origem_inicio": segs[0]["origem_inicio"], "origem_fim": segs[-1]["origem_fim"],
        "duracao_estimada": round(pos + 10.0, 1),
        "montagem": segs, "capitulos": caps,
    })

plano = {
    "video": "Bruto/live_2935010407_1080p60.mp4", "jogo": JOGO,
    "vod": "https://www.twitch.tv/videos/2935010407", "transcricao": TR,
    "estilo": "Estilo/ESTILO - video longo - Claude Code v2.md (v3)",
    "status": STATUS, "aprovado_em": "2026-11-22 (João: \"Aprovado\")",
    "formato": "16:9 1920x1080 60 fps (igual à fonte)",
    # tela final exclusiva da série GTA 6 (arte do João, 2026-11-22) — 10 s, espaço livre p/ elementos de tela final do YouTube
    "encerramento": {"arquivo": "Estilo/encerramento_gta6.png", "duracao": 10.0},
    # blur só em nudez de fato (regra do João, 2026-11-22)
    "facecam": [1400, 126, 506, 284],
    "censura": [{"ini": t(x), "fim": t(y), "nota": n} for x, y, n in CENSURA],
    "removidos_relevantes": [
        "0:00–0:33 e 0:47–3:02: espera de início de live",
        "15:37–17:50: ligação telefônica da vida real (privacidade)",
        "1:36–1:39: trecho sem fala",
        "3:19–3:20: código sendo digitado em loop",
        "5:24–5:28: menus e configurações",
        "6:25–6:28: minutos parado no mapa",
        "5:36–5:39 e 6:39–6:42: áudio da VOD silenciado pela Twitch (direitos autorais) — viraram elipses",
    ],
    "episodios": plano_eps,
    "duracao_original": round(d["duracao"], 2),
}
json.dump(plano, open("Trabalho/plano_gta_2935010407.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)


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


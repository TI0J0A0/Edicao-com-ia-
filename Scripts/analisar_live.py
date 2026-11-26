"""ANALISTA AUDIOVISUAL (V4) — leitura multimodal leve da live inteira, antes do plano.

Uma passada barata de vídeo (2 amostras/s numa grade 96x54 em cinza + diferença entre amostras calculada pelo
próprio ffmpeg) e uma de áudio (loudness e energia na banda de voz por segundo). Processa em blocos de 30 min,
com CHECKPOINT por bloco (retoma se cair) e até 3 blocos em paralelo.

Sinais por segundo: movimento do jogo, movimento da facecam (reação), luminância, letterbox (cutscene),
corte de cena, tela estática com câmera viva (menu/mapa/pausa), quadro inteiro parado (travamento da live),
loudness, voz.
Janelas de 10 s recebem ETIQUETAS (cutscene, menu, acao, conversa, reacao, tempo_morto, tecnico) e uma
"intensidade" — usadas para PRIORIZAR revisão, nunca para cortar sozinhas (regra do Estilo: nenhum detector
isolado decide).

Saídas (na pasta de cache):
  analise.json        sinais + janelas + eventos (cortes, reações, cutscenes, menus, travamentos, tempo morto)
  resumo_ia.txt       1 linha por minuto: etiquetas + eventos + começo da fala — é o que a IA lê primeiro
                      (bem menor que a transcrição inteira => menos tokens)
  facecam.json/.jpg   (com --facecam auto) retângulo detectado + imagem de conferência
  quadros/            (com --quadros) painéis ADAPTATIVOS: 1 quadro/60 s no geral e 1 quadro/4 s, maior,
                      nas regiões marcadas para detalhar (cutscenes, reações, trocas de etiqueta, dúvidas)

Uso: python Scripts/analisar_live.py <video_ou_proxy> <pasta_cache> [--transcricao T.json]
        [--facecam auto | x,y,w,h] [--fonte-wh 1920x1080] [--quadros VIDEO_HD] [--blocos-paralelos 3]
--fonte-wh: resolução da fonte quando a análise roda no proxy (para converter a facecam).
"""
import argparse
import bisect
import concurrent.futures as cf
import json
import math
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import comum  # noqa: E402

CFG = comum.projeto().get("analise", {})
GW, GH = CFG.get("grade", [96, 54])
SPS = CFG.get("amostras_por_s", 2)
BLOCO = 1800.0
VERSAO = 2          # muda quando o formato do checkpoint muda (invalida caches antigos)
LIMIAR = bytes(0 if v <= 20 else 1 for v in range(256))     # tradução rápida: célula "mudou" se diff > 20


def ler_amostras(video, t0, dur):
    """grade cinza + grade de diferença, SPS amostras/s, via um único ffmpeg (vstack)."""
    fc = (f"[0:v]fps={SPS},format=gray,split[a][b];[a]scale={GW}:{GH}:flags=area[g];"
          f"[b]tblend=all_mode=difference,scale={GW}:{GH}:flags=area[d];[g][d]vstack")
    p = subprocess.Popen(["ffmpeg", "-hide_banner", "-loglevel", "error", *comum.hwaccel_args(),
                          "-ss", f"{t0:.3f}", "-t", f"{dur:.3f}", "-i", video, "-an",
                          "-filter_complex", fc, "-f", "rawvideo", "-pix_fmt", "gray", "-"],
                         stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    n = GW * GH
    while True:
        buf = p.stdout.read(2 * n)
        if len(buf) < 2 * n:
            break
        yield buf[:n], buf[n:]
    p.wait()


def ler_audio(video, t0, dur):
    """loudness (LUFS momentâneo, média por s) e energia de voz (dB, banda 300–3400 Hz) por segundo."""
    r = comum.sh(["ffmpeg", "-hide_banner", "-nostats", "-ss", f"{t0:.3f}", "-t", f"{dur:.3f}", "-i", video, "-vn",
                  "-af", "pan=mono|c0=0.5*c0+0.5*c1,asplit[x][y];[x]ebur128=metadata=1,"
                         "ametadata=print:key=lavfi.r128.M:file=-[xo];"
                         "[y]highpass=f=300,lowpass=f=3400,aresample=8000,asetnsamples=n=8000:p=0,"
                         "astats=metadata=1:reset=1,ametadata=print:key=lavfi.astats.Overall.RMS_level:file=-[yo];"
                         "[xo][yo]amix=inputs=2", "-f", "null", "-"])
    loud, voz = {}, {}
    t = None
    for linha in r.stdout.splitlines():
        if linha.startswith("frame:"):
            try:
                t = float(linha.split("pts_time:")[1])
            except (IndexError, ValueError):
                t = None
        elif t is not None and "=" in linha:
            k, v = linha.split("=", 1)
            try:
                v = float(v)
            except ValueError:
                v = -90.0
            v = v if math.isfinite(v) else -90.0
            s = int(t)
            if k.endswith("r128.M"):
                loud.setdefault(s, []).append(max(-70.0, v))
            elif k.endswith("RMS_level"):
                voz[s] = max(-90.0, v)
    n = int(math.ceil(dur))
    return ([round(sum(loud[s]) / len(loud[s]), 1) if s in loud else -70.0 for s in range(n)],
            [round(voz.get(s, -90.0), 1) for s in range(n)])


def regiao(cam, W, H):
    """facecam (x,y,w,h em pixels da fonte) -> células da grade."""
    if not cam:
        return None
    x, y, w, h = cam
    return (max(0, int(x / W * GW)), max(0, int(y / H * GH)),
            min(GW, int(math.ceil((x + w) / W * GW))), min(GH, int(math.ceil((y + h) / H * GH))))


def soma_regiao(buf, r):
    x0, y0, x1, y1 = r
    return sum(sum(buf[y * GW + x0:y * GW + x1]) for y in range(y0, y1)), (x1 - x0) * (y1 - y0)


def analisar_bloco(video, t0, dur, cam_cel, cache):
    arq = os.path.join(cache, f"analise_bloco_{int(t0):06d}.json")
    feito = comum.carregar_json(arq)
    if feito and feito.get("v") == VERSAO and feito.get("dur") == round(dur, 2) and feito.get("cam") == list(cam_cel or []):
        return feito                                   # checkpoint: bloco já analisado
    gm, cm, lum, lb, frac, amostras_cam = [], [], [], [], [], []
    tot = GW * GH
    k = 0
    for g, d in ler_amostras(video, t0, dur):
        st, nt = sum(d), tot
        sc = nc = 0
        if cam_cel:
            sc, nc = soma_regiao(d, cam_cel)
        gm.append(round((st - sc) / max(1, nt - nc), 2))           # movimento do jogo (fora da cam)
        cm.append(round(sc / nc, 2) if nc else 0.0)                 # movimento da facecam
        mudou = sum(d.translate(LIMIAR))
        frac.append(round(mudou / tot, 3))                          # fração da tela que mudou
        lg, ng = sum(g), tot
        if cam_cel:
            s2, n2 = soma_regiao(g, cam_cel)
            lg, ng = lg - s2, ng - n2
        lum.append(round(lg / max(1, ng), 1))
        # letterbox: 5 linhas de cima e de baixo escuras, meio claro (colunas da facecam ignoradas)
        cols = [x for x in range(GW) if not (cam_cel and cam_cel[0] <= x < cam_cel[2])]
        topo = [g[y * GW + x] for y in range(0, 4) for x in cols[::3]]
        base = [g[y * GW + x] for y in range(GH - 4, GH) for x in cols[::3]]
        meio = [g[y * GW + x] for y in range(GH // 3, 2 * GH // 3) for x in cols[::3]]
        lb.append(1 if topo and max(topo) < 18 and max(base) < 18 and sum(meio) / len(meio) > 28 else 0)
        if cam_cel is None and (k % 4 == 0 or frac[-1] > 0.6):      # amostras p/ detectar facecam
            amostras_cam.append((frac[-1] > 0.6, bytes(d)))
        k += 1
    loud, voz = ler_audio(video, t0, dur)
    res = {"v": VERSAO, "t0": t0, "dur": round(dur, 2), "cam": list(cam_cel or []), "gm": gm, "cm": cm, "frac": frac,
           "lum": lum, "lb": lb, "loud": loud, "voz": voz}
    comum.salvar_json(arq, res)
    # amostras de células para a detecção automática de facecam (binário, à parte)
    if amostras_cam:
        with open(arq[:-5] + "_cam.bin", "wb") as f:
            for corte, d in amostras_cam:
                f.write(bytes([1 if corte else 0]) + d)
    return res


def detectar_facecam(cache, W, H):
    """facecam = região que NÃO muda nos cortes de cena do jogo, mas tem movimento próprio (a pessoa).
    HUD também não muda nos cortes, mas fica parado — por isso exige movimento."""
    tot = GW * GH
    no_corte, mov, nc, nm = [0] * tot, [0] * tot, 0, 0
    for f in sorted(os.listdir(cache)):
        if not f.endswith("_cam.bin"):
            continue
        b = open(os.path.join(cache, f), "rb").read()
        for i in range(0, len(b), tot + 1):
            corte, d = b[i], b[i + 1:i + 1 + tot]
            if len(d) < tot:
                break
            if corte:
                nc += 1
                for c in range(tot):
                    no_corte[c] += d[c]
            else:
                nm += 1
                for c in range(tot):
                    mov[c] += d[c]
    if nc < 8 or nm < 8:
        return {"ok": False, "motivo": f"amostras insuficientes (cortes de cena {nc}, amostras de movimento {nm})"}
    mc = sorted(no_corte)[tot // 2] / nc
    cand = [1 if no_corte[c] / nc < 0.35 * mc and mov[c] / nm > 1.2 else 0 for c in range(tot)]
    # maior componente conexo
    vis, melhor = [0] * tot, []
    for c in range(tot):
        if not cand[c] or vis[c]:
            continue
        pilha, comp = [c], []
        vis[c] = 1
        while pilha:
            u = pilha.pop()
            comp.append(u)
            x, y = u % GW, u // GW
            for v in ((u - 1) if x > 0 else -1, (u + 1) if x < GW - 1 else -1, u - GW, u + GW):
                if 0 <= v < tot and cand[v] and not vis[v]:
                    vis[v] = 1
                    pilha.append(v)
        if len(comp) > len(melhor):
            melhor = comp
    if len(melhor) < 12:
        return {"ok": False, "motivo": "nenhuma região com cara de facecam"}
    xs, ys = [u % GW for u in melhor], [u // GW for u in melhor]
    x0, x1, y0, y1 = min(xs), max(xs) + 1, min(ys), max(ys) + 1
    ret = [round(x0 / GW * W), round(y0 / GH * H), round((x1 - x0) / GW * W), round((y1 - y0) / GH * H)]
    return {"ok": True, "facecam": ret, "celulas": len(melhor), "cortes_usados": nc,
            "preenchimento": round(len(melhor) / ((x1 - x0) * (y1 - y0)), 2)}


def iou(a, b):
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    ix, iy = max(0, min(ax + aw, bx + bw) - max(ax, bx)), max(0, min(ay + ah, by + bh) - max(ay, by))
    i = ix * iy
    return i / (aw * ah + bw * bh - i) if i else 0.0


def percentil(xs, p):
    s = sorted(xs)
    return s[min(len(s) - 1, int(p * len(s)))] if s else 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("cache")
    ap.add_argument("--transcricao")
    ap.add_argument("--facecam", default=None)
    ap.add_argument("--fonte-wh", default=None)
    ap.add_argument("--quadros", default=None, help="vídeo (de preferência o HD) para os painéis adaptativos")
    ap.add_argument("--blocos-paralelos", type=int, default=3)
    ap.add_argument("--inicio", type=float, default=0.0)
    ap.add_argument("--fim", type=float, default=0.0)
    a = ap.parse_args()
    os.makedirs(a.cache, exist_ok=True)
    info = comum.sonda(a.video)
    if a.fonte_wh:
        W, H = map(int, a.fonte_wh.lower().split("x"))
    else:
        W, H = info["w"], info["h"]
    fim = a.fim or info["dur"]
    cam = None
    if a.facecam and a.facecam != "auto":
        cam = [int(v) for v in a.facecam.split(",")]
    saida = {"video": a.video, "fonte_wh": [W, H], "inicio": a.inicio, "fim": fim, "amostras_por_s": SPS}
    if a.facecam == "auto" or not cam:
        # pré-passada curta (3 amostras de 3 min espalhadas) só para achar a facecam; depois a análise
        # completa já mede o movimento da câmera (reações) com o retângulo certo
        pre = os.path.join(a.cache, "facecam_amostras")
        os.makedirs(pre, exist_ok=True)
        tot = fim - a.inicio
        for k in range(3):
            t = a.inicio + tot * (k + 0.5) / 3 - 90
            analisar_bloco(a.video, max(a.inicio, t), min(180.0, tot), None, pre)
        fcm = detectar_facecam(pre, W, H)
        saida["facecam_detectada"] = fcm
        comum.salvar_json(os.path.join(a.cache, "facecam.json"), fcm)
        if fcm.get("ok"):
            print(f"Facecam detectada: {fcm['facecam']} (confira {os.path.join(a.cache, 'facecam.jpg')})", flush=True)
            if a.facecam == "auto":
                cam = fcm["facecam"]
        else:
            print("Facecam: não detectada —", fcm.get("motivo"), flush=True)
    cam_cel = regiao(cam, W, H)
    blocos = []
    t = a.inicio
    while t < fim - 0.5:
        blocos.append((t, min(BLOCO, fim - t)))
        t += BLOCO
    print(f"Analisando {comum.hms(fim - a.inicio)} em {len(blocos)} bloco(s)…", flush=True)
    with cf.ThreadPoolExecutor(max_workers=max(1, a.blocos_paralelos)) as ex:
        res = list(ex.map(lambda b: analisar_bloco(a.video, b[0], b[1], cam_cel, a.cache), blocos))

    if cam:
        saida["facecam"] = cam
        conhecidas = {k: v for k, v in comum.projeto().get("facecam_conhecidas", {}).items() if not k.startswith("_")}
        saida["facecam_parecida_com"] = {k: round(iou(cam, v), 2) for k, v in conhecidas.items()}
        x, y, w, h = cam
        comum.sh(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-ss", f"{(a.inicio + fim) / 2:.1f}",
                  "-i", a.quadros or a.video, "-frames:v", "1", "-vf",
                  f"scale={W}:{H},drawbox=x={x}:y={y}:w={w}:h={h}:color=red@0.9:t=6,scale=960:-2,format=yuvj420p",
                  os.path.join(a.cache, "facecam.jpg")])

    # ---- junta blocos em séries por segundo
    gm, cm, frac, lum, lb, loud, voz = [], [], [], [], [], [], []
    for r in res:
        n = int(math.ceil(r["dur"]))
        for s in range(n):
            amos = slice(s * SPS, (s + 1) * SPS)
            g, c, fr, lu, l_ = r["gm"][amos], r["cm"][amos], r["frac"][amos], r["lum"][amos], r["lb"][amos]
            gm.append(round(sum(g) / len(g), 2) if g else 0)
            cm.append(round(sum(c) / len(c), 2) if c else 0)
            frac.append(max(fr) if fr else 0)
            lum.append(round(sum(lu) / len(lu), 1) if lu else 0)
            lb.append(1 if l_ and sum(l_) * 2 >= len(l_) else 0)
        loud += r["loud"][:n] + [-70.0] * max(0, n - len(r["loud"]))
        voz += r["voz"][:n] + [-90.0] * max(0, n - len(r["voz"]))
    N = len(gm)
    T0 = a.inicio
    fala = [0] * N
    frases = []
    if a.transcricao:
        tr = comum.carregar_json(a.transcricao, {})
        frases = [(f["inicio"], f["fim"], f["texto"]) for f in tr.get("frases", [])]
        for i0, i1, _ in frases:
            for s in range(max(0, int(i0 - T0)), min(N, int(math.ceil(i1 - T0)))):
                fala[s] = 1

    # ---- limiares relativos à própria live (robustos a jogos claros/escuros/barulhentos)
    gm_p25, gm_p75 = percentil(gm, 0.25), percentil(gm, 0.75)
    cm_med, cm_p90 = percentil(cm, 0.5), percentil(cm, 0.9)
    voz_fundo = percentil(voz, 0.2)
    loud_p75, loud_med, gm_med = percentil(loud, 0.75), percentil(loud, 0.5), percentil(gm, 0.5)
    eventos = {"cortes_cena": [], "reacoes": [], "travamentos": [], "cutscenes": [], "menus": [], "tempo_morto": [],
               "tela_preta": []}
    # corte de cena por AMOSTRA, critério absoluto: >70% da tela mudou e a diferença média é grande
    # (relativo à própria live falhava em vídeos com muitos cortes)
    gm_med_am = percentil([x for r in res for x in r["gm"]], 0.5)
    for r in res:
        for k2, (fr2, g2) in enumerate(zip(r["frac"], r["gm"])):
            if fr2 > 0.7 and g2 > max(25.0, 2 * gm_med_am):
                t = round(r["t0"] + k2 / SPS, 1)
                if not eventos["cortes_cena"] or t - eventos["cortes_cena"][-1] >= 1.0:
                    eventos["cortes_cena"].append(t)
    # reação: pico de movimento da câmera junto com voz alta (grito, risada, susto)
    for s in range(N):
        if cm[s] > max(cm_p90 * 1.5, cm_med * 3, 2.0) and voz[s] > voz_fundo + 15:
            if not eventos["reacoes"] or T0 + s - eventos["reacoes"][-1] > 5:
                eventos["reacoes"].append(round(T0 + s, 1))

    def spans(cond, minimo):
        out, ini = [], None
        for s in range(N + 1):
            c = s < N and cond(s)
            if c and ini is None:
                ini = s
            elif not c and ini is not None:
                if s - ini >= minimo:
                    out.append([round(T0 + ini, 1), round(T0 + s, 1)])
                ini = None
        return out
    eventos["cutscenes"] = spans(lambda s: lb[s] == 1, 4)
    eventos["menus"] = spans(lambda s: gm[s] < 0.6 and cm[s] > 0.6 and lum[s] > 12, 5)
    # travamento da LIVE: amostras seguidas (0,5 s) com o quadro inteiro idêntico — jogo E facecam parados.
    # Por amostra (não pela média do segundo), senão travadas de ~1 s passavam despercebidas.
    for r in res:
        run0 = None
        cms = r["cm"] if any(r["cm"]) else [0.0] * len(r["gm"])
        # quadros idênticos não dão 0 exato: a redução para a grade (scale=area) deixa um piso (~0,96 medido).
        # Por isso: no piso do próprio bloco (+0,25) E nenhuma célula mudou (frac == 0).
        piso_g = min(r["gm"]) if r["gm"] else 0.0
        piso_c = min(cms) if cms else 0.0
        for k2 in range(len(r["gm"]) + 1):
            parado = (k2 < len(r["gm"]) and r["frac"][k2] == 0 and r["gm"][k2] <= piso_g + 0.25
                      and cms[k2] <= piso_c + 0.25 and r["lum"][k2] > 8)
            if parado and run0 is None:
                run0 = k2
            elif not parado and run0 is not None:
                if k2 - run0 >= 1:                      # 1 amostra = quadro inteiro idêntico por >= 0,5 s
                    eventos["travamentos"].append([round(r["t0"] + (run0 - 1) / SPS, 1), round(r["t0"] + k2 / SPS, 1)])
                run0 = None
    eventos["tela_preta"] = spans(lambda s: lum[s] < 8, 2)
    sem_voz = (lambda s: not fala[s] and voz[s] < voz_fundo + 8) if frases else (lambda s: voz[s] < voz_fundo + 3)
    eventos["tempo_morto"] = spans(lambda s: sem_voz(s) and cm[s] <= max(cm_med * 1.5, 0.3) and lb[s] == 0
                                   and loud[s] < loud_med and gm[s] < gm_med, 20)

    # ---- janelas de 10 s com etiquetas
    janelas = []
    pos_reac = [r - T0 for r in eventos["reacoes"]]
    for w0 in range(0, N, 10):
        w1 = min(N, w0 + 10)
        rng = range(w0, w1)
        n = len(rng)
        tags = []
        if sum(lb[s] for s in rng) * 2 >= n:
            tags.append("cutscene")
        if sum(1 for s in rng if gm[s] < 0.6 and cm[s] > 0.6) * 10 >= 6 * n:
            tags.append("menu")
        if sum(1 for s in rng if gm[s] < 0.05 and cm[s] < 0.05) >= 1:
            tags.append("tecnico")
        if sum(gm[s] for s in rng) / n > gm_p75 and sum(loud[s] for s in rng) / n > loud_p75 - 3:
            tags.append("acao")
        if sum(fala[s] for s in rng) * 2 >= n:
            tags.append("conversa")
        if bisect.bisect_left(pos_reac, w0) < bisect.bisect_left(pos_reac, w1):
            tags.append("reacao")
        if not tags and all(sem_voz(s) for s in rng):
            calmo = sum(gm[s] for s in rng) / n < gm_med and sum(loud[s] for s in rng) / n < loud_med
            tags.append("tempo_morto" if calmo else "deslocamento")
        elif not tags:
            tags.append("gameplay")
        inten = min(1.0, round(0.35 * min(1, sum(gm[s] for s in rng) / n / max(1, gm_p75 * 2))
                               + 0.35 * min(1, max(0, sum(voz[s] for s in rng) / n - voz_fundo) / 25)
                               + 0.3 * ("reacao" in tags), 2))
        janelas.append({"t": round(T0 + w0, 1), "tags": tags, "intensidade": inten})

    # ---- regiões para olhar com mais detalhe (frames mais densos)
    detalhar = []
    for i, j in enumerate(janelas):
        troca = i and set(j["tags"]) != set(janelas[i - 1]["tags"])
        if "reacao" in j["tags"] or "cutscene" in j["tags"] or "tecnico" in j["tags"] or troca:
            detalhar.append([j["t"], round(j["t"] + 10, 1)])
    fund = []
    for x, y in detalhar:
        if fund and x <= fund[-1][1] + 10:
            fund[-1][1] = max(fund[-1][1], y)
        else:
            fund.append([x, y])
    saida.update({"limiares": {"gm_p25": gm_p25, "gm_p75": gm_p75, "cm_p90": cm_p90, "voz_fundo": voz_fundo,
                               "loud_p75": loud_p75},
                  "por_segundo": {"gm": gm, "cm": cm, "lum": lum, "letterbox": lb, "loud": loud, "voz": voz,
                                  "fala": fala},
                  "eventos": eventos, "janelas": janelas, "regioes_detalhar": fund})
    comum.salvar_json(os.path.join(a.cache, "analise.json"), saida)

    # ---- resumo compacto para a IA (1 linha/min)
    linhas = [f"# Resumo multimodal — {a.video} ({comum.hms(fim - T0)}). Etiquetas por janela de 10 s; "
              f"R=reação C=cutscene M=menu T=travamento P=tela preta; fala = começo do que foi dito no minuto."]
    fi = 0
    for m0 in range(0, N, 60):
        js = [j for j in janelas if T0 + m0 <= j["t"] < T0 + m0 + 60]
        cont = {}
        for j in js:
            for tg in j["tags"]:
                cont[tg] = cont.get(tg, 0) + 1
        evs = []
        for nome, sig in (("reacoes", "R"), ("cortes_cena", None)):
            if sig:
                evs += [f"{sig}{comum.hms(t)[2:]}" for t in eventos[nome] if T0 + m0 <= t < T0 + m0 + 60]
        for nome, sig in (("cutscenes", "C"), ("menus", "M"), ("travamentos", "T"), ("tela_preta", "P")):
            evs += [f"{sig}{comum.hms(x)[2:]}-{y - x:.0f}s" for x, y in eventos[nome] if T0 + m0 <= x < T0 + m0 + 60]
        txt = []
        while fi < len(frases) and frases[fi][0] < T0 + m0 + 60:
            if frases[fi][0] >= T0 + m0:
                txt.append(frases[fi][2])
            fi += 1
        fala_txt = " / ".join(txt)
        if len(fala_txt) > 140:
            fala_txt = fala_txt[:137] + "…"
        inten = max((j["intensidade"] for j in js), default=0)
        tags = " ".join(f"{k}{'×' + str(v) if v > 1 else ''}" for k, v in sorted(cont.items(), key=lambda x: -x[1]))
        linhas.append(f"{comum.hms(T0 + m0)} | i{inten:.1f} | {tags or '-'} | {' '.join(evs)} | {fala_txt}")
    open(os.path.join(a.cache, "resumo_ia.txt"), "w", encoding="utf-8").write("\n".join(linhas) + "\n")

    # ---- painéis adaptativos
    if a.quadros:
        painel_adaptativo(a.quadros, a.cache, T0, fim, fund)
    print(f"cortes de cena {len(eventos['cortes_cena'])} | reações {len(eventos['reacoes'])} | "
          f"cutscenes {len(eventos['cutscenes'])} | menus {len(eventos['menus'])} | "
          f"travamentos {len(eventos['travamentos'])} | tempo morto {len(eventos['tempo_morto'])} trechos "
          f"({sum(y - x for x, y in eventos['tempo_morto']) / 60:.1f} min) | regiões p/ detalhar {len(fund)}")
    print("Saídas:", os.path.join(a.cache, "analise.json"), "e resumo_ia.txt")


def painel_adaptativo(video, cache, t0, t1, regioes):
    """1 quadro/60 s em tudo + 1 quadro/4 s (maior) nas regiões marcadas. Painéis de 24 quadros."""
    pasta = os.path.join(cache, "quadros")
    os.makedirs(pasta, exist_ok=True)
    tempos = {round(t, 1): "base" for t in frange(t0, t1, 60)}
    for x, y in regioes:
        for t in frange(x, min(y, t1 - 0.5), 4):
            tempos[round(t, 1)] = "detalhe"
    lista = sorted(tempos.items())
    fonte = "C\\:/Windows/Fonts/arialbd.ttf"
    for p0 in range(0, len(lista), 24):
        grupo = lista[p0:p0 + 24]
        imgs = []
        for k, (t, tipo) in enumerate(grupo):
            out = os.path.join(pasta, f"_q{k:02d}.jpg")
            cor = "yellow" if tipo == "detalhe" else "white"
            comum.sh(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-ss", f"{t:.2f}", "-i", video,
                      "-frames:v", "1", "-vf", f"scale=480:-2,drawtext=fontfile='{fonte}':text='{comum.hms(t).replace(':', chr(92) + ':')}':"
                      f"x=6:y=6:fontsize=20:fontcolor={cor}:box=1:boxcolor=black@0.7,format=yuvj420p", out])
            if os.path.exists(out):
                imgs.append(out)
        if not imgs:
            continue
        lst = os.path.join(pasta, "_lista.txt")
        with open(lst, "w", encoding="utf-8") as f:
            for im in imgs:
                f.write(f"file '{os.path.abspath(im)}'\n")
        comum.sh(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst,
                  "-vf", "tile=4x6:padding=3,format=yuvj420p", "-frames:v", "1",
                  os.path.join(pasta, f"painel_{p0 // 24:03d}_{comum.hms(grupo[0][0]).replace(':', '')}.jpg")])
        for im in imgs:
            os.remove(im)
        os.remove(lst)


def frange(a, b, p):
    t = a
    while t < b:
        yield t
        t += p


if __name__ == "__main__":
    main()

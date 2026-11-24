"""Monta VÁRIOS episódios longos (16:9, resolução/FPS da fonte) a partir de UM plano aprovado.

Formato do plano (Trabalho/plano_<serie>.json), gerado por um script plano_<serie>_gerar.py:
{
  "video": "Bruto/live.mp4", "jogo": "GTA 6", "status": "aprovado",
  "encerramento": {"arquivo": "Estilo/tiojoao_animado.mp4" | "Estilo/encerramento_<jogo>.png", "duracao": 10.0 (só p/ imagem)},
  "censura": [{"ini": 9000.0, "fim": 9030.5, "nota": "nudez — strip club"}],   # tempos da FONTE; opcional
  "facecam": [1400, 126, 506, 284],          # x, y, w, h da câmera do João (fica nítida no blur)
  "episodios": [
    {"parte": 1, "titulo": "...", "arquivo": "videos_longos/GTA 6/GTA 6 - Parte 01.mp4",
     "status": "aprovado",                     # opcional: só renderiza episódios aprovados
     "montagem": [
        {"capitulo": "Abertura", "origem_inicio": 123.4, "origem_fim": 150.0,
         "decisao": "MANTER", "motivo": "...",
         "transicao": "corte" | "dissolve" | "continuo",   # emenda que ENTRA neste trecho
         "dur_transicao": 0.25,                           # opcional (s)
         "zooms": [{"inicio": 3.0, "fim": 6.0, "escala": 1.10, "cx": 0.5, "cy": 0.5}],  # tempos relativos ao trecho
         "textos": [{"inicio": 1.0, "fim": 3.5, "texto": "alguns minutos depois…"}]}
     ]}
  ]
}

Emendas (regras do Estilo, seção 5):
- "corte"    : imagem corta no meio de uma sobreposição curta e o ÁUDIO faz crossfade
               (padrão 0,20 s) — sem estalo, sem salto de volume. É a emenda invisível padrão.
- "dissolve" : dissolve visual curto (padrão 0,25 s) + crossfade de áudio. Só para elipse de tempo
               ou troca de ambiente; nunca em série.
- "continuo" : trechos colados na fonte; sem sobreposição.
Censura (regra do João, 2026-11-22 — "pro vídeo não cair"): cenas de nudez explícita do jogo ficam com a
imagem do jogo borrada (boxblur forte) durante os intervalos de "censura"; a facecam, os letreiros e o
áudio continuam normais. Vale para corpo dos trechos, dissolves e o quadro final do encerramento.

O áudio de cada episódio é montado numa trilha única com acrossfade em todas as junções e depois
normalizado (-14 LUFS); o vídeo é montado em pedaços com duração em quadros exatos e unido sem
recodificar, então áudio e vídeo terminam juntos.

Uso: python Scripts/montar_episodios.py --plano Trabalho/plano_x.json [--parte 1] [--so N] [--pasta Trabalho/ep_cache]
"""
import argparse
import json
import math
import os
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(RAIZ)
ap = argparse.ArgumentParser()
ap.add_argument("--plano", required=True)
ap.add_argument("--parte", type=int, default=0, help="renderiza só esta parte (0 = todas aprovadas)")
ap.add_argument("--so", type=int, default=0, help="só os N primeiros trechos (teste rápido)")
ap.add_argument("--pasta", default=None)
ap.add_argument("--ignorar-status", action="store_true", help="permite renderizar prévias sem aprovação")
args = ap.parse_args()

plano = json.load(open(args.plano, encoding="utf-8"))
if plano.get("status") != "aprovado" and not args.ignorar_status:
    sys.exit("O plano ainda não foi aprovado.")
SRC = plano["video"]
PASTA = args.pasta or os.path.join("Trabalho", "ep_" + os.path.splitext(os.path.basename(args.plano))[0])

# ---------- propriedades da fonte (mantém resolução e FPS originais)
pr = json.loads(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                                "stream=width,height,r_frame_rate", "-of", "json", SRC],
                               capture_output=True, text=True).stdout)["streams"][0]
W, H = pr["width"], pr["height"]
num, den = map(int, pr["r_frame_rate"].split("/"))
FPS = round(num / den)            # Twitch "59.94/60" -> 60 (o render sai em CFR)
FONTE = "Scripts/fonts/Montserrat-Bold.otf"
RED, ICE, BLACK = (220, 38, 38), (245, 245, 245), (17, 17, 17)
XF_CORTE, XF_DISSOLVE = 0.20, 0.25

VENC = ["-c:v", "h264_amf", "-quality", "quality", "-rc", "cqp",
        "-qp_i", "18", "-qp_p", "20", "-qp_b", "22", "-g", str(FPS * 2), "-pix_fmt", "yuv420p"]
AENC = ["-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2"]


def q(x):
    """arredonda para quadro inteiro"""
    return round(x * FPS) / FPS


CENSURA = sorted((float(c["ini"]), float(c["fim"])) for c in plano.get("censura", []))
CAM = plano.get("facecam")


def censura_em(a, d):
    """intervalos de censura que caem em [a, a+d) da fonte, em tempo relativo ao pedaço"""
    return [(max(0.0, x - a), min(d, y - a)) for x, y in CENSURA if y > a and x < a + d]


def censura_filtro(entrada, saida, iv, tag):
    """borra o quadro inteiro (menos a facecam) nos intervalos iv (tempo relativo do pedaço)"""
    if not iv:
        return [f"{entrada}null{saida}"]
    en = "+".join(f"between(t,{x:.3f},{y:.3f})" for x, y in iv)
    g = [f"{entrada}split=2[{tag}s][{tag}b]", f"[{tag}b]boxblur=luma_radius=40:luma_power=3:chroma_radius=20:chroma_power=3:enable='{en}'[{tag}bb]"]  # só calcula nos intervalos
    if CAM:
        x, y, w, h = CAM
        g += [f"[{tag}s]split=2[{tag}s1][{tag}s2]", f"[{tag}s2]crop={w}:{h}:{x}:{y}[{tag}cam]",
              f"[{tag}bb][{tag}cam]overlay={x}:{y}[{tag}bc]", f"[{tag}s1][{tag}bc]overlay=0:0:enable='{en}'{saida}"]
    else:
        g += [f"[{tag}s][{tag}bb]overlay=0:0:enable='{en}'{saida}"]
    return g


def sufixo_censura(iv):
    return "" if not iv else "_c" + "_".join(f"{round(x * 10)}-{round(y * 10)}" for x, y in iv)[:60]


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="ignore")
    if r.returncode != 0:
        print(r.stderr[-3000:])
        raise SystemExit(f"ffmpeg falhou: {' '.join(cmd[:12])} …")
    return r


def fonte(px):
    return ImageFont.truetype(FONTE, px)


def esp(dr, xy, txt, f, cor, e):
    x, y = xy
    for ch in txt:
        dr.text((x, y), ch, font=f, fill=cor)
        x += dr.textlength(ch, font=f) + e


def larg_esp(dr, txt, f, e):
    return sum(dr.textlength(c, font=f) + e for c in txt) - e


def card_titulo(caminho, jogo, titulo, parte):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    faixa = Image.new("L", (1, H), 0)
    for y in range(H):
        d = abs(y - H / 2) / (H / 2)
        faixa.putpixel((0, y), int(200 * max(0.0, 1 - d * 1.35) ** 0.8))
    escuro = Image.new("RGBA", (W, H), BLACK + (0,))
    escuro.putalpha(faixa.resize((W, H)))
    im = Image.alpha_composite(im, escuro)
    dr = ImageDraw.Draw(im)
    s = H / 1080
    f1, f2 = fonte(int(34 * s)), fonte(int(92 * s))
    topo = f"{jogo.upper()}  ·  PARTE {parte}"
    wj = larg_esp(dr, topo, f1, 10)
    esp(dr, ((W - wj) / 2, 418 * s), topo, f1, ICE + (230,), 10)
    tit = titulo.upper()
    while dr.textlength(tit, font=f2) > W * 0.86 and f2.size > 40:
        f2 = fonte(f2.size - 4)
    wt = dr.textlength(tit, font=f2)
    dr.text(((W - wt) / 2 + 3, 478 * s + 4), tit, font=f2, fill=(0, 0, 0, 150))
    dr.text(((W - wt) / 2, 478 * s), tit, font=f2, fill=RED + (255,))
    dr.rectangle(((W - 120) / 2, 478 * s + f2.size + 40, (W + 120) / 2, 478 * s + f2.size + 45), fill=ICE + (230,))
    im.save(caminho)


def card_capitulo(caminho, n, titulo):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    s = H / 1080
    f1, f2 = fonte(int(22 * s)), fonte(int(46 * s))
    rot = f"CAPÍTULO {n}"
    w = max(larg_esp(dr, rot, f1, 6), dr.textlength(titulo, font=f2))
    x0, y0 = 72 * s, 772 * s
    dr.rectangle((x0, y0, x0 + w + 64, y0 + 112 * s), fill=BLACK + (200,))
    dr.rectangle((x0, y0, x0 + 8, y0 + 112 * s), fill=RED + (255,))
    esp(dr, (x0 + 32, y0 + 18 * s), rot, f1, RED + (255,), 6)
    dr.text((x0 + 32, y0 + 46 * s), titulo, font=f2, fill=ICE + (255,))
    im.save(caminho)


def card_texto(caminho, txt):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    s = H / 1080
    f = fonte(int(30 * s))
    w = dr.textlength(txt, font=f)
    x0, y0 = 72 * s, 800 * s
    dr.rectangle((x0, y0, x0 + w + 48, y0 + 60 * s), fill=BLACK + (190,))
    dr.rectangle((x0, y0, x0 + 6, y0 + 60 * s), fill=RED + (255,))
    dr.text((x0 + 26, y0 + 12 * s), txt, font=f, fill=ICE + (255,))
    im.save(caminho)


def zoom_filtro(zooms):
    """zoom suave (ease in-out) via zoompan quadro a quadro; centro em (cx, cy) relativos."""
    partes_z, partes_x, partes_y = [], [], []
    for z in zooms:
        a, b, e = z["inicio"], z["fim"], min(float(z.get("escala", 1.08)), 1.15)   # teto de qualidade
        r = min(0.6, (b - a) / 3)               # rampa de entrada/saída
        # p(t) = 0..1..0 com cosseno nas rampas
        p = (f"if(between(it,{a},{a + r}),(1-cos(PI*(it-{a})/{r}))/2,"
             f"if(between(it,{a + r},{b - r}),1,"
             f"if(between(it,{b - r},{b}),(1+cos(PI*(it-{b - r})/{r}))/2,0)))")
        partes_z.append(f"({e - 1})*{p}")
        cx, cy = float(z.get("cx", 0.5)), float(z.get("cy", 0.5))
        partes_x.append((cx, a, b))
        partes_y.append((cy, a, b))
    zexpr = "1+" + "+".join(partes_z)

    def centro(lst, eixo):
        expr = "0.5"
        for c, a, b in reversed(lst):
            expr = f"if(between(it,{a},{b}),{c},{expr})"
        return f"max(0,min({eixo}-{eixo}/zoom,({expr})*{eixo}-{eixo}/zoom/2))"
    return (f"zoompan=z='{zexpr}':x='{centro(partes_x, 'iw')}':y='{centro(partes_y, 'ih')}'"
            f":d=1:s={W}x{H}:fps={FPS}")


def fundo(t0, dur, cache):
    """nível de fundo (percentil 25 da loudness momentânea, LUFS) de um trecho da fonte"""
    k = f"{t0:.2f}_{dur:.2f}"
    if k in cache:
        return cache[k]
    r = subprocess.run(["ffmpeg", "-hide_banner", "-ss", f"{max(0, t0):.3f}", "-t", f"{dur:.3f}", "-i", SRC, "-vn",
                        "-af", "ebur128=metadata=1,ametadata=print:key=lavfi.r128.M:file=-", "-f", "null", "-"],
                       capture_output=True, text=True, encoding="utf-8", errors="ignore")
    xs = []
    for linha in r.stdout.splitlines():
        if "lavfi.r128.M=" in linha:
            try:
                xs.append(max(-70.0, float(linha.split("=")[1])))
            except ValueError:
                pass
    xs = sorted(xs[4:])            # descarta o aquecimento da janela de 400 ms
    v = round(xs[len(xs) // 4], 1) if len(xs) >= 6 else None
    cache[k] = v
    return v


def montar(ep):
    parte = ep["parte"]
    pasta = os.path.join(PASTA, f"parte_{parte:02d}")
    os.makedirs(os.path.join(pasta, "v"), exist_ok=True)
    os.makedirs(os.path.join(pasta, "cards"), exist_ok=True)
    segs = ep["montagem"][: args.so] if args.so else ep["montagem"]
    n = len(segs)

    # ---- sobreposição de cada junção (entre i-1 e i)
    A = [q(s["origem_inicio"]) for s in segs]
    B = [q(s["origem_fim"]) for s in segs]
    cache_fundo_p = os.path.join(pasta, "fundo_cache.json")
    cache_fundo = json.load(open(cache_fundo_p, encoding="utf-8")) if os.path.exists(cache_fundo_p) else {}
    ov = [0.0] * n
    tipo = ["inicio"] * n
    diag = {}
    for i in range(1, n):
        t = segs[i].get("transicao", "corte")
        if abs(segs[i]["origem_inicio"] - segs[i - 1]["origem_fim"]) < 0.05:   # colado na fonte
            tipo[i], ov[i] = "continuo", 0.0
            continue
        tipo[i] = "dissolve" if t == "dissolve" else "corte"
        if "dur_transicao" in segs[i]:
            d = float(segs[i]["dur_transicao"])
        else:
            # crossfade adaptativo: degrau grande no som de fundo pede transição de áudio mais longa
            fa = fundo(B[i - 1] - 3.0, 3.0, cache_fundo)
            fd = fundo(A[i], 3.0, cache_fundo)
            dif = abs(fa - fd) if fa is not None and fd is not None else 0.0
            base = XF_DISSOLVE if tipo[i] == "dissolve" else XF_CORTE
            d = base if dif < 6 else max(base, 0.6) if dif < 12 else max(base, 1.0)   # margem sobre o critério do verificador (8/15)
            diag[i] = {"fundo_antes": fa, "fundo_depois": fd, "crossfade": d}
        lim = min(B[i - 1] - A[i - 1], B[i] - A[i]) / 3
        ov[i] = q(min(d, lim))
    json.dump(cache_fundo, open(cache_fundo_p, "w", encoding="utf-8"))
    if diag:
        longos = sum(1 for x in diag.values() if x["crossfade"] > XF_DISSOLVE)
        print(f"  emendas com crossfade longo (degrau de som de fundo): {longos} de {len(diag)}", flush=True)

    # ---- gráficos
    overlays = {}
    jogo = plano.get("jogo", "")
    card_titulo(os.path.join(pasta, "cards", "titulo.png"), jogo, ep["titulo_card"] if "titulo_card" in ep
                else ep["titulo"].split("|")[0].strip(), parte)
    ncap = 0
    for i, s in enumerate(segs):
        if s["capitulo"] == "Abertura" or (i and segs[i - 1]["capitulo"] == s["capitulo"]):
            continue
        ncap += 1
        png = os.path.join(pasta, "cards", f"cap{ncap:02d}.png")
        card_capitulo(png, ncap, s["capitulo"])
        if ncap == 1:
            overlays.setdefault(i, []).append((os.path.join(pasta, "cards", "titulo.png"), 0.3, 3.9))
            overlays[i].append((png, 4.5, 7.7))
        else:
            overlays.setdefault(i, []).append((png, 0.8, 4.0))
    for i, s in enumerate(segs):
        for k, tx in enumerate(s.get("textos", [])):
            png = os.path.join(pasta, "cards", f"txt_{i:03d}_{k}.png")
            card_texto(png, tx["texto"])
            overlays.setdefault(i, []).append((png, float(tx["inicio"]), float(tx["fim"])))

    # ---- VÍDEO: corpo de cada trecho + clipes de dissolve
    pedacos = []

    def render_video(out, a, d, ovl, zooms, rel0):
        """a = início na fonte; d = duração; rel0 = deslocamento do início em relação ao trecho"""
        nq = int(round(d * FPS))
        if nq <= 0:
            return None
        iv = censura_em(a, d)
        if iv:
            out = out[:-4] + sufixo_censura(iv) + ".mp4"
        if os.path.exists(out):
            return out
        cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-ss", f"{a:.4f}", "-i", SRC]
        g = [f"[0:v]fps={FPS},scale={W}:{H},setsar=1,setpts=PTS-STARTPTS[v0]"]
        cur = "[v0]"
        if zooms:
            zz = [{**z, "inicio": z["inicio"] - rel0, "fim": z["fim"] - rel0} for z in zooms
                  if z["fim"] - rel0 > 0 and z["inicio"] - rel0 < d]
            if zz:
                g.append(f"{cur}{zoom_filtro(zz)}[vz]")
                cur = "[vz]"
        if iv:
            g += censura_filtro(cur, "[vcz]", iv, "cz")
            cur = "[vcz]"
        for k, (png, t0, t1) in enumerate(ovl):
            t0, t1 = t0 - rel0, min(t1 - rel0, d - 0.1)
            if t1 <= 0.2 or t0 >= d:
                continue
            cmd += ["-loop", "1", "-framerate", str(FPS), "-t", f"{d:.3f}", "-i", png]
            idx = cmd.count("-i") - 1
            g.append(f"[{idx}:v]format=rgba,fade=t=in:st={max(t0, 0):.2f}:d=0.4:alpha=1,"
                     f"fade=t=out:st={t1 - 0.4:.2f}:d=0.4:alpha=1[o{k}]")
            g.append(f"{cur}[o{k}]overlay=0:0:enable='between(t,{t0:.2f},{t1:.2f})'[w{k}]")
            cur = f"[w{k}]"
        g.append(f"{cur}format=yuv420p[vout]")
        run(cmd + ["-filter_complex", ";".join(g), "-map", "[vout]", "-an", "-frames:v", str(nq),
                   *VENC, "-r", str(FPS), out])
        return out

    for i in range(n):
        ini, fim = A[i], B[i]
        # início do corpo
        if tipo[i] == "corte":
            c0 = ini + q(ov[i] / 2)
        elif tipo[i] == "dissolve":
            c0 = ini + ov[i]
        else:
            c0 = ini
        # fim do corpo
        if i + 1 < n and tipo[i + 1] == "corte":
            c1 = fim - (ov[i + 1] - q(ov[i + 1] / 2))
        elif i + 1 < n and tipo[i + 1] == "dissolve":
            c1 = fim - ov[i + 1]
        else:
            c1 = fim
        if tipo[i] == "dissolve":
            ia_, ib_ = censura_em(B[i - 1] - ov[i], ov[i] + 0.5), censura_em(ini, ov[i] + 0.5)
            outd = os.path.join(pasta, "v", f"{i:03d}_dissolve_{round(ini * FPS)}_{round(ov[i] * FPS)}"
                                f"{sufixo_censura(ia_ + ib_)}.mp4")
            nq = int(round(ov[i] * FPS))
            if not os.path.exists(outd):
                run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                     "-ss", f"{B[i - 1] - ov[i]:.4f}", "-t", f"{ov[i] + 0.5:.3f}", "-i", SRC,
                     "-ss", f"{ini:.4f}", "-t", f"{ov[i] + 0.5:.3f}", "-i", SRC, "-filter_complex",
                     ";".join([f"[0:v]fps={FPS},scale={W}:{H},setsar=1,setpts=PTS-STARTPTS[a0]",
                               *censura_filtro("[a0]", "[a1]", ia_, "da"), "[a1]format=yuv420p[a]",
                               f"[1:v]fps={FPS},scale={W}:{H},setsar=1,setpts=PTS-STARTPTS[b0]",
                               *censura_filtro("[b0]", "[b1]", ib_, "db"), "[b1]format=yuv420p[b]",
                               f"[a][b]xfade=transition=fade:duration={ov[i]:.4f}:offset=0[x]"]),
                     "-map", "[x]", "-frames:v", str(nq), *VENC, "-r", str(FPS), outd])
            pedacos.append(outd)
        out = os.path.join(pasta, "v", f"{i:03d}_{round(c0 * FPS)}_{round(c1 * FPS)}.mp4")   # cache por tempo exato
        p = render_video(out, c0, c1 - c0, overlays.get(i, []), segs[i].get("zooms", []), c0 - ini)
        if p:
            pedacos.append(p)
        print(f"  parte {parte} [{i + 1}/{n}] {segs[i]['capitulo']} | {fim - ini:.1f}s | {tipo[i]}", flush=True)

    # ---- encerramento: vídeo animado (ex.: tiojoao_animado.mp4) ou IMAGEM 16:9 (tela final por jogo, ex.:
    # Estilo/encerramento_gta6.png) exibida por "duracao" s com aproximação lenta. Sempre entra com
    # dissolve de 0,5 s sobre o último quadro do episódio; o som do jogo some em 0,5 s.
    enc = plano.get("encerramento")
    dur_enc = 0.0
    if enc and not args.so:
        img = os.path.splitext(enc["arquivo"])[1].lower() in (".png", ".jpg", ".jpeg", ".webp")
        if img:
            dur_enc = q(float(enc.get("duracao", 10.0)))
        else:   # o xfade de 0,5 s sobre o último quadro rende exatamente a duração do cartão
            dur_enc = q(float(run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                   enc["arquivo"]]).stdout.strip()))
        base_enc = os.path.splitext(os.path.basename(enc["arquivo"]))[0]
        oute = os.path.join(pasta, "v", f"zz_enc_{base_enc}_{round(dur_enc * FPS)}_{round(B[-1] * FPS)}.mp4")
        iv_fim = [(0.0, 99.0)] if censura_em(B[-1] - 0.05, 0.1) else []
        if iv_fim:
            oute = oute[:-4] + "_c.mp4"
        if not os.path.exists(oute):
            ult = B[-1]
            nq = int(round(dur_enc * FPS))
            if img:
                entrada = ["-loop", "1", "-framerate", str(FPS), "-t", f"{dur_enc + 1:.3f}", "-i", enc["arquivo"]]
                card = (f"[1:v]scale={W * 2}:{H * 2}:flags=lanczos,setsar=1,"
                        f"zoompan=z='1+0.04*on/{nq}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:"
                        f"s={W}x{H}:fps={FPS},format=yuv420p,setpts=PTS-STARTPTS[card]")
            else:
                entrada = ["-i", enc["arquivo"]]
                card = (f"[1:v]fps={FPS},split[c1][c2];[c1]scale={W}:-2,crop={W}:{H},gblur=sigma=40,"
                        f"eq=brightness=-0.25[cb];[c2]scale=-2:{H}[cf];[cb][cf]overlay=(W-w)/2:0,setsar=1,"
                        f"format=yuv420p,setpts=PTS-STARTPTS[card]")
            run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-ss", f"{ult - 0.05:.3f}",
                 "-i", SRC, *entrada, "-filter_complex",
                 f"[0:v]fps={FPS},scale={W}:{H},setsar=1,trim=end_frame=1,loop=loop=-1:size=1[lf0];"
                 + ";".join(censura_filtro("[lf0]", "[lf1]", iv_fim, "ec")) + ";[lf1]"
                 f"trim=duration=0.5,setpts=PTS-STARTPTS,format=yuv420p[last];{card};"
                 f"[last][card]xfade=transition=fade:duration=0.5:offset=0[x]",
                 "-map", "[x]", "-frames:v", str(nq), *VENC, "-r", str(FPS), oute])
        pedacos.append(oute)

    # ---- onde cada emenda cai no episódio final (para o verificador)
    juncoes, acum = [], 0.0
    for i in range(n):
        if i:
            acum -= ov[i]
            if tipo[i] != "continuo":
                juncoes.append({"trecho": i, "tipo": tipo[i], "t": round(acum + ov[i] / 2, 3), "crossfade": ov[i],
                                "origem_de": B[i - 1], "origem_para": A[i], "capitulo": segs[i]["capitulo"]})
        acum += B[i] - A[i]
    json.dump({"parte": parte, "duracao_prevista": round(acum + dur_enc, 3), "duracao_encerramento": dur_enc,
               "juncoes": juncoes,
               "capitulos": ep.get("capitulos", [])},
              open(os.path.join(pasta, "juncoes.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    lst = os.path.join(pasta, "video.txt")
    with open(lst, "w", encoding="utf-8") as f:
        for p in pedacos:
            f.write(f"file '{os.path.abspath(p)}'\n")
    vid = os.path.join(pasta, "video.mp4")
    run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst,
         "-c", "copy", vid])

    # ---- ÁUDIO: trilha única com acrossfade em todas as junções
    # cada trecho é lido com a duração cheia; a sobreposição ov[i] é consumida pelo acrossfade
    # (o vídeo já descontou exatamente o mesmo tempo).
    blocos = []      # cadeias de trechos contínuos viram 1 input só
    for i in range(n):
        if i and tipo[i] == "continuo":
            blocos[-1]["fim"] = B[i]
        else:
            blocos.append({"ini": A[i], "fim": B[i], "ov": ov[i]})
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y"]
    for b in blocos:
        cmd += ["-ss", f"{b['ini']:.4f}", "-t", f"{b['fim'] - b['ini']:.4f}", "-i", SRC]
    g = []
    for k in range(len(blocos)):
        g.append(f"[{k}:a]aresample=48000,aformat=channel_layouts=stereo,asetpts=PTS-STARTPTS[a{k}]")
    cur = "[a0]"
    for k in range(1, len(blocos)):
        g.append(f"{cur}[a{k}]acrossfade=d={blocos[k]['ov']:.4f}:c1=tri:c2=tri[x{k}]")
        cur = f"[x{k}]"
    if dur_enc:
        g.append(f"{cur}afade=t=out:st={sum(b['fim'] - b['ini'] for b in blocos) - sum(b['ov'] for b in blocos[1:]) - 0.5:.3f}:d=0.5,"
                 f"apad=pad_dur={dur_enc:.3f}[af]")
        cur = "[af]"
    aud = os.path.join(pasta, "audio.wav")
    lst_a = os.path.join(pasta, "audio_filtro.txt")
    open(lst_a, "w", encoding="utf-8").write(";".join(g))
    run(cmd + ["-/filter_complex", lst_a, "-map", cur, "-c:a", "pcm_s16le", aud])

    # ---- normaliza (-14 LUFS, 2 passagens) e junta
    r = run(["ffmpeg", "-hide_banner", "-i", aud, "-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json",
             "-f", "null", "-"])
    m = json.loads(r.stderr[r.stderr.rfind("{"):r.stderr.rfind("}") + 1])
    ln = (f"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
          f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
    saida = ep["arquivo"]
    os.makedirs(os.path.dirname(saida), exist_ok=True)
    run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", vid, "-i", aud, "-map", "0:v", "-map", "1:a",
         "-c:v", "copy", "-af", ln + ",aresample=48000", *AENC, "-shortest", "-movflags", "+faststart", saida])
    dv = float(run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=duration", "-of",
                    "csv=p=0", saida]).stdout.strip() or 0)
    da = float(run(["ffprobe", "-v", "error", "-select_streams", "a:0", "-show_entries", "stream=duration", "-of",
                    "csv=p=0", saida]).stdout.strip() or 0)
    print(f"Parte {parte} pronta: {saida} | vídeo {dv / 60:.2f} min | áudio {da / 60:.2f} min | dif {abs(dv - da):.3f}s")


for ep in plano["episodios"]:
    if args.parte and ep["parte"] != args.parte:
        continue
    if not args.parte and ep.get("status", plano.get("status")) != "aprovado" and not args.ignorar_status:
        print(f"Parte {ep['parte']} não aprovada, pulando.")
        continue
    montar(ep)

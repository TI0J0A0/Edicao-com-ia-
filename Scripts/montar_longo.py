"""Monta um vídeo LONGO horizontal (1920x1080, 60 fps) a partir de um plano aprovado com
"montagem" (lista de trechos do original) e "capitulos".

- Cada trecho é recortado do original e recodificado (h264_amf), com micro-fades de áudio
  para não estalar nos cortes.
- Título depois do gancho e títulos de capítulo discretos (PNG gerado com Pillow, Montserrat).
- Último trecho emenda no Estilo/tiojoao_animado.mp4 com crossfade de 0,5 s.
- Junta tudo sem recodificar e normaliza o áudio para -14 LUFS (padrão YouTube).

Uso: python Scripts/montar_longo.py --plano Trabalho/plano_coletor.json --saida "Final/x.mp4"
     [--pasta Trabalho/longo_coletor] [--so N]   (--so N renderiza só os N primeiros, p/ teste)
"""
import argparse
import json
import os
import re
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(RAIZ)
ap = argparse.ArgumentParser()
ap.add_argument("--plano", required=True)
ap.add_argument("--saida", required=True)
ap.add_argument("--pasta", default="Trabalho/longo_coletor")
ap.add_argument("--so", type=int, default=0)
ap.add_argument("--titulo", default="Coletor de Marionetes")
ap.add_argument("--jogo", default="Phantom Blade Zero")
args = ap.parse_args()

plano = json.load(open(args.plano, encoding="utf-8"))
if plano.get("status") != "aprovado":
    sys.exit("O plano ainda não foi aprovado.")
SRC = plano["video"]
segs = plano["montagem"]
W, H, FPS = 1920, 1080, 60
FONTE = "Scripts/fonts/Montserrat-Bold.otf"
RED, ICE, BLACK = (220, 38, 38), (245, 245, 245), (17, 17, 17)
os.makedirs(f"{args.pasta}/segs", exist_ok=True)
os.makedirs(f"{args.pasta}/cards", exist_ok=True)

VENC = ["-c:v", "h264_amf", "-quality", "quality", "-rc", "cqp",
        "-qp_i", "18", "-qp_p", "20", "-qp_b", "22", "-g", "120", "-pix_fmt", "yuv420p"]
AENC = ["-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2"]


def fonte(px):
    return ImageFont.truetype(FONTE, px)


def texto_espacado(dr, xy, txt, f, cor, esp):
    x, y = xy
    for ch in txt:
        dr.text((x, y), ch, font=f, fill=cor)
        x += dr.textlength(ch, font=f) + esp
    return x


def largura_espacada(dr, txt, f, esp):
    return sum(dr.textlength(c, font=f) + esp for c in txt) - esp


def card_titulo(caminho):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    # faixa escura com bordas suaves no meio da tela
    faixa = Image.new("L", (1, H), 0)
    for y in range(H):
        d = abs(y - H / 2) / (H / 2)
        faixa.putpixel((0, y), int(200 * max(0.0, 1 - d * 1.35) ** 0.8))
    escuro = Image.new("RGBA", (W, H), BLACK + (0,))
    escuro.putalpha(faixa.resize((W, H)))
    im = Image.alpha_composite(im, escuro)
    dr = ImageDraw.Draw(im)
    f1, f2 = fonte(34), fonte(104)
    jogo = args.jogo.upper()
    wj = largura_espacada(dr, jogo, f1, 10)
    texto_espacado(dr, ((W - wj) / 2, 418), jogo, f1, ICE + (230,), 10)
    tit = args.titulo.upper()
    wt = dr.textlength(tit, font=f2)
    dr.text(((W - wt) / 2 + 3, 478 + 4), tit, font=f2, fill=(0, 0, 0, 150))
    dr.text(((W - wt) / 2, 478), tit, font=f2, fill=RED + (255,))
    dr.rectangle(((W - 120) / 2, 626, (W + 120) / 2, 631), fill=ICE + (230,))
    im.save(caminho)


def card_capitulo(caminho, n, titulo):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    f1, f2 = fonte(22), fonte(46)
    rot = f"CAPÍTULO {n}"
    w = max(largura_espacada(dr, rot, f1, 6), dr.textlength(titulo, font=f2))
    x0, y0 = 72, 772
    dr.rectangle((x0, y0, x0 + w + 64, y0 + 112), fill=BLACK + (200,))
    dr.rectangle((x0, y0, x0 + 8, y0 + 112), fill=RED + (255,))
    texto_espacado(dr, (x0 + 32, y0 + 18), rot, f1, RED + (255,), 6)
    dr.text((x0 + 32, y0 + 46), titulo, font=f2, fill=ICE + (255,))
    im.save(caminho)


def card_tempo(caminho, txt):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    f = fonte(30)
    w = dr.textlength(txt, font=f)
    x0, y0 = 72, 800
    dr.rectangle((x0, y0, x0 + w + 48, y0 + 60), fill=BLACK + (190,))
    dr.rectangle((x0, y0, x0 + 6, y0 + 60), fill=RED + (255,))
    dr.text((x0 + 26, y0 + 12), txt, font=f, fill=ICE + (255,))
    im.save(caminho)


# ---------- quais trechos recebem gráficos
overlays = {}   # índice do trecho -> lista de (png, inicio, fim) em segundos relativos ao trecho
card_titulo(f"{args.pasta}/cards/titulo.png")
n_cap = 0
for i, s in enumerate(segs):
    novo = i == 0 or segs[i - 1]["capitulo"] != s["capitulo"]
    if s["capitulo"] == "Abertura" or not novo:
        continue
    n_cap += 1
    png = f"{args.pasta}/cards/cap{n_cap:02d}.png"
    card_capitulo(png, n_cap, s["capitulo"])
    if n_cap == 1:   # logo depois do gancho: título do episódio e, em seguida, o capítulo
        overlays.setdefault(i, []).append((f"{args.pasta}/cards/titulo.png", 0.0, 3.6))
        overlays[i].append((png, 4.2, 7.4))
    else:
        overlays.setdefault(i, []).append((png, 0.6, 3.8))
for i, s in enumerate(segs):
    if re.search(r"sonzinho de chuva", s["motivo"]):
        card_tempo(f"{args.pasta}/cards/tempo.png", "alguns minutos depois…")
        overlays.setdefault(i, []).append((f"{args.pasta}/cards/tempo.png", 0.0, 2.6))

FADE_A = 0.025
lista = []
total = len(segs) if not args.so else min(args.so, len(segs))
for i, s in enumerate(segs[:total]):
    a, b = s["origem_inicio"], s["origem_fim"]
    dur = b - a
    out = f"{args.pasta}/segs/{i:03d}.mp4"
    lista.append(out)
    ultimo = i == len(segs) - 1
    if os.path.exists(out) and not ultimo:
        continue
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-ss", f"{a:.3f}", "-t", f"{dur:.3f}", "-i", SRC]
    g, vin = [], "[0:v]"
    g.append(f"{vin}fps={FPS},scale={W}:{H},setsar=1[v0]")
    cur = "[v0]"
    for k, (png, t0, t1) in enumerate(overlays.get(i, [])):
        t1 = min(t1, dur - 0.1)
        cmd += ["-loop", "1", "-framerate", str(FPS), "-t", f"{dur:.3f}", "-i", png]
        idx = k + 1
        g.append(f"[{idx}:v]format=rgba,fade=t=in:st={t0:.2f}:d=0.4:alpha=1,"
                 f"fade=t=out:st={t1 - 0.4:.2f}:d=0.4:alpha=1[o{k}]")
        g.append(f"{cur}[o{k}]overlay=0:0:enable='between(t,{t0:.2f},{t1:.2f})'[v{k + 1}]")
        cur = f"[v{k + 1}]"
    if ultimo:
        cd, xf = float(plano["encerramento"]["duracao"]), 0.5
        g.append(f"[0:a]afade=t=in:d={FADE_A},afade=t=out:st={dur - xf:.3f}:d={xf},"
                 f"apad=whole_dur={dur - xf + cd:.3f}[a]")
    else:
        g.append(f"[0:a]afade=t=in:d={FADE_A},afade=t=out:st={dur - FADE_A:.3f}:d={FADE_A}[a]")
    if ultimo:
        # emenda com o cartão animado (vertical): centralizado sobre ele mesmo desfocado
        cmd += ["-i", plano["encerramento"]["arquivo"]]
        ci = len(overlays.get(i, [])) + 1
        g.append(f"[{ci}:v]fps={FPS},split[c1][c2]")
        g.append(f"[c1]scale={W}:-2,crop={W}:{H},gblur=sigma=40,eq=brightness=-0.25[cb]")
        g.append(f"[c2]scale=-2:{H}[cf]")
        g.append(f"[cb][cf]overlay=(W-w)/2:0,setsar=1,format=yuv420p,settb=1/{FPS}[card]")
        g.append(f"{cur}format=yuv420p,settb=1/{FPS}[vl]")
        g.append(f"[vl][card]xfade=transition=fade:duration={xf}:offset={dur - xf:.3f}[vout]")
        cur = "[vout]"
    else:
        g.append(f"{cur}format=yuv420p[vout]")
        cur = "[vout]"
    cmd += ["-filter_complex", ";".join(g), "-map", cur, "-map", "[a]", *VENC, *AENC, "-r", str(FPS), out]
    print(f"[{i + 1}/{total}] {s['capitulo']} | {dur:.1f}s", flush=True)
    subprocess.run(cmd, check=True)

# ---------- junta e normaliza
lst = f"{args.pasta}/lista.txt"
with open(lst, "w", encoding="utf-8") as f:
    for p in lista:
        f.write(f"file '{os.path.abspath(p)}'\n")
junto = f"{args.pasta}/junto.mp4"
subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0",
                "-i", lst, "-c", "copy", junto], check=True)
print("Medindo volume…", flush=True)
r = subprocess.run(["ffmpeg", "-hide_banner", "-i", junto, "-vn", "-af",
                    "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
                   capture_output=True, text=True, encoding="utf-8", errors="ignore")
m = json.loads(r.stderr[r.stderr.rfind("{"):r.stderr.rfind("}") + 1])
ln = (f"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
      f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
os.makedirs(os.path.dirname(args.saida), exist_ok=True)
subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-stats", "-y", "-i", junto,
                "-c:v", "copy", "-af", ln, *AENC, "-movflags", "+faststart", args.saida], check=True)
print("Pronto:", args.saida)


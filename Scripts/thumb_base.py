"""Imagem-base de thumbnail para cada episódio de uma série (regra do João, 2026-11-22: todo episódio sai
com título + imagem de qualidade ligada ao título, para ele montar a thumbnail por cima).

O plano traz, por episódio, "thumb": [{"origem": seg, "nota": "..."}, ...] — momentos escolhidos olhando os
painéis de candidatos (o primeiro é o principal). Para cada momento o script varre ±1 s da FONTE em resolução
cheia (15 quadros/s), mede a nitidez de cada quadro (variância das bordas) e salva o mais nítido em PNG
sem perda — evita quadro borrado de movimento.

Uso: python Scripts/thumb_base.py --plano Trabalho/plano_x.json [--parte N]
Saída: videos_longos/<Jogo>/<Jogo> - Parte NN - thumb base[ 2].png
"""
import argparse
import json
import os
import shutil
import subprocess
import tempfile

from PIL import Image, ImageFilter, ImageStat

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(RAIZ)
ap = argparse.ArgumentParser()
ap.add_argument("--plano", required=True)
ap.add_argument("--parte", type=int, default=0)
ap.add_argument("--janela", type=float, default=1.0, help="segundos para cada lado do momento")
a = ap.parse_args()
plano = json.load(open(a.plano, encoding="utf-8"))
SRC = plano["video"]


def nitidez(caminho):
    im = Image.open(caminho).convert("L")
    im = im.resize((im.width // 2, im.height // 2))
    return ImageStat.Stat(im.filter(ImageFilter.FIND_EDGES)).var[0]


def melhor_quadro(t, saida):
    tmp = tempfile.mkdtemp(prefix="thumb_")
    try:
        ini = max(0.0, t - a.janela)
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-ss", f"{ini:.3f}", "-i", SRC,
                        "-t", f"{2 * a.janela:.3f}", "-vf", "fps=15,format=yuvj420p", "-q:v", "2",
                        os.path.join(tmp, "q_%03d.jpg")], check=True)
        qs = sorted(os.listdir(tmp))
        notas = [(nitidez(os.path.join(tmp, q)), k) for k, q in enumerate(qs)]
        _, k = max(notas)
        tk = ini + k / 15
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-ss", f"{tk:.3f}", "-i", SRC,
                        "-frames:v", "1", "-pix_fmt", "rgb24", saida], check=True)
        return tk
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def hms(x):
    x = int(x)
    return f"{x // 3600}:{x % 3600 // 60:02d}:{x % 60:02d}"


for ep in plano["episodios"]:
    if a.parte and ep["parte"] != a.parte:
        continue
    pasta = os.path.dirname(ep["arquivo"])
    nome = os.path.splitext(os.path.basename(ep["arquivo"]))[0]
    for i, m in enumerate(ep.get("thumb", [])):
        out = os.path.join(pasta, f"{nome} - thumb base{'' if i == 0 else f' {i + 1}'}.png")
        tk = melhor_quadro(float(m["origem"]), out)
        print(f"Parte {ep['parte']}: {out}  (live {hms(tk)} — {m.get('nota', '')})", flush=True)

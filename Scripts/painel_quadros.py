"""Gera painéis (contact sheets) de uma live longa para análise visual: 1 quadro a cada --cada
segundos, em grade --cols x --lins, com o tempo da live escrito em cada quadro.
Use um proxy leve (ex.: versão 160p/360p da Twitch) — o original fica só para o render.
Painéis já gerados são pulados (cache).

Uso: python Scripts/painel_quadros.py <video> <pasta_saida> [--cada 30] [--cols 8] [--lins 5] [--largura 284]
Saída: <pasta>/painel_000.jpg ... (cada painel cobre cada*cols*lins segundos)
"""
import argparse
import concurrent.futures as cf
import os
import subprocess

ap = argparse.ArgumentParser()
ap.add_argument("video")
ap.add_argument("saida")
ap.add_argument("--cada", type=float, default=30)
ap.add_argument("--cols", type=int, default=8)
ap.add_argument("--lins", type=int, default=5)
ap.add_argument("--largura", type=int, default=284)
ap.add_argument("--paralelo", type=int, default=4)
a = ap.parse_args()
os.makedirs(a.saida, exist_ok=True)
dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                            a.video], capture_output=True, text=True).stdout.strip())
janela = a.cada * a.cols * a.lins
FONTE = "C\\:/Windows/Fonts/arialbd.ttf"


def painel(i):
    ini = i * janela
    out = os.path.join(a.saida, f"painel_{i:03d}.jpg")
    if os.path.exists(out):
        return out
    # tempo da live = ini + t do recorte; drawtext usa pts com offset
    vf = (f"fps=1/{a.cada},scale={a.largura}:-2,"
          f"drawtext=fontfile='{FONTE}':text='%{{pts\\:hms\\:{ini:.0f}}}':x=4:y=4:fontsize=18:"
          f"fontcolor=yellow:box=1:boxcolor=black@0.7,"
          f"tile={a.cols}x{a.lins}:padding=2:color=black,format=yuvj420p")
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-ss", f"{ini:.2f}", "-t", f"{janela:.2f}",
                    "-i", a.video, "-vf", vf, "-frames:v", "1", "-q:v", "4", out], check=True)
    return out


n = int(dur // janela) + (1 if dur % janela > a.cada else 0)
with cf.ThreadPoolExecutor(a.paralelo) as ex:
    for p in ex.map(painel, range(n)):
        pass
print(f"{n} painéis ({janela / 60:.0f} min cada) em {a.saida}")

"""Transcrição minuto a minuto ("H:MM | frase / frase / ...") para mapear uma live longa.
Funciona com a transcrição final (<nome>_transcricao.json) OU com a pasta de blocos do transcrever_longo.py
ainda em andamento (usa os blocos prontos; cada bloco = --bloco minutos).

Uso: python Scripts/transcricao_por_minuto.py <transcricao.json | pasta_blocos> <saida.txt> [--bloco 30]
"""
import argparse
import glob
import json
import os
import re

ap = argparse.ArgumentParser()
ap.add_argument("entrada")
ap.add_argument("saida")
ap.add_argument("--bloco", type=float, default=30)
a = ap.parse_args()

frases = []
if os.path.isdir(a.entrada):
    for f in sorted(glob.glob(os.path.join(a.entrada, "bloco_*_transcricao.json"))):
        k = int(re.search(r"bloco_(\d+)_", os.path.basename(f)).group(1))
        off = k * a.bloco * 60
        for fr in json.load(open(f, encoding="utf-8"))["frases"]:
            frases.append((fr["inicio"] + off, fr["texto"].strip()))
else:
    frases = [(fr["inicio"], fr["texto"].strip()) for fr in json.load(open(a.entrada, encoding="utf-8"))["frases"]]

por_min = {}
for t, tx in sorted(frases):
    if tx:
        por_min.setdefault(int(t // 60), []).append(tx)
with open(a.saida, "w", encoding="utf-8") as f:
    for m in sorted(por_min):
        f.write(f"{m // 60}:{m % 60:02d} | {' / '.join(por_min[m])}\n")
print(f"{len(por_min)} minutos com fala -> {a.saida}")

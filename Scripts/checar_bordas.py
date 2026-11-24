"""Confere um plano pronto: nenhuma borda de corte pode cair no meio de fala / diálogo do jogo.

Uso: python Scripts/checar_bordas.py <plano.json> <transcricao.json> [audio_da_fonte]
Se acusar algo: corrigir no gerador do plano (usar Bordas.inicio/Bordas.fim) e gerar de novo.
Rodar ANTES de renderizar. Bordas coladas na fonte (trecho contínuo) não são cortes e são ignoradas.
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bordas import Bordas  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("plano")
ap.add_argument("transcricao")
ap.add_argument("audio", nargs="?")
a = ap.parse_args()
P = json.load(open(a.plano, encoding="utf-8"))
B = Bordas(a.transcricao, a.audio)


def hms(s):
    s = float(s)
    return f"{int(s // 3600)}:{int(s % 3600 // 60):02d}:{s % 60:05.2f}"


ruins = 0
for ep in P["episodios"]:
    M = ep["montagem"]
    for i, s in enumerate(M):
        colado_antes = i > 0 and abs(s["origem_inicio"] - M[i - 1]["origem_fim"]) < 0.05
        colado_depois = i + 1 < len(M) and abs(M[i + 1]["origem_inicio"] - s["origem_fim"]) < 0.05
        final = i == len(M) - 1
        for lado, chave, colado in (("ini", "origem_inicio", colado_antes), ("fim", "origem_fim", colado_depois)):
            if colado or (lado == "ini" and i == 0 and s[chave] < 1):
                continue
            x = s[chave]
            prob = B.problema(x, lado)
            if not prob and lado == "fim" and B._prox_inicio(x) - x < (1.2 if final else 0.4):
                prob = f"fala recomeça {B._prox_inicio(x) - x:.2f}s depois do corte (conversa cortada)"
            if prob:
                novo = B.inicio(x) if lado == "ini" else B.fim(x, final=final)
                if prob:
                    ruins += 1
                    print(f"Parte {ep['parte']} trecho {i + 1} {lado} {hms(x)}: {prob} -> sugerido {hms(novo)}")
print(f"{ruins} borda(s) cortando fala")
raise SystemExit(1 if ruins else 0)

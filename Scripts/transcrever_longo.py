"""Transcreve uma live LONGA (horas) em blocos, em paralelo e com cache.

- Corta o áudio em blocos de --bloco minutos (WAV 16 kHz mono), cada um transcrito pelo
  .claude/skills/transcricao/scripts/transcrever.py em um processo separado.
- Blocos já transcritos são pulados (retoma de onde parou se cair no meio).
- No fim junta tudo num único <nome>_transcricao.json/.txt/.srt com os tempos da live original,
  no mesmo formato da skill de transcrição (frases, palavras, pausas, duracao).

Uso: python Scripts/transcrever_longo.py <audio_ou_video> <pasta_cache> <pasta_saida>
         [--nome NOME] [--bloco 30] [--paralelo 3] [--modelo turbo]
"""
import argparse
import concurrent.futures as cf
import json
import os
import subprocess
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRANSCREVER = os.path.join(RAIZ, ".claude", "skills", "transcricao", "scripts", "transcrever.py")
PY = os.path.join(os.environ["USERPROFILE"], "whisper-env", "Scripts", "python.exe")

ap = argparse.ArgumentParser()
ap.add_argument("arquivo")
ap.add_argument("cache")
ap.add_argument("saida")
ap.add_argument("--nome", default=None)
ap.add_argument("--bloco", type=float, default=30.0, help="minutos por bloco")
ap.add_argument("--paralelo", type=int, default=3)
ap.add_argument("--modelo", default="turbo")
ap.add_argument("--pausa", type=float, default=0.7)
a = ap.parse_args()

nome = a.nome or os.path.splitext(os.path.basename(a.arquivo))[0]
os.makedirs(a.cache, exist_ok=True)
os.makedirs(a.saida, exist_ok=True)

dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                            a.arquivo], capture_output=True, text=True).stdout.strip())
passo = a.bloco * 60
blocos = []
t = 0.0
while t < dur - 1:
    blocos.append((len(blocos), t, min(passo, dur - t)))
    t += passo
threads = max(1, (os.cpu_count() or 4) // a.paralelo)
print(f"{nome}: {dur / 3600:.2f} h em {len(blocos)} blocos de {a.bloco:.0f} min, "
      f"{a.paralelo} em paralelo ({threads} threads cada)", flush=True)


def fazer(b):
    i, ini, d = b
    wav = os.path.join(a.cache, f"bloco_{i:03d}.wav")
    js = os.path.join(a.cache, f"bloco_{i:03d}_transcricao.json")
    if os.path.exists(js):
        return i, "cache"
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-ss", f"{ini:.3f}", "-t", f"{d:.3f}",
                    "-i", a.arquivo, "-vn", "-ac", "1", "-ar", "16000", wav], check=True)
    log = open(os.path.join(a.cache, f"bloco_{i:03d}.log"), "w", encoding="utf-8")
    r = subprocess.run([PY, TRANSCREVER, wav, a.cache, "--modelo", a.modelo, "--pausa", str(a.pausa),
                        "--threads", str(threads)], stdout=log, stderr=subprocess.STDOUT,
                       env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    log.close()
    if r.returncode != 0 or not os.path.exists(js):
        return i, f"ERRO (veja bloco_{i:03d}.log)"
    os.remove(wav)
    return i, "ok"


with cf.ThreadPoolExecutor(a.paralelo) as ex:
    for i, st in ex.map(fazer, blocos):
        print(f"  bloco {i + 1}/{len(blocos)}: {st}", flush=True)

falta = [i for i, _, _ in blocos if not os.path.exists(os.path.join(a.cache, f"bloco_{i:03d}_transcricao.json"))]
if falta:
    sys.exit(f"Blocos sem transcrição: {falta}. Rode de novo para tentar só esses.")

# ---------- junta com os tempos da live
frases, palavras = [], []
for i, ini, _ in blocos:
    d = json.load(open(os.path.join(a.cache, f"bloco_{i:03d}_transcricao.json"), encoding="utf-8"))
    for fr in d["frases"]:
        ws = [{"inicio": round(w["inicio"] + ini, 2), "fim": round(w["fim"] + ini, 2), "palavra": w["palavra"]}
              for w in fr["palavras"]]
        palavras.extend(ws)
        frases.append({"id": len(frases) + 1, "inicio": round(fr["inicio"] + ini, 2),
                       "fim": round(fr["fim"] + ini, 2), "texto": fr["texto"], "palavras": ws})
pausas = []
for p, q in zip(palavras, palavras[1:]):
    gap = q["inicio"] - p["fim"]
    if gap >= a.pausa:
        pausas.append({"inicio": p["fim"], "fim": q["inicio"], "duracao": round(gap, 2),
                       "depois_de": p["palavra"], "antes_de": q["palavra"]})


def ts(seg, sep="."):
    return f"{int(seg // 3600):02d}:{int(seg % 3600 // 60):02d}:{seg % 60:06.3f}".replace(".", sep)


base = os.path.join(a.saida, f"{nome}_transcricao")
json.dump({"arquivo": os.path.abspath(a.arquivo), "idioma": "pt", "duracao": round(dur, 2), "modelo": a.modelo,
           "blocos_min": a.bloco, "frases": frases, "pausas": pausas},
          open(base + ".json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
with open(base + ".txt", "w", encoding="utf-8") as f:
    for fr in frases:
        f.write(f"[{ts(fr['inicio'])} -> {ts(fr['fim'])}] {fr['texto']}\n")
with open(base + ".srt", "w", encoding="utf-8") as f:
    for fr in frases:
        f.write(f"{fr['id']}\n{ts(fr['inicio'], ',')} --> {ts(fr['fim'], ',')}\n{fr['texto']}\n\n")
print(f"Pronto: {len(frases)} frases, {len(pausas)} pausas -> {base}.json/.txt/.srt")

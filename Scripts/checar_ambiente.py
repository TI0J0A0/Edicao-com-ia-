"""Valida as dependências ANTES de começar uma live (V4): falha cedo em vez de quebrar na hora 3 do render.

Uso: python Scripts/checar_ambiente.py      (código de saída 1 se faltar algo obrigatório)
"""
import importlib.util
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import comum  # noqa: E402

ok, falhas, avisos = [], [], []


def item(cond, msg, obrigatorio=True):
    (ok if cond else (falhas if obrigatorio else avisos)).append(msg)


item(shutil.which("ffmpeg") and shutil.which("ffprobe"), "ffmpeg/ffprobe no PATH")
if shutil.which("ffmpeg"):
    enc = comum.sh(["ffmpeg", "-hide_banner", "-encoders"]).stdout
    item(" h264_amf " in enc, "encoder h264_amf (único que funciona nesta máquina)")
    filtros = comum.sh(["ffmpeg", "-hide_banner", "-filters"]).stdout
    for f in ("freezedetect", "blackdetect", "silencedetect", "ebur128", "loudnorm", "xfade", "acrossfade",
              "astats", "cropdetect", "zoompan", "scdet"):
        item(f" {f} " in filtros, f"filtro ffmpeg {f}")
    t = comum.sh(["ffmpeg", "-hide_banner", "-loglevel", "error", "-f", "lavfi", "-i", "testsrc=s=320x240:d=0.5",
                  "-c:v", "h264_amf", "-f", "null", "-"])
    item(t.returncode == 0, "h264_amf codifica de verdade (teste de 0,5 s)")
item(importlib.util.find_spec("PIL") is not None, f"Pillow no Python do sistema ({sys.executable})")
wenv = os.path.join(os.environ.get("USERPROFILE", ""), "whisper-env", "Scripts")
item(os.path.exists(os.path.join(wenv, "python.exe")), "whisper-env (faster-whisper) para transcrição")
item(os.path.exists(os.path.join(wenv, "yt-dlp.exe")), "yt-dlp no whisper-env", obrigatorio=False)
tr = os.path.join(comum.RAIZ, ".claude", "skills", "transcricao", "scripts", "transcrever.py")
item(os.path.exists(tr), "skill de transcrição (.claude/skills/transcricao)")
item(os.path.exists(os.path.join(comum.SCRIPTS, "fonts", "Montserrat-Bold.otf")), "fonte Montserrat-Bold.otf")
for f in ("projeto.json", "perfis.json"):
    item(os.path.exists(os.path.join(comum.CONFIG, f)), f"config/{f}")
item(os.path.exists(os.path.join(comum.SCRIPTS, "links_processados.json")), "registro de links processados")
item(os.path.exists(os.path.join(comum.SCRIPTS, "memoria_editorial.json")), "memória editorial", obrigatorio=False)
livre = shutil.disk_usage(comum.RAIZ).free / 1e9
item(livre > 60, f"espaço livre {livre:.0f} GB (live de 4–9 h + render pede ~60 GB)", obrigatorio=False)
for p in ("Estilo/encerramento_gta6.png",):
    item(os.path.exists(os.path.join(comum.RAIZ, p)), p, obrigatorio=False)

for m in ok:
    print("  ok  ", m)
for m in avisos:
    print("  AVISO", m)
for m in falhas:
    print("  FALTA", m)
print("AMBIENTE OK" if not falhas else f"{len(falhas)} dependência(s) faltando")
raise SystemExit(1 if falhas else 0)

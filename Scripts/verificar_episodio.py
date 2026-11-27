"""Revisão de qualidade automática de um episódio renderizado por montar_episodios.py.

Verifica:
- arquivo abre e decodifica sem erro (decodificação completa);
- resolução, FPS, codecs, duração de vídeo x áudio (sincronismo);
- trechos pretos (blackdetect) e silêncios longos acidentais (silencedetect);
- saltos bruscos de volume nas emendas (loudness momentânea 1 s antes x 1 s depois);
- gera um painel com os quadros antes/depois de cada emenda para revisão visual;
- TRAVAMENTOS (regra 2026-11-24): quadro inteiro congelado (jogo + facecam) por >= 0,25 s, no FPS nativo —
  pega lag da live e quadro repetido do render. Facecam parada junto = travou de verdade (menu/mapa não conta,
  porque a câmera continua mexendo);
- FALA CORTADA (regra 2026-11-24): energia de voz logo antes de cada emenda e no fim do episódio
  (antes da tela final) — fala ou diálogo do jogo cortado no meio.

Uso: python Scripts/verificar_episodio.py <episodio.mp4> <juncoes.json> [--rapido]
Saída: <pasta do juncoes.json>/qc.json e qc_emendas_*.jpg ; código de saída 1 se houver erro grave.
"""
import argparse
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bordas import energia_voz  # noqa: E402
import comum  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("video")
ap.add_argument("juncoes")
ap.add_argument("--rapido", action="store_true", help="pula a decodificação completa")
ap.add_argument("--esperado-w", type=int, default=1920)
ap.add_argument("--esperado-h", type=int, default=1080)
a = ap.parse_args()
J = json.load(open(a.juncoes, encoding="utf-8"))
pasta = os.path.dirname(a.juncoes)
problemas, avisos = [], []


def sh(cmd):
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="ignore")


# ---- metadados
pr = json.loads(sh(["ffprobe", "-v", "error", "-show_entries",
                    "stream=codec_type,codec_name,width,height,r_frame_rate,duration:format=duration",
                    "-of", "json", a.video]).stdout)
v = next(s for s in pr["streams"] if s["codec_type"] == "video")
au = next((s for s in pr["streams"] if s["codec_type"] == "audio"), None)
dv, da = float(v["duration"]), float(au["duration"]) if au else 0
n, d = map(int, v["r_frame_rate"].split("/"))
fps = n / d
info = {"arquivo": a.video, "resolucao": f"{v['width']}x{v['height']}", "fps": round(fps, 3),
        "video": v["codec_name"], "audio": au["codec_name"] if au else None,
        "duracao_video": round(dv, 3), "duracao_audio": round(da, 3), "duracao_min": round(dv / 60, 2),
        "duracao_prevista": J.get("duracao_prevista")}
if (v["width"], v["height"]) != (a.esperado_w, a.esperado_h):
    problemas.append(f"resolução {info['resolucao']} diferente da esperada")
if not au:
    problemas.append("sem faixa de áudio")
if abs(dv - da) > 0.1:
    problemas.append(f"vídeo e áudio com durações diferentes ({dv:.2f}s x {da:.2f}s)")
if J.get("duracao_prevista") and abs(dv - J["duracao_prevista"]) > 1.0:
    problemas.append(f"duração {dv:.2f}s difere da prevista {J['duracao_prevista']:.2f}s")

# ---- preto, silêncio e loudness em uma passada só de áudio + uma de vídeo
print("Procurando trechos pretos e travamentos…", flush=True)
# Travamento = JOGO parado E FACECAM parada ao mesmo tempo. Medidos separados numa passada só: a facecam é ~6%
# da tela, então no quadro inteiro um menu parado com o João mexendo parecia "congelado" (falso positivo).
CAM = J.get("facecam")
W0, H0 = v["width"], v["height"]
_QC = comum.projeto().get("qc", {})
fz = f"freezedetect=n={_QC.get('ruido_congelado_jogo', 0.002)}:d={_QC.get('congelado_aviso_s', 0.25)}"
fz_cam = f"freezedetect=n={_QC.get('ruido_congelado_cam', 0.0001)}:d={_QC.get('congelado_aviso_s', 0.25)}"


def _meta(nome):
    return (f"metadata=print:key=lavfi.freezedetect.freeze_start:file={nome}s.txt,"
            f"metadata=print:key=lavfi.freezedetect.freeze_end:file={nome}e.txt")


if CAM:
    x, y, w, h = CAM
    fc = (f"[0:v]split=2[g][c];[g]drawbox=x={x}:y={y}:w={w}:h={h}:color=black:t=fill,scale=320:-2,"
          f"blackdetect=d=0.6:pix_th=0.08,{fz},{_meta('qcfz_g')}[go];"
          f"[c]crop={w}:{h}:{x}:{y},format=gray,{fz_cam},{_meta('qcfz_c')}[co];[co]nullsink")
else:
    fc = f"[0:v]scale=320:-2,blackdetect=d=0.6:pix_th=0.08,{fz},{_meta('qcfz_g')}[go]"
r = subprocess.run(["ffmpeg", "-hide_banner", "-i", os.path.abspath(a.video), "-filter_complex", fc, "-map", "[go]",
                    "-an", "-f", "null", "-"], capture_output=True, text=True, encoding="utf-8", errors="ignore",
                   cwd=pasta or ".")
if r.returncode != 0:      # checagem que não roda NÃO pode parecer aprovada
    problemas.append("a checagem de pretos/travamentos não rodou: " + r.stderr.strip()[-200:])
pretos = [(float(x), float(y)) for x, y in re.findall(r"black_start:([\d.]+) black_end:([\d.]+)", r.stderr)]
fim_util = dv - float(J.get("duracao_encerramento") or 0) - 0.6   # tela final é parada/muda de propósito


def _spans(nome):
    def ler(suf):
        arq = os.path.join(pasta or ".", f"{nome}{suf}.txt")
        if not os.path.exists(arq):
            return []
        vals = [float(l.split("=")[1]) for l in open(arq, encoding="utf-8") if "freezedetect.freeze_" in l]
        os.remove(arq)
        return vals
    ini, fim = ler("s"), ler("e")
    return [(x, fim[k] if k < len(fim) else dv) for k, x in enumerate(ini)]


fr_jogo, fr_cam = _spans("qcfz_g"), _spans("qcfz_c")
if CAM:   # interseção: só conta quando os dois param juntos
    fr = [(max(x, x2), min(y, y2)) for x, y in fr_jogo for x2, y2 in fr_cam if min(y, y2) - max(x, x2) >= 0.25]
else:
    fr = fr_jogo
travamentos = []
for x, y in fr:
    if x >= fim_util or any(px <= x <= py for px, py in pretos):   # tela final / tela preta já avisada
        continue
    travamentos.append((round(x, 2), round(y, 2)))
    (problemas if y - x >= 1.0 else avisos).append(
        f"TRAVAMENTO {x:.2f}s–{y:.2f}s ({y - x:.2f}s): {'jogo e facecam parados juntos' if CAM else 'quadro inteiro parado (facecam desconhecida)'}"
        " — lag da live ou render; cortar/cobrir ou re-renderizar")
for x, y in pretos:
    if x > dv - 4:      # o cartão final pode escurecer
        continue
    avisos.append(f"tela preta {x:.1f}s–{y:.1f}s ({y - x:.1f}s) — conferir se é do jogo (loading/cutscene)")

print("Medindo áudio…", flush=True)
r = sh(["ffmpeg", "-hide_banner", "-i", a.video, "-vn", "-af",
        "silencedetect=n=-50dB:d=4,ebur128=metadata=1,ametadata=print:key=lavfi.r128.M:file=-",
        "-f", "null", "-"])
silencios = [(float(x), float(y)) for x, y in
             re.findall(r"silence_start: ([\d.]+)[\s\S]*?silence_end: ([\d.]+)", r.stderr)]
for x, y in silencios:
    if x >= fim_util:
        continue
    avisos.append(f"silêncio {x:.1f}s–{y:.1f}s ({y - x:.1f}s)")
mom = []
for blk in r.stdout.split("frame:")[1:]:
    t = re.search(r"pts_time:([\d.]+)", blk)
    m = re.search(r"lavfi\.r128\.M=(-?[\d.inf]+)", blk)
    if t and m:
        try:
            mom.append((float(t.group(1)), max(-70.0, float(m.group(1)))))
        except ValueError:
            pass


def piso(t0, t1):
    """nível de fundo (percentil 25 da loudness momentânea) — ignora a diferença natural entre fala e pausa,
    que existe em toda emenda feita entre frases, e acusa só degrau real no som do jogo/ambiente."""
    xs = sorted(l for t, l in mom if t0 <= t < t1)
    return xs[len(xs) // 4] if len(xs) >= 8 else None


saltos = []
for j in J["juncoes"]:
    if j.get("crossfade_fixo") and min(piso(j["t"] - 1.0, j["t"]) or 0, piso(j["t"], j["t"] + 1.0) or 0) < -45:
        continue    # emenda DENTRO de silêncio de mapa/menu (ritmo V4.1): a volta do som do jogo é natural, sem degrau
    antes, depois = piso(j["t"] - 3.2, j["t"] - 0.2), piso(j["t"] + 0.2, j["t"] + 3.2)
    if antes is None or depois is None:
        continue
    dif = depois - antes
    j["fundo_antes"], j["fundo_depois"] = round(antes, 1), round(depois, 1)
    cf = float(j.get("crossfade", 0.2))
    exigido = 1.0 if abs(dif) >= 15 else 0.6 if abs(dif) >= 8 else 0.0
    j["crossfade_exigido"] = exigido
    if exigido and cf + 1e-3 < exigido and max(antes, depois) > -45:
        saltos.append(j)
        avisos.append(f"degrau no som de fundo de {dif:+.1f} LU na emenda {j['t']:.1f}s "
                      f"(trecho {j['trecho']}, {j['capitulo']}) — conferir")

# ---- fala cortada: voz alta logo antes de cada emenda e no fim do conteúdo (antes da tela final)
print("Procurando fala cortada…", flush=True)
falas_cortadas = []


def voz_no_corte(t, nome):
    t0, ser = energia_voz(a.video, t - 30, min(30, t))   # termina exatamente no corte
    if len(ser) < 60:
        return
    from bordas import fundo_robusto
    fundo = fundo_robusto(ser)              # fundo do jogo (30 s, ignorando silêncio digital de menus)
    if fundo is None:
        return
    ult = ser[-12:]                         # 0,6 s antes do corte
    # fala cortada de verdade tem voz ATÉ o instante do corte; frase que terminou 0,4 s antes (respiro do corte de
    # silêncio do ritmo V4.1) não conta — exige voz também nos últimos 0,25 s (2026-11-26)
    if ult and sum(1 for v in ult if v > fundo + 12) >= 6 and sum(1 for v in ult[-5:] if v > fundo + 12) >= 3:
        falas_cortadas.append({"t": round(t, 2), "onde": nome, "acima_do_fundo_db": round(max(ult) - fundo, 1)})
        return f"possível FALA CORTADA {nome} ({t:.1f}s): voz {max(ult) - fundo:+.0f} dB acima do fundo até o corte"


for j in J["juncoes"]:
    m = voz_no_corte(j["t"] + float(j.get("audio_desloc", 0) or 0),   # J/L: a fronteira do som anda
                     f"na emenda do trecho {j['trecho']} ({j['capitulo']})")
    if m:
        avisos.append(m)
m = voz_no_corte(fim_util + 0.6, "no FIM do episódio")
if m:
    problemas.append(m + " — o fim do episódio não pode cortar fala")

# ---- painel visual das emendas (antes | depois), 12 emendas por painel
print("Gerando painéis das emendas…", flush=True)
FONTE = "C\\:/Windows/Fonts/arialbd.ttf"
for p0 in range(0, len(J["juncoes"]), 12):
    grupo = J["juncoes"][p0:p0 + 12]
    imgs = []
    for k, j in enumerate(grupo):
        for lado, dt in (("a", -0.25), ("d", 0.25)):
            out = os.path.join(pasta, f"_qc_{p0 + k:03d}{lado}.jpg")
            sh(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-ss", f"{max(0, j['t'] + dt):.3f}", "-i", a.video,
                "-frames:v", "1", "-vf", f"scale=384:-2,drawtext=fontfile='{FONTE}':text='{j['t']:.1f}s {lado}':"
                f"x=4:y=4:fontsize=16:fontcolor=yellow:box=1:boxcolor=black@0.7,format=yuvj420p", out])
            imgs.append(out)
    if imgs:
        lst = os.path.join(pasta, "_qc_lista.txt")
        with open(lst, "w", encoding="utf-8") as f:
            for im in imgs:
                f.write(f"file '{os.path.abspath(im)}'\n")
        sh(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst,
            "-vf", "tile=4x6:padding=2,format=yuvj420p", "-frames:v", "1",
            os.path.join(pasta, f"qc_emendas_{p0 // 12:02d}.jpg")])
        for im in imgs:
            os.remove(im)
        os.remove(lst)

# ---- decodificação completa
if not a.rapido:
    print("Decodificando o arquivo inteiro…", flush=True)
    r = sh(["ffmpeg", "-hide_banner", "-v", "error", "-i", a.video, "-f", "null", "-"])
    erros = [l for l in r.stderr.splitlines() if l.strip()]
    if erros:
        problemas.append(f"{len(erros)} erros de decodificação (ex.: {erros[0][:120]})")
    info["decodificacao_completa"] = "ok" if not erros else "com erros"

res = {**info, "emendas": len(J["juncoes"]), "pretos": pretos, "silencios": silencios,
       "saltos_volume": saltos, "travamentos": travamentos, "falas_cortadas": falas_cortadas, "problemas": problemas, "avisos": avisos}
json.dump(res, open(os.path.join(pasta, "qc.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps({k: res[k] for k in ("resolucao", "fps", "duracao_min", "duracao_video", "duracao_audio",
                                      "emendas")}, ensure_ascii=False))
print("PROBLEMAS:", problemas or "nenhum")
print("AVISOS:", len(avisos))
for x in avisos[:40]:
    print("  -", x)
raise SystemExit(1 if problemas else 0)

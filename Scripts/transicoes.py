"""TRANSIÇÕES INTELIGENTES (V4) — escolhe a emenda de cada junção pelo contexto, em vez de um padrão único.

Para cada junção entre trechos descontínuos, mede na FONTE:
- semelhança visual entre o último quadro de A e o primeiro de B (grade 96x54);
- tela escura/carregamento em algum dos lados (transição natural do jogo);
- distância no tempo entre os trechos (elipse);
- voz logo DEPOIS do fim de A e logo ANTES do início de B (diálogo que seria cortado);
- degrau de som de fundo (o montar_episodios já ajusta o crossfade por isso).

Decide:
- "corte"    (padrão): imagem corta; áudio com crossfade curto. Usado quando a cena continua parecida ou
                       quando um lado é carregamento/tela escura (a transição já existe no jogo).
- "dissolve" : só para elipse real (troca de ambiente E salto > 8 min), nunca dois seguidos, com teto por
               episódio (config/projeto.json -> transicoes).
- L-cut      : "audio_desloc" > 0 — o som de A continua alguns décimos sobre a imagem de B, para a frase
               terminar, desde que o começo de B não tenha voz (nunca sobrepor falas).
- J-cut      : "audio_desloc" < 0 — o som de B entra antes da imagem, quando a fala de B começa colada no corte.
Transição marcada à mão no plano com "transicao_forcada": true não é alterada.
Grava em cada trecho: transicao, audio_desloc, transicao_motivo. Rodar ANTES do validar_plano.py.

Uso: python Scripts/transicoes.py Trabalho/plano_x.json [--audio A] [--so-relatorio]
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import comum  # noqa: E402
from bordas import energia_voz  # noqa: E402

GW, GH = 96, 54


def quadro(video, t):
    r = __import__("subprocess").run(
        ["ffmpeg", "-hide_banner", "-loglevel", "error", "-ss", f"{max(0, t):.3f}", "-i", video, "-frames:v", "1",
         "-vf", f"scale={GW}:{GH}:flags=area,format=gray", "-f", "rawvideo", "-"], capture_output=True)
    return r.stdout if len(r.stdout) == GW * GH else None


def diferenca(a, b, cam=None, W=1920, H=1080):
    if not a or not b:
        return None
    skip = set()
    if cam:
        x, y, w, h = cam
        for yy in range(int(y / H * GH), min(GH, int((y + h) / H * GH) + 1)):
            for xx in range(int(x / W * GW), min(GW, int((x + w) / W * GW) + 1)):
                skip.add(yy * GW + xx)
    vals = [abs(a[i] - b[i]) for i in range(GW * GH) if i not in skip]
    return sum(vals) / max(1, len(vals))


def lum(a):
    return sum(a) / len(a) if a else 0


def voz_acima(audio, t0, dur, fundo_jan=20.0):
    """fração dos 50 ms de [t0, t0+dur] com voz bem acima do fundo local."""
    a0, ser = energia_voz(audio, t0 - fundo_jan / 2, fundo_jan + dur)
    if len(ser) < 40:
        return 0.0
    fundo = sorted(ser)[len(ser) // 5]
    i0 = int(round((t0 - a0) / 0.05))
    jan = ser[i0:i0 + max(1, int(round(dur / 0.05)))]
    return sum(1 for v in jan if v > fundo + 10) / max(1, len(jan))


def escolher(plano, audio=None, escrever=True):
    cfg = comum.projeto().get("transicoes", {})
    jl = float(cfg.get("jl_max", 0.8))
    src = plano["video"]
    info = comum.sonda(src)
    W, H = info["w"], info["h"]
    cam = plano.get("facecam")
    audio = audio or plano.get("audio") or src
    relatorio = []
    for ep in plano["episodios"]:
        M = ep["montagem"]
        nd = 0
        for i in range(1, len(M)):
            s, p = M[i], M[i - 1]
            if abs(s["origem_inicio"] - p["origem_fim"]) < 0.05:
                s["transicao"], s["audio_desloc"] = "continuo", 0.0
                continue
            if s.get("transicao_forcada"):
                nd += s.get("transicao") == "dissolve"
                relatorio.append((ep["parte"], i + 1, s["transicao"], 0.0, "forçada no plano"))
                continue
            fa, fb = quadro(src, p["origem_fim"] - 0.05), quadro(src, s["origem_inicio"] + 0.02)
            dif = diferenca(fa, fb, cam, W, H)
            salto = s["origem_inicio"] - p["origem_fim"]
            escuro = min(lum(fa), lum(fb)) < 14
            motivos = []
            tipo = "corte"
            if escuro:
                motivos.append("um lado é tela escura/carregamento: transição natural do jogo")
            elif dif is not None and dif < 14:
                motivos.append(f"cena parecida (dif {dif:.0f}): corte invisível")
            elif salto > 480 and (dif is None or dif > 30):
                ant_d = p.get("transicao") == "dissolve"
                if not ant_d and nd < plano.get("dissolves_max", cfg.get("dissolves_por_episodio_max", 6)):
                    tipo = "dissolve"
                    motivos.append(f"elipse de {salto / 60:.0f} min com troca de ambiente (dif {dif:.0f})")
                else:
                    motivos.append("elipse, mas dissolve evitado (seguido/teto) — corte com crossfade")
            else:
                motivos.append(f"corte com crossfade (dif {dif if dif is None else round(dif)}, salto {salto:.0f}s)")
            # J/L pela voz na fonte
            depois_a = voz_acima(audio, p["origem_fim"], jl)          # voz que continuaria depois do corte
            antes_b = voz_acima(audio, s["origem_inicio"] - jl, jl)   # voz logo antes do início de B
            inicio_b = voz_acima(audio, s["origem_inicio"], jl)
            fim_a = voz_acima(audio, p["origem_fim"] - jl, jl)
            desloc = 0.0
            if depois_a > 0.3 and inicio_b < 0.15:
                desloc = round(jl, 2)
                motivos.append(f"L-cut {desloc}s: a fala de A continua depois do corte e B começa sem voz")
            elif antes_b > 0.3 and fim_a < 0.15:
                desloc = -round(min(jl, 0.6), 2)
                motivos.append(f"J-cut {-desloc}s: a fala de B começa antes do ponto de entrada e A termina sem voz")
            elif depois_a > 0.3 and inicio_b >= 0.15:
                motivos.append("ATENÇÃO: voz dos dois lados — mover a borda (Bordas.fim) em vez de sobrepor falas")
            s["transicao"], s["audio_desloc"], s["transicao_motivo"] = tipo, desloc, "; ".join(motivos)
            nd += tipo == "dissolve"
            relatorio.append((ep["parte"], i + 1, tipo, desloc, s["transicao_motivo"]))
    return relatorio


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("plano")
    ap.add_argument("--audio")
    ap.add_argument("--so-relatorio", action="store_true")
    a = ap.parse_args()
    plano = comum.carregar_json(a.plano)
    rel = escolher(plano, a.audio)
    for parte, k, tipo, d, mot in rel:
        print(f"Parte {parte} trecho {k}: {tipo}{f' audio_desloc {d:+.2f}s' if d else ''} — {mot}")
    if not a.so_relatorio:
        plano.pop("validacao", None)            # montagem mudou: precisa validar de novo
        comum.salvar_json(a.plano, plano)
        print(f"{len(rel)} junção(ões) decidida(s); plano gravado — agora rodar validar_plano.py")


if __name__ == "__main__":
    main()

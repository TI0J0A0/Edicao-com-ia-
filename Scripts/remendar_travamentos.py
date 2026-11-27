"""REMENDO DE TRAVAMENTOS (V4) — cobre a IMAGEM travada da fonte com a mesma live gravada em outra plataforma.

Por quê: o VOD da Twitch às vezes perde pedaços de 2 s de imagem (travamento com múltiplos de 2 s, ex.:
1:15:29.97–1:15:40.03) enquanto o SOM continua normal. Cortar o travamento remove fala ("nunca corte uma fala");
deixar mostra imagem parada ("cuidado com momentos travando"). Se a mesma live existe no YouTube (simulcast),
a imagem desses segundos está lá — então o trecho fica CONTÍNUO, com o som original da Twitch, e só a imagem
dos segundos travados vem da outra gravação.

Para cada bloco de travamento (travamentos_fonte.json, vãos < 2,5 s juntos) dentro das partes do plano:
1. baixa só aquele pedaço do YouTube (yt-dlp --download-sections, vídeo 1440p60 + áudio);
2. alinha quadro a quadro: 1 s ANTES do travamento e confere 0,5 s DEPOIS (tem que bater no mesmo deslocamento,
   ±1 quadro) — se não bater, o remendo é recusado e o travamento continua sendo cortado;
3. confere que a outra gravação NÃO está travada no mesmo intervalo (freezedetect);
4. confere que o som da Twitch no intervalo é o mesmo do YouTube (envelope de energia) — som da fonte inteiro.
Saída: <cache>/remendos/remendos.json  [{ini, fim, arquivo, desloc, dif_antes, dif_depois}]
       (tempo no clipe = tempo na fonte − desloc). O gerador do plano lê isso e grava "remendos_video" no plano;
       o montar_episodios sobrepõe o clipe na imagem só nesses intervalos.

Precisa de numpy: rodar com o Python do whisper-env:
  %USERPROFILE%/whisper-env/Scripts/python.exe Scripts/remendar_travamentos.py --plano Trabalho/plano_x.json \
      --yt <url> --desloc-aprox 281.9 --travamentos <cache>/travamentos_fonte.json --saida <cache>/remendos
"""
import argparse
import json
import os
import subprocess
import sys

import numpy as np

GW, GH = 96, 54
FPS = 60.0


def quadros(src, ss, dur):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-ss", f"{max(0, ss):.3f}", "-i", src,
                        "-t", f"{dur:.3f}", "-vf", f"fps={FPS:g},scale={GW}:{GH}:flags=area,format=gray",
                        "-f", "rawvideo", "-"], capture_output=True)
    n = len(r.stdout) // (GW * GH)
    return np.frombuffer(r.stdout[:n * GW * GH], np.uint8).reshape(n, GH, GW).astype(np.float32)


def energia(src, ss, dur):
    """envelope de energia (dB) a cada 50 ms"""
    r = subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-ss", f"{max(0, ss):.3f}", "-i", src,
                        "-t", f"{dur:.3f}", "-vn", "-ac", "1", "-ar", "8000", "-f", "s16le", "-"], capture_output=True)
    x = np.frombuffer(r.stdout[:len(r.stdout) // 2 * 2], np.int16).astype(np.float32)
    n = len(x) // 400
    if n == 0:
        return np.zeros(0)
    x = x[:n * 400].reshape(n, 400)
    return 10 * np.log10((x ** 2).mean(axis=1) + 1)


def alinhar(A, Bq, cam_cols):
    """melhor índice de Bq onde a sequência A encaixa; devolve (indice, dif, segunda_melhor)"""
    m = np.ones(GW, bool)
    m[:cam_cols] = False                       # ignora a faixa da facecam
    res = []
    for off in range(0, len(Bq) - len(A) + 1):
        res.append((float(np.abs(Bq[off:off + len(A)][:, :, m] - A[:, :, m]).mean()), off))
    if not res:
        return None, None, None
    res.sort()
    seg = next((d for d, o in res[1:] if abs(o - res[0][1]) > 3), None)
    return res[0][1], res[0][0], seg


def paradas_em(Bq, t0, t1, cam_cols, lim=0.5):
    """paradas da imagem do JOGO (fora da facecam) no clipe, em [t0, t1] (tempo do clipe), medidas quadro a quadro
    na grade 96x54: quadro 'parado' = diferença média < lim para o anterior. Devolve [(ini, fim)] >= 0,6 s.
    (2026-11-26: o freezedetect do ffmpeg confundia o ruído de compressão do YouTube com movimento e deixou passar
    um trecho que no YouTube também estava parado, com um quadro novo a cada 2 s.)"""
    m = np.ones(GW, bool)
    m[:cam_cols] = False
    i0, i1 = max(1, int(t0 * FPS)), min(len(Bq), int(t1 * FPS) + 1)
    out, ini = [], None
    for i in range(i0, i1):
        parado = float(np.abs(Bq[i][:, m] - Bq[i - 1][:, m]).mean()) < lim
        if parado and ini is None:
            ini = i
        elif not parado and ini is not None:
            if (i - ini) / FPS >= 0.6:
                out.append((ini / FPS, i / FPS))
            ini = None
    if ini is not None and (i1 - ini) / FPS >= 0.6:
        out.append((ini / FPS, i1 / FPS))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plano", required=True)
    ap.add_argument("--yt", required=True)
    ap.add_argument("--desloc-aprox", type=float, required=True, help="tempo fonte − tempo YouTube (alinhado pelo áudio)")
    ap.add_argument("--travamentos", required=True)
    ap.add_argument("--saida", required=True)
    ap.add_argument("--formato", default="308+140/400+140/bv*[height<=1440]+ba")
    ap.add_argument("--parada-max", type=float, default=2.0,
                    help="maior parada aceita na outra gravação (s); com paradas, o gerador cobre o remendo com zoom "
                         "contínuo lento. Acima disso, ou parada > 60%% do tempo, o remendo é recusado")
    ap.add_argument("--so", type=float, nargs="*", help="só estes blocos (início em s)")
    ap.add_argument("--margem", type=float, default=2.5, help="vão que junta travamentos num bloco só")
    a = ap.parse_args()

    plano = json.load(open(a.plano, encoding="utf-8"))
    src = plano["video"]
    W = int(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width",
                            "-of", "csv=p=0", src], capture_output=True, text=True).stdout.strip())
    cam = plano.get("facecam")
    cam_cols = int((cam[0] + cam[2]) / W * GW) + 1 if cam else 0
    faixas = [(ep["origem_inicio"], ep["origem_fim"]) for ep in plano["episodios"]]

    blocos = []
    for x, y in sorted(json.load(open(a.travamentos, encoding="utf-8"))):
        if blocos and x - blocos[-1][1] < a.margem:
            blocos[-1][1] = max(blocos[-1][1], y)
        else:
            blocos.append([x, y])
    blocos = [b for b in blocos if any(f0 - 1 < b[0] < f1 + 1 for f0, f1 in faixas)]
    os.makedirs(a.saida, exist_ok=True)
    yt_dlp = os.path.join(os.environ["USERPROFILE"], "whisper-env", "Scripts", "yt-dlp.exe")
    saida_p = os.path.join(a.saida, "remendos.json")
    ok = {round(r["ini"], 2): r for r in (json.load(open(saida_p, encoding="utf-8")) if os.path.exists(saida_p) else [])}
    recusados = []
    for ini, fim in blocos:
        if a.so and not any(abs(ini - x) < 0.5 for x in a.so):
            continue
        if round(ini, 2) in ok and os.path.exists(ok[round(ini, 2)]["arquivo"]):
            continue
        y0 = ini - a.desloc_aprox - 6
        if y0 < 0:
            recusados.append((ini, fim, "antes do começo da gravação do YouTube"))
            continue
        y1 = fim - a.desloc_aprox + 4
        arq = os.path.join(a.saida, f"yt_{ini:.2f}.mkv")
        if not os.path.exists(arq):
            subprocess.run([yt_dlp, "-q", "--no-warnings", "-f", a.formato, "--merge-output-format", "mkv",
                            "--download-sections", f"*{y0:.2f}-{y1:.2f}", "-o", arq, a.yt], check=False)
        if not os.path.exists(arq):
            recusados.append((ini, fim, "download falhou"))
            continue
        clip_dur = y1 - y0 + 6
        Bq = quadros(arq, 0, clip_dur)
        # 1) antes do travamento (1 s que termina 0,3 s antes dele)
        A1 = quadros(src, ini - 1.3, 1.0)
        o1, d1, s1 = alinhar(A1, Bq, cam_cols)
        # 2) depois do travamento (0,5 s começando 0,3 s depois)
        A2 = quadros(src, fim + 0.3, 0.5)
        o2, d2, s2 = alinhar(A2, Bq, cam_cols)
        if o1 is None or o2 is None:
            recusados.append((ini, fim, "clipe curto demais"))
            continue
        des1 = (ini - 1.3) - o1 / FPS                # tempo no clipe = fonte − desloc
        des2 = (fim + 0.3) - o2 / FPS
        motivo = None
        if abs(des1 - des2) > 1.5 / FPS:
            motivo = f"alinhamento antes/depois não bate ({des1:.3f} x {des2:.3f})"
        elif d1 > 8 or d2 > 8:
            motivo = f"quadros não batem (dif {d1:.1f}/{d2:.1f})"
        elif s1 is not None and s1 - d1 < 1.0:
            motivo = f"cena parada, alinhamento ambíguo (dif {d1:.1f} x {s1:.1f})"
        if motivo and len(ok) >= 3:
            # plano B (cena parada/ambígua): o deslocamento Twitch x YouTube é CONSTANTE e o clipe sempre começa
            # numa chave do YouTube (a cada 2 s) — então desloc ≡ fração fixa (mod 2). Testa só esses candidatos
            # e aceita se os quadros baterem ANTES e DEPOIS do travamento.
            fr = float(np.median([r["desloc"] % 2 for r in ok.values()]))
            m = np.ones(GW, bool)
            m[:cam_cols] = False

            def dif_em(Aq, t_src, c):
                o = int(round((t_src - c) * FPS))
                if o < 0 or o + len(Aq) > len(Bq):
                    return 99.0
                return float(np.abs(Bq[o:o + len(Aq)][:, :, m] - Aq[:, :, m]).mean())
            cands = [ini - 14 + fr + 2 * k - (ini - 14) % 2 for k in range(9)]
            melhor = min(((dif_em(A1, ini - 1.3, c), dif_em(A2, fim + 0.3, c), c) for c in cands),
                         key=lambda x: x[0] + x[1])
            if melhor[0] < 4.5 and melhor[1] < 4.5:
                d1, d2, des1 = melhor[0], melhor[1], melhor[2]
                print(f"  plano B {ini:.2f}: {motivo} -> desloc previsto {des1:.3f} (dif {d1:.1f}/{d2:.1f})", flush=True)
                motivo = None
            else:
                motivo += f"; plano B também não bate (dif {melhor[0]:.1f}/{melhor[1]:.1f})"
        paradas = []
        if not motivo:
            paradas = [(x - (ini - des1), y - (ini - des1))
                       for x, y in paradas_em(Bq, ini - des1 - 0.05, fim - des1 + 0.1, cam_cols)]
            frac = sum(y - x for x, y in paradas) / max(0.1, fim - ini)
            if any(y - x > a.parada_max for x, y in paradas) or frac > 0.6:
                motivo = (f"o YouTube também está parado nesse intervalo (maior parada "
                          f"{max(y - x for x, y in paradas):.1f}s, {frac:.0%} do tempo)")
        if not motivo:
            et = energia(src, ini - 0.5, fim - ini + 1)
            ey = energia(arq, ini - des1 - 0.5, fim - ini + 1)
            n = min(len(et), len(ey))
            if n > 10 and np.std(et[:n]) > 1 and np.std(ey[:n]) > 1:
                c = float(np.corrcoef(et[:n], ey[:n])[0, 1])
                if c < 0.6:
                    motivo = f"som da Twitch diferente do YouTube no intervalo (corr {c:.2f})"
        if motivo:
            recusados.append((ini, fim, motivo))
            print(f"  RECUSADO {ini:.2f}–{fim:.2f}: {motivo}", flush=True)
            continue
        ok[round(ini, 2)] = {"ini": round(ini, 3), "fim": round(fim, 3), "arquivo": arq.replace("\\", "/"),
                             "desloc": round(des1, 4), "dif_antes": round(d1, 2), "dif_depois": round(d2, 2),
                             # paradinhas da outra gravação (tempo na fonte): o gerador cobre com zoom suave
                             "paradas": [[round(ini + x, 2), round(ini + y, 2)] for x, y in paradas]}
        print(f"  ok {ini:.2f}–{fim:.2f} desloc {des1:.3f} (dif {d1:.1f}/{d2:.1f})", flush=True)
        json.dump(sorted(ok.values(), key=lambda r: r["ini"]), open(saida_p, "w", encoding="utf-8"), indent=1)
    json.dump(sorted(ok.values(), key=lambda r: r["ini"]), open(saida_p, "w", encoding="utf-8"), indent=1)
    print(f"{len(ok)} remendo(s) ok, {len(recusados)} recusado(s) -> {saida_p}")
    for r in recusados:
        print(f"  recusado {r[0]:.2f}–{r[1]:.2f}: {r[2]}")


if __name__ == "__main__":
    sys.exit(main())

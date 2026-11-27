"""Baixa uma VOD da Twitch na QUALIDADE ORIGINAL + áudio + proxy 160p (V4).

Aprendido em 2026-11-26 (live 2940902491, transmitida em 1440p60 com Enhanced Broadcasting): a lista de
qualidades da Twitch (e portanto o `yt-dlp -F`) mostrava no máximo 720p60, sem "Source". O original
(2560x1440 60 fps) estava na pasta `chunked/` do mesmo servidor, fora da lista. Este script:
  1. lê a lista oficial (yt-dlp -J) e a resolução de cada qualidade;
  2. testa a pasta `chunked/` (original) trocando o nome da qualidade no endereço da playlist;
  3. escolhe a MAIOR resolução encontrada e mostra a decisão ANTES de baixar;
  4. baixa original -> Bruto/live_<id>_<res>.mp4, áudio e proxy 160p -> Trabalho/longo_<jogo>_<id>/.

Uso: python Scripts/baixar_vod.py <link_da_vod> [--jogo gta] [--so-ver]
"""
import argparse
import json
import os
import re
import subprocess
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import comum  # noqa: E402

YTDLP = os.path.join(os.environ.get("USERPROFILE", ""), "whisper-env", "Scripts", "yt-dlp.exe")


def get(url):
    with urllib.request.urlopen(url, timeout=30) as r:
        return r.status, r.read()


def resolucao_de(playlist_url, tmp):
    """baixa 1 segmento da playlist e lê a resolução/fps real."""
    try:
        _, txt = get(playlist_url)
    except Exception:
        return None
    segs = [l for l in txt.decode("utf-8", "ignore").splitlines() if l and not l.startswith("#")]
    if not segs:
        return None
    seg = segs[min(5, len(segs) - 1)]
    seg_url = seg if seg.startswith("http") else playlist_url.rsplit("/", 1)[0] + "/" + seg
    try:
        _, dados = get(seg_url)
    except Exception:
        return None
    open(tmp, "wb").write(dados)
    r = comum.sh(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                  "stream=width,height,r_frame_rate,codec_name", "-of", "json", tmp])
    st = (json.loads(r.stdout or "{}").get("streams") or [None])[0]
    os.remove(tmp)
    if not st:
        return None
    n, d = map(int, st["r_frame_rate"].split("/"))
    return {"w": st["width"], "h": st["height"], "fps": round(n / d, 2), "codec": st["codec_name"],
            "segmentos": len(segs)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("link")
    ap.add_argument("--jogo", default="gta")
    ap.add_argument("--so-ver", action="store_true")
    a = ap.parse_args()
    vid = re.search(r"videos/(\d+)", a.link).group(1)
    info = json.loads(subprocess.run([YTDLP, "-J", a.link], capture_output=True, text=True, encoding="utf-8").stdout)
    oficiais = [f for f in info["formats"] if f.get("height") and f.get("vcodec") not in (None, "none")]
    top = max(oficiais, key=lambda f: (f["height"], f.get("fps") or 0))
    print(f"Lista oficial: até {top['format_id']} ({top.get('width')}x{top['height']})")
    pl_top = top["url"]
    tmp = os.path.join(comum.RAIZ, "Trabalho", f"_seg_{vid}.ts")
    os.makedirs(os.path.dirname(tmp), exist_ok=True)
    cand = {"lista": (pl_top, resolucao_de(pl_top, tmp))}
    nome_q = re.search(r"/([^/]+)/index-[^/]*\.m3u8", pl_top)
    if nome_q:
        u = pl_top.replace(f"/{nome_q.group(1)}/", "/chunked/")
        r = resolucao_de(u, tmp)
        if r:
            cand["chunked (original, fora da lista)"] = (u, r)
    for k, (u, r) in cand.items():
        print(f"  {k}: {r['w']}x{r['h']} {r['fps']} fps {r['codec']} ({r['segmentos']} segmentos)" if r else f"  {k}: indisponível")
    melhor_k, (melhor_u, melhor_r) = max(((k, v) for k, v in cand.items() if v[1]), key=lambda kv: kv[1][1]["h"])
    print(f"ESCOLHIDA: {melhor_k} -> {melhor_r['w']}x{melhor_r['h']} {melhor_r['fps']} fps")
    if a.so_ver:
        return
    cache = os.path.join("Trabalho", f"longo_{a.jogo}_{vid}")
    os.makedirs(cache, exist_ok=True)
    os.makedirs("Bruto", exist_ok=True)
    res = f"{melhor_r['h']}p{round(melhor_r['fps'])}"
    jobs = [([YTDLP, "-N", "8", "--no-part", "-o", f"Bruto/live_{vid}_{res}.mp4", melhor_u], "dl_fonte.log"),
            ([YTDLP, "-f", "Audio_Only", "-N", "8", "-o", f"{cache}/audio_{vid}.%(ext)s", a.link], "dl_audio.log"),
            ([YTDLP, "-f", "160p", "-N", "8", "-o", f"{cache}/proxy_{vid}_160p.%(ext)s", a.link], "dl_160.log")]
    procs = [subprocess.Popen(c, stdout=open(os.path.join(cache, log), "w"), stderr=subprocess.STDOUT) for c, log in jobs]
    for p, (c, log) in zip(procs, jobs):
        print(f"{log}: rc={p.wait()}")


if __name__ == "__main__":
    main()

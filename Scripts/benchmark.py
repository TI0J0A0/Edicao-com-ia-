"""BENCHMARK (V4) — mede antes de mudar: velocidade, CPU, memória, qualidade e tokens.

1. Decodificação 1080p60: CPU x d3d11va x amf (tempo, CPU usada, memória máx.) — via `ffmpeg -benchmark`.
2. Render de um pedaço igual ao do montar_episodios (fps + scale + h264_amf CQP 18/20/22): CPU-decode x GPU-decode,
   e SSIM entre os dois resultados (prova se a GPU muda a imagem).
3. Análise (analisar_live.py): no vídeo HD x no proxy 160p.
4. Tokens: tamanho do resumo multimodal x transcrição (≈ 4 caracteres por token).
Grava Scripts/benchmarks/benchmark_<data>.json e .md. Só ative "hwaccel_decode" em config/projeto.json se o
ganho for real E o SSIM ficar >= 0.999.

Uso: python Scripts/benchmark.py <video_1080p> [--transcricao T.json --resumo resumo_ia.txt] [--seg 60]
"""
import argparse
import datetime
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import comum  # noqa: E402


def bench(cmd):
    t = time.time()
    r = comum.sh(["ffmpeg", "-hide_banner", "-benchmark", *cmd])
    wall = time.time() - t
    ut = re.search(r"utime=([\d.]+)s stime=([\d.]+)s rtime=([\d.]+)s", r.stderr)
    mx = re.search(r"maxrss=(\d+)KiB", r.stderr)
    return {"ok": r.returncode == 0, "tempo_s": round(wall, 2),
            "cpu_s": round(float(ut.group(1)) + float(ut.group(2)), 2) if ut else None,
            "mem_max_mb": round(int(mx.group(1)) / 1024) if mx else None,
            "erro": None if r.returncode == 0 else r.stderr.strip()[-200:]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--seg", type=float, default=60.0)
    ap.add_argument("--inicio", type=float, default=300.0)
    ap.add_argument("--transcricao")
    ap.add_argument("--resumo")
    a = ap.parse_args()
    info = comum.sonda(a.video)
    tmp = os.path.join(comum.RAIZ, "Trabalho", "_benchmark")
    os.makedirs(tmp, exist_ok=True)
    R = {"data": datetime.datetime.now().isoformat(timespec="seconds"), "video": a.video,
         "fonte": f"{info['w']}x{info['h']} {info['fps_str']}", "trecho_s": a.seg}
    ss = ["-ss", f"{a.inicio}", "-t", f"{a.seg}"]

    print("1) decodificação…", flush=True)
    R["decodificacao"] = {}
    for nome, hw in (("cpu", []), ("d3d11va", ["-hwaccel", "d3d11va"]), ("amf", ["-hwaccel", "amf"])):
        R["decodificacao"][nome] = bench([*hw, *ss, "-i", a.video, "-an", "-f", "null", "-"])
        print("  ", nome, R["decodificacao"][nome], flush=True)

    print("2) render (cadeia do montar_episodios)…", flush=True)
    venc = ["-c:v", "h264_amf", *comum.projeto()["render"]["venc"], "-g", "120"]
    R["render"] = {}
    saidas = {}
    for nome, hw in (("cpu_decode", []), ("gpu_decode_d3d11va", ["-hwaccel", "d3d11va"]), ("gpu_decode_amf", ["-hwaccel", "amf"])):
        out = os.path.join(tmp, f"render_{nome}.mp4")
        R["render"][nome] = bench(["-y", *hw, *ss, "-i", a.video, "-vf",
                                   f"fps={info['fps_str']},scale={info['w']}:{info['h']},setsar=1,format=yuv420p",
                                   "-an", *venc, out])
        saidas[nome] = out
        print("  ", nome, R["render"][nome], flush=True)
    for nome in ("gpu_decode_d3d11va", "gpu_decode_amf"):
        r = comum.sh(["ffmpeg", "-hide_banner", "-i", saidas["cpu_decode"], "-i", saidas[nome],
                      "-lavfi", "ssim", "-f", "null", "-"])
        m = re.search(r"All:([\d.]+)", r.stderr)
        R["render"]["ssim_cpu_x_" + nome] = float(m.group(1)) if m else None
    r = comum.sh(["ffmpeg", "-hide_banner", *ss, "-i", a.video, "-i", saidas["cpu_decode"],
                  "-lavfi", "[0:v][1:v]ssim", "-f", "null", "-"])
    m = re.search(r"All:([\d.]+)", r.stderr)
    R["render"]["ssim_fonte_x_render"] = float(m.group(1)) if m else None
    print("   SSIM cpu x d3d11va:", R["render"]["ssim_cpu_x_gpu_decode_d3d11va"], "| cpu x amf:",
          R["render"]["ssim_cpu_x_gpu_decode_amf"], "| fonte x render:", R["render"]["ssim_fonte_x_render"])

    print("3) análise HD x proxy 160p…", flush=True)
    clip = os.path.join(tmp, "clip.mp4")
    proxy = os.path.join(tmp, "clip_160p.mp4")
    comum.sh(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *ss, "-i", a.video, "-c", "copy", clip])
    comum.sh(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", clip, "-vf", "scale=-2:160",
              "-c:v", "h264_amf", "-c:a", "aac", proxy])
    R["analise"] = {}
    for nome, v in (("hd", clip), ("proxy_160p", proxy)):
        cache = os.path.join(tmp, f"an_{nome}")
        comum.sh(["cmd", "/c", "rmdir", "/s", "/q", cache])
        t = time.time()
        r = comum.sh([sys.executable, os.path.join(comum.SCRIPTS, "analisar_live.py"), v, cache, "--facecam",
                      "auto", "--fonte-wh", f"{info['w']}x{info['h']}"])
        R["analise"][nome] = {"tempo_s": round(time.time() - t, 1), "ok": r.returncode == 0,
                              "x_tempo_real": round(a.seg / max(0.1, time.time() - t), 1),
                              "facecam": (comum.carregar_json(os.path.join(cache, "facecam.json"), {}) or {}).get("facecam")}
        print("  ", nome, R["analise"][nome], flush=True)

    if a.transcricao and a.resumo:
        tr = comum.carregar_json(a.transcricao, {})
        txt = sum(len(f["texto"]) + 30 for f in tr.get("frases", []))
        rs = os.path.getsize(a.resumo)
        R["tokens"] = {"transcricao_txt_tokens": txt // 4, "transcricao_json_tokens": os.path.getsize(a.transcricao) // 4,
                       "resumo_ia_tokens": rs // 4, "reducao_x": round(txt / max(1, rs), 1)}
        print("4) tokens:", R["tokens"])

    rg = R["render"]
    melhor, ganho_r = None, 1.0
    for hw in ("d3d11va", "amf"):
        k = "gpu_decode_" + hw
        g = rg["cpu_decode"]["tempo_s"] / rg[k]["tempo_s"] if rg[k]["ok"] else 0
        if g > ganho_r and (rg.get("ssim_cpu_x_" + k) or 0) >= 0.999:
            melhor, ganho_r = hw, g
    R["conclusao"] = {"ganho_decodificacao": {hw: round(R["decodificacao"]["cpu"]["tempo_s"] / R["decodificacao"][hw]["tempo_s"], 2)
                                              for hw in ("d3d11va", "amf") if R["decodificacao"][hw]["ok"]},
                      "melhor_render": melhor, "ganho_render_x": round(ganho_r, 2),
                      "recomendacao": (f"ativar hwaccel_decode={melhor}" if melhor and ganho_r > 1.1 else
                                       "manter decodificação na CPU (sem ganho real >10% com imagem idêntica)")}
    os.makedirs(os.path.join(comum.SCRIPTS, "benchmarks"), exist_ok=True)
    base = os.path.join(comum.SCRIPTS, "benchmarks", f"benchmark_{datetime.date.today().isoformat()}")
    comum.salvar_json(base + ".json", R)
    print("CONCLUSÃO:", R["conclusao"])
    print("Gravado:", base + ".json")


if __name__ == "__main__":
    main()

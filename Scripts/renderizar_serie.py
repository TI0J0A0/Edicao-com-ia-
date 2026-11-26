"""MOTOR DE RENDER DA SÉRIE (V4) — renderiza as partes EM PARALELO, roda o QC de cada uma e o revisor no fim.

Benchmark (2026-11-26, Ryzen 7 5800XT + RX 9070 XT): o render de 1 parte usa ~3 dos 16 núcleos; 3 partes ao
mesmo tempo dão 1,94x a vazão (22,7 s -> 11,7 s por minuto de vídeo). Padrão: 3 em paralelo.
Retomada: o montar_episodios.py guarda cada pedaço por tempo exato — se cair, rodar de novo continua de onde
parou; parte já entregue com QC sem problemas é pulada (use --refazer para forçar).

Uso: python Scripts/renderizar_serie.py --plano Trabalho/plano_x.json [--partes 1,2] [--paralelo 3] [--refazer]
"""
import argparse
import concurrent.futures as cf
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import comum  # noqa: E402

PY = sys.executable
S = comum.SCRIPTS


def parte(plano_p, pasta, ep, refazer):
    n = ep["parte"]
    pp = os.path.join(pasta, f"parte_{n:02d}")
    os.makedirs(pp, exist_ok=True)
    qc_p = os.path.join(pp, "qc.json")
    qc = comum.carregar_json(qc_p)
    if not refazer and qc and os.path.exists(ep["arquivo"]) and not qc.get("problemas") \
            and os.path.getmtime(qc_p) >= os.path.getmtime(ep["arquivo"]):
        return n, "pulada (já pronta e aprovada no QC)", 0.0
    t = time.time()
    with open(os.path.join(pasta, f"render_{n}.log"), "w", encoding="utf-8") as log:
        r = subprocess.run([PY, os.path.join(S, "montar_episodios.py"), "--plano", plano_p, "--parte", str(n),
                            "--pasta", pasta], stdout=log, stderr=subprocess.STDOUT,
                           env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    if r.returncode != 0:
        return n, f"RENDER FALHOU (ver {pasta}/render_{n}.log)", time.time() - t
    with open(os.path.join(pp, "qc.log"), "w", encoding="utf-8") as log:
        q = subprocess.run([PY, os.path.join(S, "verificar_episodio.py"), ep["arquivo"], os.path.join(pp, "juncoes.json")],
                           stdout=log, stderr=subprocess.STDOUT, env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    qc = comum.carregar_json(qc_p, {})
    st = "ok" if q.returncode == 0 else f"QC COM PROBLEMAS: {qc.get('problemas')}"
    return n, f"{st} | {qc.get('duracao_min')} min | {len(qc.get('avisos', []))} aviso(s)", time.time() - t


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plano", required=True)
    ap.add_argument("--partes", default="")
    ap.add_argument("--paralelo", type=int, default=3)
    ap.add_argument("--refazer", action="store_true")
    a = ap.parse_args()
    plano = comum.carregar_json(a.plano)
    from validar_plano import hash_montagem
    if plano.get("validacao", {}).get("hash") != hash_montagem(plano):
        sys.exit("Plano não validado. Rode antes: python Scripts/validar_plano.py " + a.plano)
    pasta = os.path.join("Trabalho", "ep_" + os.path.splitext(os.path.basename(a.plano))[0])
    quer = {int(x) for x in a.partes.split(",") if x.strip()}
    eps = [e for e in plano["episodios"] if (not quer or e["parte"] in quer)
           and e.get("status", plano.get("status")) == "aprovado"]
    print(f"Renderizando {len(eps)} parte(s), {a.paralelo} por vez…", flush=True)
    t0 = time.time()
    with cf.ThreadPoolExecutor(max_workers=max(1, a.paralelo)) as ex:
        futs = [ex.submit(parte, a.plano, pasta, e, a.refazer) for e in eps]
        for f in cf.as_completed(futs):
            n, st, dt = f.result()
            print(f"  Parte {n}: {st} ({dt / 60:.1f} min)", flush=True)
    print(f"Render + QC: {(time.time() - t0) / 60:.1f} min. Rodando o revisor independente…", flush=True)
    rel = os.path.join(pasta, "revisao.md")
    r = subprocess.run([PY, os.path.join(S, "revisor_editorial.py"), a.plano, "--pasta-render", pasta, "--saida", rel],
                       capture_output=True, text=True, encoding="utf-8", errors="ignore",
                       env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    print(r.stdout.splitlines()[0] if r.stdout else r.stderr[-500:])
    print("Relatório da revisão:", rel)
    raise SystemExit(r.returncode)


if __name__ == "__main__":
    main()

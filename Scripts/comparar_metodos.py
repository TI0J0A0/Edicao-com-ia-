"""MODO DE COMPARAÇÃO (V4) — testa mudanças num trecho representativo ANTES de usar numa live de horas.

Recebe um vídeo (trecho da live), a transcrição e uma lista de trechos "brutos" (como o editor marcaria) e gera:
  A = método atual/anterior (v3): bordas só fora de palavras (snap), sempre "corte", render legado
      (Scripts/legado/montar_episodios_v3.py);
  B = método V4: Bordas (frases + voz do áudio, fim de episódio fechado), transições por contexto (J/L),
      validação, render V4.
Depois roda o MESMO QC (verificar_episodio.py) e o MESMO revisor nos dois e escreve o relatório de diferenças:
bordas (e se cortam fala), transições, durações, problemas de QC, veredito do revisor e tempo de processamento.
Nunca aprova uma mudança só porque deu mais cortes ou vídeo menor: o relatório mostra o que mudou para decidir.

Uso: python Scripts/comparar_metodos.py --video V --transcricao T --trechos "0-28.5,33-220,252-318" [--analise A]
        [--facecam x,y,w,h] [--nome teste] [--perfil narrativo]
"""
import argparse
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import comum  # noqa: E402
from bordas import Bordas  # noqa: E402

PY = sys.executable
S = comum.SCRIPTS


def snap_v3(palavras, dur, x, lado):
    """borda do método v3 (gerador de plano antigo): só tira a borda de dentro de UMA palavra."""
    for i, w in enumerate(palavras):
        if w["inicio"] - 0.15 <= x <= w["fim"] + 0.15:
            if lado == "ini":
                ant = palavras[i - 1]["fim"] if i else 0
                return round(max(w["inicio"] - 0.2, (ant + w["inicio"]) / 2), 2)
            prox = palavras[i + 1]["inicio"] if i + 1 < len(palavras) else dur
            return round(min(w["fim"] + 0.25, (w["fim"] + prox) / 2), 2)
        if w["inicio"] > x + 1:
            break
    return round(x, 2)


def rodar(cmd, log):
    t = time.time()
    with open(log, "w", encoding="utf-8") as f:
        r = subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT, env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    return r.returncode, time.time() - t


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True)
    ap.add_argument("--transcricao", required=True)
    ap.add_argument("--trechos", required=True)
    ap.add_argument("--analise")
    ap.add_argument("--facecam")
    ap.add_argument("--audio")
    ap.add_argument("--nome", default="comparacao")
    ap.add_argument("--perfil", default="mundo_aberto")
    a = ap.parse_args()
    pasta = os.path.join("Trabalho", f"comparacao_{a.nome}")
    os.makedirs(pasta, exist_ok=True)
    tr = comum.carregar_json(a.transcricao)
    palavras = [w for f in tr["frases"] for w in f["palavras"]]
    brutos = [tuple(float(v) for v in p.split("-")) for p in a.trechos.split(",")]
    B = Bordas(a.transcricao, a.audio or a.video)
    cam = [int(v) for v in a.facecam.split(",")] if a.facecam else None
    tempos = {}

    def plano(trechos, nome, extra=None):
        p = {"video": a.video, "jogo": "Comparação", "status": "aprovado", "transcricao": a.transcricao,
             "audio": a.audio or a.video, "analise": a.analise, "perfil": a.perfil.split("+"), "facecam": cam,
             "episodios": [{"parte": 1, "titulo": f"{nome.upper()} | Parte 1", "titulo_card": f"MÉTODO {nome.upper()}",
                            "arquivo": os.path.join(pasta, f"{nome}.mp4"),
                            "montagem": [{"capitulo": f"Trecho {i + 1}", "origem_inicio": x, "origem_fim": y,
                                          "decisao": "MANTER", "motivo": "comparação", "transicao": "corte"}
                                         for i, (x, y) in enumerate(trechos)]}]}
        arq = os.path.join(pasta, f"plano_{nome}.json")
        comum.salvar_json(arq, p)
        return arq

    # ---------------- A: v3
    t = time.time()
    ta = [(snap_v3(palavras, tr["duracao"], x, "ini"), snap_v3(palavras, tr["duracao"], y, "fim")) for x, y in brutos]
    pa = plano(ta, "A_v3")
    tempos["A_plano_s"] = round(time.time() - t, 2)
    rc, tempos["A_render_s"] = rodar([PY, os.path.join(S, "legado", "montar_episodios_v3.py"), "--plano", pa,
                                      "--pasta", os.path.join(pasta, "ep_A")], os.path.join(pasta, "A_render.log"))
    if rc:
        sys.exit(f"render A falhou — ver {pasta}/A_render.log")
    ja = os.path.join(pasta, "ep_A", "parte_01", "juncoes.json")     # o render legado não grava a facecam:
    jj = comum.carregar_json(ja, {})                                    # o QC dos dois usa a mesma régua
    jj["facecam"] = cam
    comum.salvar_json(ja, jj)

    # ---------------- B: V4
    t = time.time()
    tb = []
    for i, (x, y) in enumerate(brutos):
        tb.append((B.inicio(x) if not (i == 0 and x < 1) else x, B.fim(y, final=(i == len(brutos) - 1))))
    pb = plano(tb, "B_v4")
    import transicoes
    pl = comum.carregar_json(pb)
    rel_tr = transicoes.escolher(pl)
    comum.salvar_json(pb, pl)
    import validar_plano
    erros_b, avisos_b = validar_plano.validar(pl, a.transcricao, a.audio or a.video, a.analise, None)
    if not erros_b:
        pl["validacao"] = {"hash": validar_plano.hash_montagem(pl), "em": "comparacao", "avisos": avisos_b}
        comum.salvar_json(pb, pl)
    tempos["B_plano_s"] = round(time.time() - t, 2)
    rc, tempos["B_render_s"] = rodar([PY, os.path.join(S, "montar_episodios.py"), "--plano", pb, "--pasta",
                                      os.path.join(pasta, "ep_B")] + ([] if not erros_b else ["--sem-validacao"]),
                                     os.path.join(pasta, "B_render.log"))
    if rc:
        sys.exit(f"render B falhou — ver {pasta}/B_render.log")

    # ---------------- mesmo QC e mesmo revisor
    res = {}
    for nome, arq_plano in (("A_v3", pa), ("B_v4", pb)):
        ep = os.path.join(pasta, "ep_" + nome[0], "parte_01")
        _, tempos[nome[0] + "_qc_s"] = rodar([PY, os.path.join(S, "verificar_episodio.py"), os.path.join(pasta, f"{nome}.mp4"),
                                             os.path.join(ep, "juncoes.json"), "--rapido"], os.path.join(pasta, f"{nome}_qc.log"))
        qc = comum.carregar_json(os.path.join(ep, "qc.json"), {})
        import revisor_editorial
        rv = revisor_editorial.Revisor(arq_plano, os.path.join(pasta, "ep_" + nome[0]))
        rv.tecnico()
        rv.editorial()
        ver, txt = rv.relatorio(os.path.join(pasta, f"{nome}_revisao.md"))
        res[nome] = {"qc": qc, "veredito": ver, "achados": rv.achados, "info": comum.sonda(os.path.join(pasta, f"{nome}.mp4"))}

    # ---------------- relatório
    L = [f"# Comparação de métodos — {a.nome}", "", f"Vídeo: `{a.video}` · perfil {a.perfil} · {len(brutos)} trechos", "",
         "## Bordas (tempo na live)", "", "| Trecho | Bruto | A (v3) | corta fala? | B (V4) | corta fala? |", "|---|---|---|---|---|---|"]
    for i, ((x, y), (xa, ya), (xb, yb)) in enumerate(zip(brutos, ta, tb)):
        for lado, r_, a_, b_ in (("início", x, xa, xb), ("fim", y, ya, yb)):
            if lado == "início" and i == 0 and x < 1:
                continue
            la = "ini" if lado == "início" else "fim"
            pa_, pb_ = B.problema(a_, la), B.problema(b_, la)
            if la == "fim" and not pa_ and B._prox_inicio(a_) - a_ < (1.2 if i == len(brutos) - 1 else 0.4):
                pa_ = "fala recomeça logo depois"
            if la == "fim" and not pb_ and B._prox_inicio(b_) - b_ < (1.2 if i == len(brutos) - 1 else 0.4):
                pb_ = "fala recomeça logo depois"
            L.append(f"| {i + 1} {lado} | {comum.hms(r_, True)} | {comum.hms(a_, True)} | {'SIM — ' + pa_ if pa_ else 'não'} | "
                     f"{comum.hms(b_, True)} | {'SIM — ' + pb_ if pb_ else 'não'} |")
    L += ["", "## Transições escolhidas no V4", ""] + [f"- trecho {k}: **{tp}**{f' (audio_desloc {d:+.2f}s)' if d else ''} — {m}"
                                                      for _, k, tp, d, m in rel_tr]
    L += ["", f"Validação do plano V4: {len(erros_b)} erro(s), {len(avisos_b)} aviso(s)"] + [f"- {e}" for e in erros_b + avisos_b]
    L += ["", "## Resultado", "", "| | A (v3) | B (V4) |", "|---|---|---|"]
    ra, rb = res["A_v3"], res["B_v4"]
    linhas = [("Duração", f"{ra['qc'].get('duracao_video', 0):.1f}s", f"{rb['qc'].get('duracao_video', 0):.1f}s"),
              ("FPS", ra["info"]["fps_str"], rb["info"]["fps_str"]),
              ("Problemas no QC", len(ra["qc"].get("problemas", [])), len(rb["qc"].get("problemas", []))),
              ("Avisos no QC", len(ra["qc"].get("avisos", [])), len(rb["qc"].get("avisos", []))),
              ("Falas cortadas (QC)", len(ra["qc"].get("falas_cortadas", [])), len(rb["qc"].get("falas_cortadas", []))),
              ("Travamentos (QC)", len(ra["qc"].get("travamentos", [])), len(rb["qc"].get("travamentos", []))),
              ("Revisor: problemas", sum(1 for x in ra["achados"] if x[0] == "PROBLEMA"), sum(1 for x in rb["achados"] if x[0] == "PROBLEMA")),
              ("Revisor: avisos", sum(1 for x in ra["achados"] if x[0] == "AVISO"), sum(1 for x in rb["achados"] if x[0] == "AVISO")),
              ("Veredito do revisor", ra["veredito"], rb["veredito"]),
              ("Tempo: plano", f"{tempos['A_plano_s']}s", f"{tempos['B_plano_s']}s"),
              ("Tempo: render", f"{tempos['A_render_s']:.0f}s", f"{tempos['B_render_s']:.0f}s"),
              ("Tempo: QC", f"{tempos['A_qc_s']:.0f}s", f"{tempos['B_qc_s']:.0f}s")]
    L += [f"| {n} | {x} | {y} |" for n, x, y in linhas]
    L += ["", "Problemas de QC — A: " + "; ".join(ra["qc"].get("problemas", []) or ["nenhum"]),
          "", "Problemas de QC — B: " + "; ".join(rb["qc"].get("problemas", []) or ["nenhum"]), "",
          f"Revisões completas: `{pasta}/A_v3_revisao.md` e `{pasta}/B_v4_revisao.md`. Vídeos: `{pasta}/A_v3.mp4` e `{pasta}/B_v4.mp4`."]
    rel = os.path.join(pasta, "relatorio_comparacao.md")
    open(rel, "w", encoding="utf-8").write("\n".join(L) + "\n")
    print("\n".join(L))
    print("\nRelatório:", rel)


if __name__ == "__main__":
    main()

"""Gera o relatório de entrega de uma série de vídeos longos a partir do plano + resultados reais
(juncoes.json e qc.json de cada parte, produzidos por montar_episodios.py e verificar_episodio.py).

Uso: python Scripts/relatorio_longo.py --plano Trabalho/plano_x.json [--pasta Trabalho/ep_plano_x] --saida videos_longos/<Jogo>/relatorio.md
"""
import argparse
import json
import os

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(RAIZ)
ap = argparse.ArgumentParser()
ap.add_argument("--plano", required=True)
ap.add_argument("--pasta", default=None)
ap.add_argument("--saida", required=True)
ap.add_argument("--mudancas", default=None, help="arquivo .md com as alterações feitas no projeto")
a = ap.parse_args()
plano = json.load(open(a.plano, encoding="utf-8"))
pasta = a.pasta or os.path.join("Trabalho", "ep_" + os.path.splitext(os.path.basename(a.plano))[0])


def hms(x, sempre_h=False):
    x = int(round(x))
    if x >= 3600 or sempre_h:
        return f"{x // 3600}:{x % 3600 // 60:02d}:{x % 60:02d}"
    return f"{x // 60}:{x % 60:02d}"


L = [f"# {plano['jogo']} — relatório da série (live {plano.get('vod', '')})", ""]
L.append(f"Live original: {hms(plano['duracao_original'], True)} · Estilo: {plano.get('estilo', '')} · "
         f"Formato: {plano.get('formato', '')}")
L.append("")
L.append("| Parte | Título | Duração final | Trecho da live | Emendas | Revisão |")
L.append("|---|---|---|---|---|---|")
detalhes = []
for ep in plano["episodios"]:
    p = ep["parte"]
    d = os.path.join(pasta, f"parte_{p:02d}")
    qc = json.load(open(os.path.join(d, "qc.json"), encoding="utf-8")) if os.path.exists(os.path.join(d, "qc.json")) else None
    J = json.load(open(os.path.join(d, "juncoes.json"), encoding="utf-8")) if os.path.exists(os.path.join(d, "juncoes.json")) else None
    dur = qc["duracao_video"] if qc else None
    status = ("ok" if not qc["problemas"] else "PROBLEMAS") + (f" ({len(qc['avisos'])} avisos)" if qc and qc["avisos"] else "") if qc else "não verificado"
    L.append(f"| {p} | {ep['titulo'].replace('|', chr(92) + '|')} | {hms(dur) if dur else '—'} | {hms(ep['origem_inicio'], True)} → "
             f"{hms(ep['origem_fim'], True)} | {len(J['juncoes']) if J else '—'} | {status} |")
    # capítulos reais: início do 1º trecho de cada capítulo no vídeo editado
    inicio_trecho = {0: 0.0}
    if J:
        for j in J["juncoes"]:
            inicio_trecho[j["trecho"]] = j["t"]
    caps, ult = [], None
    for i, s in enumerate(ep["montagem"]):
        if s["capitulo"] != ult:
            t = inicio_trecho.get(i)
            if t is None:      # trecho colado ao anterior: estima pelo acumulado
                t = s["editado_inicio"]
            caps.append((t, s["capitulo"]))
            ult = s["capitulo"]
    caps[0] = (0.0, caps[0][1])
    caps = [c for k, c in enumerate(caps) if k == 0 or c[0] - caps[k - 1][0] >= 10]
    det = [f"## Parte {p} — {ep['titulo']}", "",
           f"- **Arquivo:** `{ep['arquivo']}`",
           f"- **Duração final (medida):** {hms(dur) if dur else '—'}"
           + (f" · {qc['resolucao']} {qc['fps']:.0f} fps · {qc['video']}/{qc['audio']}" if qc else ""),
           f"- **Trecho da live:** {hms(ep['origem_inicio'], True)} → {hms(ep['origem_fim'], True)} "
           f"({len(ep['montagem'])} trechos mantidos)",
           f"- **Título alternativo:** {ep.get('titulo_alternativo', '')}",
           *[f"- **Imagem-base da thumbnail{'' if k == 0 else f' (alternativa {k})'}:** "
             f"`{os.path.splitext(ep['arquivo'])[0]} - thumb base{'' if k == 0 else f' {k + 1}'}.png` — "
             f"{m.get('nota', '')} (live {hms(m['origem'], True)})" for k, m in enumerate(ep.get("thumb", []))],
           "", f"**Resumo:** {ep['resumo']}", "",
           "**Capítulos para a descrição do YouTube:**", "", "```"]
    det += [f"{hms(t)} {c}" for t, c in caps]
    det += ["```", ""]
    pres = [s for s in ep["montagem"] if s["decisao"].startswith("PRESERVAR")]
    if pres:
        det.append("**Preservado inteiro:** " + "; ".join(
            f"{s['motivo']} ({hms(s['origem_inicio'], True)})" for s in pres))
        det.append("")
    if qc:
        det.append(f"**Revisão automática:** decodificação {qc.get('decodificacao_completa', 'não feita')}, "
                   f"A/V {abs(qc['duracao_video'] - qc['duracao_audio']):.3f} s de diferença, "
                   f"{len(qc['pretos'])} telas pretas, {len(qc['silencios'])} silêncios ≥ 4 s, "
                   f"{len(qc['saltos_volume'])} degraus de som não suavizados.")
        for x in qc["problemas"]:
            det.append(f"- PROBLEMA: {x}")
        for x in qc["avisos"]:
            det.append(f"- aviso: {x}")
        det.append("")
    detalhes += det
L += ["", "Removido de propósito em toda a live:", ""] + [f"- {r}" for r in plano.get("removidos_relevantes", [])]
L += [""] + detalhes
if a.mudancas and os.path.exists(a.mudancas):
    L += ["", open(a.mudancas, encoding="utf-8").read()]
os.makedirs(os.path.dirname(a.saida), exist_ok=True)
open(a.saida, "w", encoding="utf-8").write("\n".join(L) + "\n")
print("Relatório:", a.saida)

"""EDITOR — validador do plano (V4). Transforma as regras do Estilo em checagens que BLOQUEIAM o render.

ERROS (bloqueiam): decisão REVISAR pendente; decisão desconhecida; trechos fora de ordem/sobrepostos;
borda cortando fala/diálogo; fim de episódio sem cena concluída; evento narrativo obrigatório (importância 3)
removido; evento mantido cujo contexto (depende_de) foi removido; travamento da live dentro de trecho mantido.
AVISOS (conferir): remoção de trecho com reação/cutscene sem motivo registrado; tempo morto ou menu acima
do limite do perfil; duração fora da faixa; dissolves em série ou demais.

Se não houver erros, grava no plano "validacao": {hash da montagem, data, avisos}. O montar_episodios.py só
renderiza plano validado com a montagem atual (qualquer mudança depois exige validar de novo).

Fontes (do próprio plano, ou por argumento): "transcricao", "audio" (áudio da fonte, para diálogo do jogo),
"analise" (analise.json), "narrativa" (narrativa.json), "perfil" (lista de perfis de config/perfis.json).

Uso: python Scripts/validar_plano.py Trabalho/plano_x.json [--transcricao T] [--audio A] [--analise A]
        [--narrativa N] [--sem-gravar]
"""
import argparse
import datetime
import hashlib
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import comum  # noqa: E402

DECISOES = {"PRESERVAR INTEGRALMENTE", "MANTER", "CONDENSAR", "ENCURTAR", "REMOVER", "REVISAR"}


def hash_montagem(plano):
    m = [[(round(s["origem_inicio"], 2), round(s["origem_fim"], 2), s.get("transicao"), s.get("audio_desloc", 0))
          for s in ep["montagem"]] for ep in plano["episodios"]]
    return hashlib.sha1(json.dumps(m).encode()).hexdigest()[:16]


def t_str(x):
    p = [float(v) for v in x.split(":")]
    return p[0] * 3600 + p[1] * 60 + p[2] if len(p) == 3 else p[0] * 60 + p[1]


def intervalos_removidos(plano):
    """removidos_relevantes: strings 'h:mm:ss–h:mm:ss: motivo' (formato antigo) ou {ini, fim, motivo}."""
    out = []
    for r in plano.get("removidos_relevantes", []):
        if isinstance(r, dict):
            out.append((float(r["ini"]), float(r["fim"])))
        else:
            for a, b in re.findall(r"(\d+:\d{2}(?::\d{2})?)\s*[–-]\s*(\d+:\d{2}(?::\d{2})?)", str(r)):
                out.append((t_str(a), t_str(b)))
    return out


def dentro(t0, t1, ivs, folga=1.0):
    return any(a - folga <= t0 and t1 <= b + folga for a, b in ivs)


def sobrepoe(t0, t1, ivs):
    return any(a < t1 and t0 < b for a, b in ivs)


def validar(plano, transcricao=None, audio=None, analise=None, narrativa=None):
    erros, avisos = [], []
    perf = comum.perfil(plano.get("perfil"))
    cfg = comum.projeto()
    eps = plano["episodios"]
    mantidos = [(s["origem_inicio"], s["origem_fim"]) for ep in eps for s in ep["montagem"]
                if s.get("decisao", "MANTER") != "REMOVER"]

    # ---- estrutura e decisões
    ant = -1.0
    for ep in eps:
        for i, s in enumerate(ep["montagem"]):
            d = s.get("decisao", "MANTER")
            if d not in DECISOES:
                erros.append(f"Parte {ep['parte']} trecho {i + 1}: decisão '{d}' desconhecida")
            if d == "REVISAR":
                erros.append(f"Parte {ep['parte']} trecho {i + 1} ({comum.hms(s['origem_inicio'])}): decisão REVISAR "
                             "pendente — fazer a 2ª análise (quadros densos + fala) e decidir")
            if s["origem_fim"] <= s["origem_inicio"]:
                erros.append(f"Parte {ep['parte']} trecho {i + 1}: fim antes do início")
            if s["origem_inicio"] < ant - 0.05:
                erros.append(f"Parte {ep['parte']} trecho {i + 1}: fora de ordem/sobreposto ao anterior")
            ant = s["origem_fim"]

    # ---- bordas: fala e diálogo do jogo (regra 2026-11-24)
    if transcricao:
        from bordas import Bordas
        B = Bordas(transcricao, audio, cfg.get("bordas", {}).get("margem_voz_db", 7.0))
        for ep in eps:
            M = ep["montagem"]
            for i, s in enumerate(M):
                colado_antes = i > 0 and abs(s["origem_inicio"] - M[i - 1]["origem_fim"]) < 0.05
                colado_depois = i + 1 < len(M) and abs(M[i + 1]["origem_inicio"] - s["origem_fim"]) < 0.05
                final = i == len(M) - 1
                desloc = float(s.get("audio_desloc", 0))
                for lado, x, colado in (("ini", s["origem_inicio"], colado_antes), ("fim", s["origem_fim"], colado_depois)):
                    if colado or (lado == "ini" and i == 0 and x < 1):
                        continue
                    if lado == "fim" and i + 1 < len(M) and float(M[i + 1].get("audio_desloc", 0)) > 0:
                        x += float(M[i + 1]["audio_desloc"])        # L-cut: o som continua além do corte
                    if lado == "ini" and desloc < 0:
                        x += desloc                                 # J-cut: o som entra antes da imagem
                    p = B.problema(x, lado)
                    prox = B._prox_inicio(x) - x
                    if not p and lado == "fim" and prox < (cfg.get("bordas", {}).get("pausa_fim_episodio", 1.5) * 0.8
                                                            if final else 0.4):
                        p = f"fala recomeça {prox:.2f}s depois do corte (conversa cortada)"
                    if p:
                        sug = B.inicio(x) if lado == "ini" else B.fim(x, final=final)
                        quem = "FIM DO EPISÓDIO" if final and lado == "fim" else f"trecho {i + 1} {lado}"
                        erros.append(f"Parte {ep['parte']} {quem} {comum.hms(x, True)}: {p} -> usar "
                                     f"{comum.hms(sug, True)} (Bordas.{'inicio' if lado == 'ini' else 'fim'})")
    else:
        avisos.append("sem transcrição: bordas de fala NÃO conferidas")

    # ---- narrativa
    if narrativa:
        nar = comum.carregar_json(narrativa, {})
        evs = {e["id"]: e for e in nar.get("eventos", [])}
        def mantido(e):
            meio = (e["t_ini"] + e["t_fim"]) / 2
            return sobrepoe(e["t_ini"], e["t_fim"], mantidos) and any(a <= meio <= b for a, b in mantidos)
        for e in evs.values():
            if e.get("importancia") == 3 and not mantido(e):
                erros.append(f"evento obrigatório {e['id']} removido ({comum.hms(e['t_ini'])}: {e.get('descricao', '')[:70]})")
        for e in evs.values():
            if not mantido(e):
                continue
            for d in e.get("depende_de", []):
                if d in evs and not mantido(evs[d]):
                    erros.append(f"contexto ausente: {e['id']} ({comum.hms(e['t_ini'])}) fica, mas depende de {d} "
                                 f"({comum.hms(evs[d]['t_ini'])}: {evs[d].get('descricao', '')[:60]}) que foi removido")

    # ---- sinais da análise audiovisual
    if analise:
        an = comum.carregar_json(analise, {})
        ev = an.get("eventos", {})
        rem_ok = intervalos_removidos(plano)
        ini_live, fim_live = eps[0]["montagem"][0]["origem_inicio"], eps[-1]["montagem"][-1]["origem_fim"]
        def removido(t0, t1):
            return ini_live <= t0 and t1 <= fim_live and not sobrepoe(t0, t1, mantidos)
        for t in ev.get("reacoes", []):
            if removido(t - 1, t + 1) and not dentro(t, t, rem_ok, 3):
                avisos.append(f"reação forte removida em {comum.hms(t)} sem motivo em removidos_relevantes — REVISAR")
        for a_, b_ in ev.get("cutscenes", []):
            if removido(a_, b_) and not dentro(a_, b_, rem_ok, 3):
                (erros if perf.get("preservar_cutscenes") else avisos).append(
                    f"cutscene {comum.hms(a_)}–{comum.hms(b_)} removida sem motivo registrado")
            elif sobrepoe(a_, b_, mantidos) and not dentro(a_, b_, mantidos, 0.5):
                avisos.append(f"cutscene {comum.hms(a_)}–{comum.hms(b_)} mantida só em parte — conferir diálogo")
        for a_, b_ in ev.get("travamentos", []):
            if sobrepoe(a_, b_, mantidos):
                (erros if b_ - a_ >= cfg.get("qc", {}).get("congelado_problema_s", 1.0) else avisos).append(
                    f"travamento da live {comum.hms(a_)} ({b_ - a_:.0f}s) dentro de trecho mantido — cortar ou cobrir")
        for a_, b_ in ev.get("tempo_morto", []):
            for x, y in mantidos:
                ov = min(b_, y) - max(a_, x)
                if ov > perf["tempo_morto_max_s"]:
                    avisos.append(f"ritmo: {ov:.0f}s de tempo morto mantido em {comum.hms(max(a_, x))} "
                                  f"(perfil {'+'.join(perf['_perfis'])}: máx {perf['tempo_morto_max_s']}s)")
        for a_, b_ in ev.get("menus", []):
            for x, y in mantidos:
                ov = min(b_, y) - max(a_, x)
                if ov > perf["menu_max_s"]:
                    avisos.append(f"ritmo: {ov:.0f}s de menu/mapa/tela parada mantidos em {comum.hms(max(a_, x))} "
                                  f"(máx {perf['menu_max_s']}s, salvo se houver conversa/história)")

    # ---- duração e transições por episódio
    ep_cfg = cfg.get("episodio", {})
    tr_cfg = cfg.get("transicoes", {})
    for k, ep in enumerate(eps):
        dur = sum(s["origem_fim"] - s["origem_inicio"] for s in ep["montagem"]) / 60
        ultimo = k == len(eps) - 1
        if dur > ep_cfg.get("tolerancia_minutos", 62) or (dur < ep_cfg.get("min_minutos", 50) - 5 and not ultimo):
            avisos.append(f"Parte {ep['parte']}: {dur:.1f} min (faixa {ep_cfg.get('min_minutos')}–{ep_cfg.get('max_minutos')})")
        tipos = [s.get("transicao", "corte") for s in ep["montagem"][1:]]
        nd = tipos.count("dissolve")
        if nd > perf.get("dissolves_por_episodio_max", tr_cfg.get("dissolves_por_episodio_max", 6)):
            avisos.append(f"Parte {ep['parte']}: {nd} dissolves (excesso)")
        for i in range(1, len(tipos)):
            if tipos[i] == tipos[i - 1] == "dissolve":
                avisos.append(f"Parte {ep['parte']}: dissolves seguidos nos trechos {i + 1}–{i + 2}")
    return erros, avisos


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("plano")
    ap.add_argument("--transcricao")
    ap.add_argument("--audio")
    ap.add_argument("--analise")
    ap.add_argument("--narrativa")
    ap.add_argument("--sem-gravar", action="store_true")
    a = ap.parse_args()
    plano = comum.carregar_json(a.plano)
    pega = lambda k, v: v or (plano.get(k) if plano.get(k) and os.path.exists(plano.get(k)) else None)  # noqa: E731
    erros, avisos = validar(plano, pega("transcricao", a.transcricao), pega("audio", a.audio),
                            pega("analise", a.analise), pega("narrativa", a.narrativa))
    for m in erros:
        print("  ERRO ", m)
    for m in avisos:
        print("  AVISO", m)
    print(f"{len(erros)} erro(s), {len(avisos)} aviso(s)")
    if not erros and not a.sem_gravar:
        plano["validacao"] = {"hash": hash_montagem(plano), "em": datetime.datetime.now().isoformat(timespec="seconds"),
                              "avisos": avisos}
        comum.salvar_json(a.plano, plano)
        print("Plano VALIDADO — liberado para o render.")
    raise SystemExit(1 if erros else 0)


if __name__ == "__main__":
    main()

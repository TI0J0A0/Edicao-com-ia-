"""REVISOR INDEPENDENTE (V4) — avalia o resultado como espectador, separado de quem decidiu os cortes.

Não reaproveita os motivos do plano: olha só o que ficou, o que saiu e o vídeo renderizado.
Técnico : lê o qc.json de cada parte (verificar_episodio.py) — sem QC = PENDENTE, nunca aprovado.
Editorial:
  - falas/diálogos interrompidos nas bordas e no fim (mesmas regras do validador);
  - encerramento abrupto (cutscene, reação ou fala acontecendo logo depois do fim do episódio);
  - começo fraco (primeiro minuto sem fala e com baixa intensidade);
  - possível JUMP CUT (mesma cena, salto curto: personagem "pula" na tela);
  - ritmo arrastado (minutos seguidos de baixa intensidade sem fala) e tempo morto acima do perfil;
  - repetições (trechos mantidos com falas muito parecidas, a mais de 5 min um do outro);
  - momentos fortes removidos (reação/cutscene/pico de intensidade fora de removidos_relevantes);
  - contexto ausente (nome próprio que só foi apresentado num trecho removido);
  - continuidade entre episódios (buraco grande ou cena forte perdida entre o fim de uma parte e a próxima);
  - efeitos (zoom acima do teto, zoom/texto em perfil de terror, excesso de textos).
Cada achado: local (parte + tempo no episódio + tempo na live), causa provável e correção proposta.
Veredito: APROVADO só com zero problemas E QC presente de todas as partes.

Uso: python Scripts/revisor_editorial.py Trabalho/plano_x.json [--pasta-render Trabalho/ep_plano_x] [--saida rel.md]
"""
import argparse
import os
import re
import sys
import unicodedata

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import comum  # noqa: E402
import validar_plano  # noqa: E402

COMUNS = set("""Mano Cara Meu Nossa Gente Vamos Vou Agora Então Porque Aqui Isso Esse Essa Este Esta Eu Ele Ela Você
Tipo Olha Calma Pronto Beleza Certo Caraca Caramba Deus Senhor Obrigado Valeu Bom Boa Não Sim Mas Que Quando Onde
Como Porra Velho Cadê Ah Oh Ai Eita Opa Uai Tá Né Sério Muito Mais Pra Para Com Sem Uma Um Dois Três Chat""".split())


def norm(t):
    t = unicodedata.normalize("NFKD", t.lower())
    return re.sub(r"[^a-z0-9 ]+", " ", "".join(c for c in t if not unicodedata.combining(c))).split()


def trigramas(ws):
    return {tuple(ws[i:i + 3]) for i in range(len(ws) - 2)}


class Revisor:
    def __init__(self, plano_p, pasta_render=None):
        self.plano = comum.carregar_json(plano_p)
        self.pasta = pasta_render or os.path.join("Trabalho", "ep_" + os.path.splitext(os.path.basename(plano_p))[0])
        p = self.plano
        ok = lambda k: p.get(k) if p.get(k) and os.path.exists(p.get(k)) else None  # noqa: E731
        self.tr_p, self.audio, self.an_p, self.nar_p = ok("transcricao"), ok("audio"), ok("analise"), ok("narrativa")
        self.tr = comum.carregar_json(self.tr_p, {}) if self.tr_p else {}
        self.an = comum.carregar_json(self.an_p, {}) if self.an_p else {}
        self.perf = comum.perfil(p.get("perfil"))
        self.achados = []          # (gravidade, parte, t_ep, t_live, causa, correcao)
        self.pendencias = []

    def add(self, grav, parte, t_live, causa, correcao, t_ep=None):
        if t_ep is None and parte and t_live is not None:
            t_ep = self.t_editado(parte, t_live)
        self.achados.append((grav, parte, t_ep, t_live, causa, correcao))

    def t_editado(self, parte, t):
        ep = next((e for e in self.plano["episodios"] if e["parte"] == parte), None)
        if not ep:
            return None
        acum = 0.0
        for s in ep["montagem"]:
            if s["origem_inicio"] - 0.5 <= t <= s["origem_fim"] + 0.5:
                return acum + max(0.0, t - s["origem_inicio"])
            acum += s["origem_fim"] - s["origem_inicio"]
        return acum

    # ---------------------------------------------------------------- técnico
    def tecnico(self):
        for ep in self.plano["episodios"]:
            qc = comum.carregar_json(os.path.join(self.pasta, f"parte_{ep['parte']:02d}", "qc.json"))
            if not qc:
                self.pendencias.append(f"Parte {ep['parte']}: sem qc.json (render/verificar_episodio não rodou)")
                continue
            for m in qc.get("problemas", []):
                self.add("PROBLEMA", ep["parte"], None, f"técnico: {m}", "corrigir o trecho e renderizar a parte de "
                         "novo (só os pedaços alterados são recodificados)", t_ep=None)
            for m in qc.get("avisos", []):
                self.add("AVISO", ep["parte"], None, f"técnico: {m}", "conferir no painel/ouvindo", t_ep=None)

    # ---------------------------------------------------------------- editorial
    def editorial(self):
        p, an = self.plano, self.an
        eps = p["episodios"]
        mantidos = [(s["origem_inicio"], s["origem_fim"]) for e in eps for s in e["montagem"]]
        erros, _ = validar_plano.validar(p, self.tr_p, self.audio, None, self.nar_p)
        for m in erros:
            parte = int(re.search(r"Parte (\d+)", m).group(1)) if re.search(r"Parte (\d+)", m) else None
            self.add("PROBLEMA", parte, None, m, "ajustar a borda no gerador do plano (Bordas) e validar de novo",
                     t_ep=None)
        ev = an.get("eventos", {})
        ps = an.get("por_segundo", {})
        T0 = an.get("inicio", 0.0)

        def sinal(nome, t):
            i = int(t - T0)
            arr = ps.get(nome, [])
            return arr[i] if 0 <= i < len(arr) else None

        frases = [(f["inicio"], f["fim"], f["texto"]) for f in self.tr.get("frases", [])]
        for k, ep in enumerate(eps):
            M = ep["montagem"]
            fim = M[-1]["origem_fim"]
            # encerramento abrupto
            if ev:
                if any(a_ < fim < b_ - 1 for a_, b_ in ev.get("cutscenes", [])):
                    self.add("PROBLEMA", ep["parte"], fim, "episódio termina NO MEIO de uma cutscene",
                             "estender o último trecho até o fim da cutscene")
                if any(fim < r <= fim + 3 for r in ev.get("reacoes", [])):
                    self.add("AVISO", ep["parte"], fim, "reação forte logo depois do fim do episódio",
                             "estender 3–5 s para incluir a reação (ou começar a próxima parte por ela)")
            prox_fala = next((a_ for a_, _, _ in frases if a_ > fim), None)
            if prox_fala is not None and prox_fala - fim < 1.2:
                self.add("PROBLEMA", ep["parte"], fim, f"fala recomeça {prox_fala - fim:.1f}s após o fim do episódio",
                         "Bordas.fim(final=True) — fechar a conversa")
            # começo fraco
            ini = M[0]["origem_inicio"]
            if ps:
                fala1 = sum(1 for t in range(int(ini), int(ini) + 60) if sinal("fala", t))
                js = [j for j in an.get("janelas", []) if ini <= j["t"] < ini + 60]
                inten = max((j["intensidade"] for j in js), default=0)
                if fala1 < 5 and inten < 0.35:
                    self.add("AVISO", ep["parte"], ini, f"começo fraco: 1º minuto quase sem fala (intensidade {inten})",
                             "abrir na primeira ação/fala relevante (gancho real, sem spoiler)")
            # continuidade entre episódios
            if k + 1 < len(eps):
                nxt = eps[k + 1]["montagem"][0]["origem_inicio"]
                buraco = nxt - fim
                fortes = [r for r in ev.get("reacoes", []) if fim < r < nxt]
                if buraco > 300:
                    self.add("AVISO", ep["parte"], fim, f"{buraco / 60:.0f} min da live entre esta parte e a próxima",
                             "conferir se nada da história ficou de fora; se necessário, contexto curto no início da próxima")
                if fortes and not any(validar_plano.dentro(r, r, validar_plano.intervalos_removidos(p), 3) for r in fortes):
                    self.add("AVISO", ep["parte"], fortes[0], "reação forte perdida entre duas partes",
                             "incluir no fim desta parte ou no começo da próxima")
            # jump cuts e efeitos
            from transicoes import quadro, diferenca
            for i in range(1, len(M)):
                a_, b_ = M[i - 1], M[i]
                salto = b_["origem_inicio"] - a_["origem_fim"]
                if 0.05 < salto < 20 and b_.get("transicao", "corte") == "corte":
                    d = diferenca(quadro(p["video"], a_["origem_fim"] - 0.05), quadro(p["video"], b_["origem_inicio"] + 0.02),
                                  p.get("facecam"))
                    if d is not None and 6 < d < 22:
                        self.add("AVISO", ep["parte"], b_["origem_inicio"],
                                 f"possível jump cut: mesma cena, salto de {salto:.1f}s (dif {d:.0f})",
                                 "mover o corte para troca de câmera/menu/movimento ou manter os segundos removidos")
            for i, s in enumerate(M):
                for z in s.get("zooms", []):
                    if float(z.get("escala", 1.08)) > comum.projeto().get("render", {}).get("zoom_max", 1.15):
                        self.add("PROBLEMA", ep["parte"], s["origem_inicio"], "zoom acima do teto de qualidade",
                                 "reduzir a escala")
                    if self.perf.get("evitar_efeitos"):
                        self.add("AVISO", ep["parte"], s["origem_inicio"], "zoom num perfil que evita efeitos (terror)",
                                 "tirar, salvo se tiver função clara")
            ntxt = sum(len(s.get("textos", [])) for s in M)
            dur = sum(s["origem_fim"] - s["origem_inicio"] for s in M) / 60
            if dur and ntxt / dur > 0.5:
                self.add("AVISO", ep["parte"], None, f"{ntxt} textos em {dur:.0f} min (excesso)",
                         "manter só os que explicam ou realçam algo real", t_ep=None)
            # ritmo arrastado: 3+ min seguidos de janelas tempo_morto/deslocamento sem fala
            if an.get("janelas"):
                seq = 0
                for j in an["janelas"]:
                    if not any(a_ <= j["t"] < b_ for a_, b_ in [(s["origem_inicio"], s["origem_fim"]) for s in M]):
                        seq = 0
                        continue
                    lento = set(j["tags"]) <= {"tempo_morto", "deslocamento"} and j["intensidade"] < 0.3
                    seq = seq + 10 if lento else 0
                    if seq == 180:
                        self.add("AVISO", ep["parte"], j["t"] - 170, "3 min seguidos de deslocamento/tempo morto sem fala",
                                 f"condensar (perfil {'+'.join(self.perf['_perfis'])}: tempo morto máx "
                                 f"{self.perf['tempo_morto_max_s']}s)")
        # repetições
        if frases:
            blocos = []
            for a_, b_ in mantidos:
                ws = [w for x, y, t in frases if a_ <= x < b_ for w in norm(t)]
                for c in range(0, len(ws), 120):
                    blocos.append((a_, trigramas(ws[c:c + 120])))
            lim = self.perf.get("repeticao_similaridade", 0.55)
            vistos = set()
            for i in range(len(blocos)):
                for j in range(i + 1, len(blocos)):
                    ta, A = blocos[i]
                    tb, Bset = blocos[j]
                    if abs(tb - ta) < 300 or len(A) < 25 or len(Bset) < 25:
                        continue
                    jac = len(A & Bset) / len(A | Bset)
                    if jac > lim and (ta, tb) not in vistos:
                        vistos.add((ta, tb))
                        parte = next((e["parte"] for e in eps for s in e["montagem"] if s["origem_inicio"] <= tb <= s["origem_fim"]), None)
                        self.add("AVISO", parte, tb, f"repetição: fala muito parecida com {comum.hms(ta)} ({jac:.0%})",
                                 "manter só a melhor versão")
        # momentos fortes removidos e contexto ausente
        rem_ok = validar_plano.intervalos_removidos(p)
        ini_live, fim_live = mantidos[0][0], mantidos[-1][1]
        removido = lambda a_, b_: ini_live <= a_ and b_ <= fim_live and not validar_plano.sobrepoe(a_, b_, mantidos)  # noqa: E731
        for j in an.get("janelas", []):
            if j["intensidade"] >= 0.75 and removido(j["t"], j["t"] + 10) and not validar_plano.dentro(j["t"], j["t"] + 10, rem_ok, 5):
                self.add("AVISO", None, j["t"], f"pico de intensidade removido ({j['intensidade']}, {' '.join(j['tags'])})",
                         "rever: pode ser um momento forte (luta, susto, risada)", t_ep=None)
        if frases:
            primeiro = {}
            for a_, b_, t in frases:
                toks = t.split()
                for k2, w in enumerate(toks):
                    w2 = re.sub(r"[^\wÀ-ÿ]", "", w)
                    if k2 and len(w2) > 3 and w2[:1].isupper() and w2 not in COMUNS and w2 not in primeiro:
                        primeiro[w2] = a_
            for nome, t1 in primeiro.items():
                if removido(t1, t1 + 0.5):
                    depois = [a_ for a_, _, t in frases if a_ > t1 and nome in t and validar_plano.sobrepoe(a_, a_ + 0.5, mantidos)]
                    if len(depois) >= 2:
                        parte = next((e["parte"] for e in eps for s in e["montagem"] if s["origem_inicio"] <= depois[0] <= s["origem_fim"]), None)
                        self.add("AVISO", parte, depois[0], f"contexto: '{nome}' é citado, mas foi apresentado em "
                                 f"{comum.hms(t1)}, num trecho removido", "manter a apresentação ou um trecho curto que explique")

    def relatorio(self, saida=None):
        probs = [a for a in self.achados if a[0] == "PROBLEMA"]
        veredito = ("REPROVADO" if probs else "PENDENTE" if self.pendencias else "APROVADO")
        L = [f"# Revisão independente — {veredito}", "",
             f"Plano: `{self.plano.get('video')}` · perfil {'+'.join(self.perf['_perfis'])} · "
             f"{len(probs)} problema(s), {len(self.achados) - len(probs)} aviso(s)", ""]
        if self.pendencias:
            L += ["**Pendências (não dá para aprovar):**", ""] + [f"- {x}" for x in self.pendencias] + [""]
        if self.achados:
            L += ["| Gravidade | Parte | No episódio | Na live | Causa provável | Correção proposta |", "|---|---|---|---|---|---|"]
            for g, parte, te, tl, causa, corr in sorted(self.achados, key=lambda a: (a[0] != "PROBLEMA", a[1] or 0, a[3] or 0)):
                L.append(f"| {g} | {parte or '—'} | {comum.hms(te) if te is not None else '—'} | "
                         f"{comum.hms(tl) if tl is not None else '—'} | {causa.replace('|', '/')} | {corr.replace('|', '/')} |")
        txt = "\n".join(L) + "\n"
        if saida:
            open(saida, "w", encoding="utf-8").write(txt)
        return veredito, txt


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("plano")
    ap.add_argument("--pasta-render")
    ap.add_argument("--saida")
    a = ap.parse_args()
    r = Revisor(a.plano, a.pasta_render)
    r.tecnico()
    r.editorial()
    veredito, txt = r.relatorio(a.saida)
    print(txt)
    raise SystemExit(0 if veredito == "APROVADO" else 1)


if __name__ == "__main__":
    main()

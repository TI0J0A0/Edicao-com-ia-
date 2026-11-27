"""Ritmo V4.1 (João 2026-11-26, referência: séries longas de GTA 6 no YouTube — quase nenhuma pausa sem som,
episódio abre direto no jogo/fala).

1) enxugar(): corta SILÊNCIO REAL (mix inteira < -50 dB por >= 3 s: tela de mapa, menu, carregamento, pausa)
   de dentro dos trechos mantidos, deixando um respiro de 0,4 s de cada lado.
   NUNCA corta: fala transcrita (do João OU diálogo do jogo), voz detectada no áudio (diálogo não transcrito),
   cutscenes da análise, perfis com "preservar_silencio_tenso" (terror). Diálogo/cutscene não fica a -50 dB:
   o jogo normal fica entre -30 e -40 dB, mapa/menu/carregamento entre -70 e -110 dB (medido na live 2940902491).
2) abertura(): o 1º trecho de cada episódio começa depois de tela preta/carregamento mudo do começo.

Uso no gerador do plano (antes de calcular os zooms, que são relativos ao trecho):
    R = ritmo.Ritmo(AUDIO, TR, analise=f"{CACHE}/analise/analise.json", cache=CACHE, perfil=PERFIL)
    segs = R.abertura(R.enxugar(R.abertura(segs)))
"""
import json
import os
import re
import subprocess

import comum


def _cfg():
    c = {"silencio_db": -50.0, "silencio_min_s": 3.0, "respiro_s": 0.4, "peca_min_s": 2.0, "protecao_fala_s": 0.15}
    c.update(comum.projeto().get("ritmo", {}))
    return c


def detectar_silencios(audio, db, min_s, cache=None):
    """silêncios da mix inteira (fonte), com cache em <cache>/silencios_<db>_<min>.json"""
    cp = os.path.join(cache, f"silencios_{int(abs(db))}db_{min_s:g}s.json") if cache else None
    if cp and os.path.exists(cp):
        return [tuple(x) for x in json.load(open(cp, encoding="utf-8"))]
    log = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", audio, "-vn", "-af",
                          f"silencedetect=n={db}dB:d={min_s}", "-f", "null", "-"],
                         capture_output=True, text=True, encoding="utf-8", errors="replace").stderr
    ini = [float(x) for x in re.findall(r"silence_start: (-?[\d.]+)", log)]
    fim = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", log)]
    sil = [(max(0.0, a), b) for a, b in zip(ini, fim)]
    if cp:
        json.dump(sil, open(cp, "w", encoding="utf-8"))
    return sil


class Ritmo:
    def __init__(self, audio, transcricao, analise=None, cache=None, perfil=None):
        self.c = _cfg()
        self.perf = comum.perfil(perfil)
        self.sil = detectar_silencios(audio, self.c["silencio_db"], self.c["silencio_min_s"], cache)
        tr = comum.carregar_json(transcricao, {}) if isinstance(transcricao, str) else (transcricao or {})
        # palavras (não frases: a frase do Whisper costuma "vazar" uns décimos para dentro do silêncio vizinho)
        self.falas = [(w["inicio"], w["fim"]) for f in tr.get("frases", []) for w in (f.get("palavras") or [])] or                      [(f["inicio"], f["fim"]) for f in tr.get("frases", [])]
        an = comum.carregar_json(analise, {}) if isinstance(analise, str) else (analise or {})
        ev = an.get("eventos", {})
        self.cutscenes = [tuple(x) for x in ev.get("cutscenes", [])]
        self.pretos = [tuple(x) for x in ev.get("tela_preta", [])]
        ps, t0 = an.get("por_segundo", {}), an.get("inicio", 0.0)
        # segundos com fala/voz detectada pela análise (por_segundo["fala"] = 1), para diálogo não transcrito
        self.voz = {int(t0) + i for i, v in enumerate(ps.get("fala", [])) if v == 1}
        self.cortes = []        # registro (para o relatório): (ini, fim, capitulo)

    def _protegido(self, a, b):
        m = self.c["protecao_fala_s"]
        if any(fa - m < b and a < fb + m for fa, fb in self.falas):
            return "fala"
        if any(ca - 1 < b and a < cb + 1 for ca, cb in self.cutscenes):
            return "cutscene"
        if any(int(a) < s < int(b) for s in self.voz):
            return "voz"
        return None

    def _corte_possivel(self, sa, sb):
        """intervalo cortável dentro do silêncio (sa, sb) — None se protegido ou curto"""
        r, m = self.c["respiro_s"], self.c["protecao_fala_s"]
        minimo = self.c["silencio_min_s"] - 2 * r
        if any(ca - 1 < sb and sa < cb + 1 for ca, cb in self.cutscenes):
            return None
        # palavra dentro do silêncio (fala baixa, ex.: João longe do microfone): corta só o maior vão sem palavra,
        # sempre com o respiro antes e depois
        livres, cur = [], sa
        for fa, fb in sorted(w for w in self.falas if w[0] - m < sb and sa < w[1] + m):
            livres.append((cur, fa - m))
            cur = max(cur, fb + m)
        livres.append((cur, sb))
        for x, y in sorted(livres, key=lambda v: v[0] - v[1]):
            a, b = x + r, y - r
            if b - a >= minimo and not self._protegido(a, b):
                return round(a, 2), round(b, 2)
        return None

    def abertura(self, segs):
        """1º trecho do episódio: pula silêncio/tela preta do começo (carregamento mudo)."""
        if not segs:
            return segs
        s = dict(segs[0])
        a = s["origem_inicio"]
        for _ in range(3):
            prox = next(((x, y) for x, y in self.sil + self.pretos if x - 0.3 <= a < y - 0.5), None)
            if not prox or self._protegido(a, prox[1] - self.c["respiro_s"]):
                break
            a = round(prox[1] - self.c["respiro_s"], 2)
        if a > s["origem_inicio"] and s["origem_fim"] - a >= self.c["peca_min_s"]:
            self.cortes.append((s["origem_inicio"], a, s.get("capitulo", "")))
            s["origem_inicio"] = a
            s["motivo"] = s.get("motivo", "") + " (abre direto no jogo: sem carregamento mudo)"
        segs = [s] + list(segs[1:])
        # pedacinho solto em TELA PRETA antes do 1º silêncio cortado (ex.: live 26/11 abre com "Incrível, mano" no
        # preto e 12 s mudos antes de "Incrível como já temos quase 40 horas"): o episódio abre na fala seguinte.
        # Só frase COMPLETA (o silêncio depois dela é >= 3 s), nunca no meio de fala.
        if len(segs) > 1:
            p0, p1 = segs[0], segs[1]
            d0 = p0["origem_fim"] - p0["origem_inicio"]
            preto = sum(max(0.0, min(y, p0["origem_fim"]) - max(x, p0["origem_inicio"])) for x, y in self.pretos)
            if d0 < 4.0 and preto >= 0.6 * d0 and p1["origem_inicio"] - p0["origem_fim"] >= self.c["silencio_min_s"] - 1:
                self.cortes.append((p0["origem_inicio"], p1["origem_inicio"], p0.get("capitulo", "")))
                p1 = dict(p1, transicao=p0.get("transicao", "corte"))
                segs = [p1] + segs[2:]
        return segs

    def enxugar(self, segs):
        if self.perf.get("preservar_silencio_tenso"):
            return segs
        out = []
        for s in segs:
            a0, b0 = s["origem_inicio"], s["origem_fim"]
            cortes = [c for c in (self._corte_possivel(x, y) for x, y in self.sil if a0 < y and x < b0) if c]
            cortes = [(max(x, a0), min(y, b0)) for x, y in cortes]
            pedacos, cur = [], a0
            for x, y in cortes:
                if x <= a0 + 0.05:          # silêncio no começo do trecho: começa depois
                    cur = max(cur, y)
                    continue
                if y >= b0 - 0.05:          # silêncio no fim do trecho: termina antes
                    pedacos.append((cur, x))
                    cur = None
                    break
                pedacos.append((cur, x))
                cur = y
            if cur is not None:
                pedacos.append((cur, b0))
            pedacos = [(x, y) for x, y in pedacos if y - x >= self.c["peca_min_s"]] or [(a0, b0)]
            if len(pedacos) == 1 and pedacos[0] == (a0, b0):
                out.append(s)
                continue
            for j, (x, y) in enumerate(pedacos):
                n = dict(s)
                n["origem_inicio"], n["origem_fim"] = round(x, 2), round(y, 2)
                if j:
                    n["transicao"] = "corte"
                    n["motivo"] = s.get("motivo", "") + " (sem o silêncio de mapa/menu)"
                    n.pop("transicao_motivo", None)
                n.pop("zooms", None)
                n["_ritmo_ini"], n["_ritmo_fim"] = abs(x - a0) > 0.05, abs(y - b0) > 0.05
                out.append(n)
            prev = a0
            for x, y in pedacos:
                if x - prev > 0.05:
                    self.cortes.append((prev, x, s.get("capitulo", "")))
                prev = y
            if b0 - prev > 0.05:
                self.cortes.append((prev, b0, s.get("capitulo", "")))
        # emenda feita DENTRO do silêncio: os dois lados já estão mudos por >= respiro, então o crossfade de áudio
        # tem de ser curto. O crossfade adaptativo (até 1 s, por causa do "degrau" silêncio x jogo) misturava a
        # frase anterior com a seguinte (QC da Parte 1 de teste, 2026-11-26).
        xf = round(min(0.3, 0.75 * self.c["respiro_s"] * 2), 2)
        for i, n in enumerate(out):
            if i and (out[i - 1].get("_ritmo_fim") or n.get("_ritmo_ini")):
                n["dur_transicao"] = xf
        for n in out:
            n.pop("_ritmo_ini", None)
            n.pop("_ritmo_fim", None)
        return out

    def resumo(self):
        tot = sum(b - a for a, b, _ in self.cortes)
        return f"ritmo: {len(self.cortes)} silêncio(s) de mapa/menu/carregamento cortado(s), {tot:.0f} s no total"


def silencios_restantes(plano, audio=None, cache=None):
    """para o validador: silêncios cortáveis que ainda estão dentro dos trechos (não protegidos)."""
    R = Ritmo(audio or plano.get("audio"), plano.get("transcricao"), plano.get("analise"), cache, plano.get("perfil"))
    if R.perf.get("preservar_silencio_tenso"):
        return []
    res = []
    for ep in plano["episodios"]:
        for i, s in enumerate(ep["montagem"]):
            for x, y in R.sil:
                if s["origem_inicio"] < y and x < s["origem_fim"]:
                    c = R._corte_possivel(max(x, s["origem_inicio"]), min(y, s["origem_fim"]))
                    if c and c[1] - c[0] >= R.c["silencio_min_s"] - 2 * R.c["respiro_s"]:
                        res.append((ep["parte"], i + 1, c[0], c[1]))
    return res

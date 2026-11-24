"""Bordas de corte que NUNCA cortam fala (regra do João, 2026-11-24).

"nunca corte uma fala ou diálogos do jogo, principalmente no final dos vídeos"

Duas fontes de verdade, usadas juntas:
1. Transcrição (frases do Whisper): a borda nunca cai dentro de uma frase. Início recua para antes da frase,
   fim avança para depois dela. Se a frase seguinte começa logo em seguida (conversa encadeada, < 0,7 s),
   o fim continua avançando até uma pausa de verdade.
2. Energia de voz no áudio da fonte (banda 300–3400 Hz, janelas de 50 ms): pega diálogo do jogo que o
   Whisper não transcreveu (inglês, música por cima). A borda só fica onde a energia está perto do fundo.

Fim de EPISÓDIO (final=True) exige pausa maior (1,5 s) e pode avançar até 40 s, para fechar a cena inteira.

Uso nos geradores de plano:
    import sys; sys.path.insert(0, "Scripts"); from bordas import Bordas
    B = Bordas("Trabalho/<transcricao>.json", "Trabalho/longo_x/audio_x.mp4")
    ini = B.inicio(t_ini); fim = B.fim(t_fim, final=(é o último trecho do episódio))
Verificação de um plano pronto: python Scripts/checar_bordas.py <plano.json> <transcricao.json> <audio>
"""
import json
import math
import re
import subprocess

JANELA = 0.05          # 50 ms por amostra de energia


def energia_voz(audio, t0, dur):
    """lista de dB (RMS na banda de voz) a cada 50 ms, de t0 até t0+dur, no áudio da fonte."""
    t0 = max(0.0, t0)
    r = subprocess.run(
        ["ffmpeg", "-hide_banner", "-nostats", "-ss", f"{t0:.3f}", "-t", f"{dur:.3f}", "-i", audio, "-vn",
         "-af", "pan=mono|c0=0.5*c0+0.5*c1,highpass=f=300,lowpass=f=3400,aresample=8000,"
                "asetnsamples=n=400:p=0,astats=metadata=1:reset=1,"
                "ametadata=print:key=lavfi.astats.Overall.RMS_level:file=-",
         "-f", "null", "-"], capture_output=True, text=True, encoding="utf-8", errors="ignore")
    out = []
    for m in re.finditer(r"RMS_level=(-?[\d.]+|-inf|inf)", r.stdout):
        try:
            v = float(m.group(1))
        except ValueError:
            v = -90.0
        out.append(max(-90.0, v if math.isfinite(v) else -90.0))
    return t0, out


class Bordas:
    def __init__(self, transcricao, audio=None, margem_db=7.0):
        d = json.load(open(transcricao, encoding="utf-8"))
        self.dur = d["duracao"]
        self.frases = sorted(((f["inicio"], f["fim"]) for f in d["frases"]), key=lambda x: x[0])
        self.audio = audio
        self.margem = margem_db

    # ---------- transcrição
    def _frase_em(self, x, folga=0.15):
        for a, b in self.frases:
            if a - folga <= x <= b + folga:
                return a, b
            if a > x + folga:
                break
        return None

    def _prox_inicio(self, x):
        for a, _ in self.frases:
            if a > x:
                return a
        return self.dur

    def _ant_fim(self, x):
        ant = 0.0
        for a, b in self.frases:
            if b < x:
                ant = b
            else:
                break
        return ant

    # ---------- áudio
    def _quieto(self, x, lado, limite):
        """procura, a partir de x, no sentido permitido, o primeiro ponto com 0,3 s de energia de voz
        perto do fundo. Devolve o ponto ou None."""
        if not self.audio:
            return x
        if lado == "fim":
            t0, ser = energia_voz(self.audio, x - 6, limite + 6)
        else:
            t0, ser = energia_voz(self.audio, x - limite, limite + 6)
        if len(ser) < 20:
            return x
        fundo = sorted(ser)[len(ser) // 5]           # percentil 20 = som do jogo sem fala
        teto = fundo + self.margem
        k = 6                                           # 0,3 s
        idx = int(round((x - t0) / JANELA))
        rng = range(idx, len(ser) - k) if lado == "fim" else range(idx, k, -1)
        for i in rng:
            bloco = ser[i - k // 2:i + k // 2] if i >= k // 2 else ser[:k]
            if bloco and max(bloco) <= teto:
                return round(t0 + i * JANELA, 2)
        return None

    # ---------- API
    def inicio(self, x, recuo_max=8.0):
        """início de trecho: nunca no meio de frase; recua para a pausa antes da frase."""
        x0 = x
        f = self._frase_em(x)
        if f:
            x = max(f[0] - 0.35, (self._ant_fim(f[0]) + f[0]) / 2)
        q = self._quieto(x, "ini", recuo_max)
        if q is not None and x0 - q <= recuo_max:
            f = self._frase_em(q)
            x = max(f[0] - 0.35, (self._ant_fim(f[0]) + f[0]) / 2) if f else q
        return round(max(0.0, x), 2)

    def fim(self, x, final=False):
        """fim de trecho: nunca no meio de frase nem de conversa encadeada. final=True (fim do episódio)
        pede pausa de 1,5 s depois e pode avançar até 40 s."""
        pausa = 1.5 if final else 0.7
        avanco_max = 40.0 if final else 12.0
        x0 = x
        for _ in range(60):
            f = self._frase_em(x)
            if f:
                x = f[1] + 0.05
            prox = self._prox_inicio(x)
            if prox - x >= pausa or x - x0 > avanco_max:
                break
            x = prox + 0.01                             # conversa continua: inclui a próxima frase
        q = self._quieto(x, "fim", avanco_max - (x - x0) + 2)
        if q is not None and q - x0 <= avanco_max + 2:
            x = q if not self._frase_em(q) else self._frase_em(q)[1] + 0.05
        fim = min(x + 0.35, (x + self._prox_inicio(x)) / 2) if self._prox_inicio(x) > x else x + 0.35
        return round(min(fim, self.dur - 0.05), 2)

    def problema(self, x, lado):
        """texto do problema se a borda corta fala; None se está limpa."""
        f = self._frase_em(x, folga=0.05)
        if f:
            return f"dentro da frase {f[0]:.2f}–{f[1]:.2f}"
        if self.audio:
            t0, ser = energia_voz(self.audio, x - 6, 12)
            if len(ser) > 40:
                fundo = sorted(ser)[len(ser) // 5]
                i = int(round((x - t0) / JANELA))
                perto = ser[max(0, i - 3):i + 3]
                if perto and max(perto) > fundo + self.margem + 3:
                    return f"voz no áudio na borda ({max(perto) - fundo:+.0f} dB acima do fundo) — diálogo do jogo?"
        return None

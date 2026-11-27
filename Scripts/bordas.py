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


def fundo_robusto(ser):
    """som de fundo do jogo: percentil 25 da energia de voz IGNORANDO silêncio digital (< -70 dB: menu de pausa,
    loading). Bug achado em 2026-11-26: com um menu mudo nos 30 s anteriores o percentil 10 caía para -89 dB e
    qualquer som do jogo virava "voz"."""
    vivos = sorted(v for v in ser if v > -70)
    if len(vivos) < max(20, len(ser) * 0.3):
        vivos = sorted(ser)
    return vivos[len(vivos) // 4] if len(vivos) > 20 else None


class Bordas:
    def __init__(self, transcricao, audio=None, margem_db=7.0):
        d = json.load(open(transcricao, encoding="utf-8"))
        self.dur = d["duracao"]
        self.frases = sorted(((f["inicio"], f["fim"]) for f in d["frases"]), key=lambda x: x[0])
        self.audio = audio
        self.margem = margem_db
        self._fundos = {}

    def _fundo(self, x):
        """som de fundo do jogo perto de x = percentil 10 da energia de voz nos 30 s ANTES de x.
        Mesma régua do QC (verificar_episodio): janela curta no meio de conversa achava o "fundo" alto demais."""
        k = round(x / 5)
        if k not in self._fundos:
            _, ser = energia_voz(self.audio, max(0.0, k * 5 - 30), 30)
            self._fundos[k] = fundo_robusto(ser)
        return self._fundos[k]

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
            if a >= x - 1e-6:
                return a
        return self.dur

    def _sair_da_fala(self, t):
        """avança t para depois de QUALQUER frase que o contenha (frases coladas: uma termina onde a outra
        começa — bug achado na comparação de 2026-11-26)."""
        mudou = True
        while mudou:
            mudou = False
            for a, b in self.frases:
                if a - 0.02 <= t < b + 0.05:
                    t, mudou = b + 0.05, True
                if a > t + 1:
                    break
        return t

    def _ant_fim(self, x):
        ant = 0.0
        for a, b in self.frases:
            if b < x:
                ant = b
            else:
                break
        return ant

    # ---------- áudio
    def _quieto(self, x, lado, limite, pausa=0.7):
        """procura, a partir de x, no sentido permitido, uma PAUSA de verdade na voz (>= pausa s perto do fundo).
        Pausa curta entre palavras (vírgula, respiração ~0,3 s) não conta — foi o que deixava o corte no meio
        de uma fala de personagem. fim: devolve o começo da pausa (+0,15 s); ini: o fim da pausa (-0,15 s)."""
        if not self.audio:
            return x
        if lado == "fim":
            t0, ser = energia_voz(self.audio, x - 8, limite + 8 + pausa)
        else:
            t0, ser = energia_voz(self.audio, x - limite - pausa, limite + pausa + 8)
        if len(ser) < 20:
            return x
        fundo = self._fundo(x)
        if fundo is None:
            fundo = sorted(ser)[len(ser) // 10]
        teto = fundo + self.margem
        k = max(6, int(round(pausa / JANELA)))
        idx = int(round((x - t0) / JANELA))
        if lado == "fim":
            for i in range(max(0, idx), len(ser) - k + 1):
                if max(ser[i:i + k]) <= teto:
                    return round(t0 + i * JANELA + 0.15, 2)
        else:
            for i in range(min(idx, len(ser)), k - 1, -1):
                if max(ser[i - k:i]) <= teto:
                    return round(t0 + i * JANELA - 0.15, 2)
        return None

    # ---------- API
    def inicio(self, x, recuo_max=8.0):
        """início de trecho: nunca no meio de frase nem de fala encadeada. Volta até o começo da sequência de
        frases coladas (pausa < 0,4 s) — no máximo recuo_max — e confirma no áudio uma pausa antes."""
        x0 = x
        t = x
        def anterior(tt):      # frase que começa antes de tt e termina mais tarde (frases coladas se sobrepõem)
            prev = [(a, b) for a, b in self.frases if a < tt - 0.01]
            return max(prev, key=lambda fb: fb[1]) if prev else None
        for _ in range(60):
            f = next(((a, b) for a, b in self.frases if a - 0.02 <= t < b + 0.05), None)
            if f:
                t = f[0]
            p = anterior(t)
            if not p or t - p[1] >= 0.4 or x0 - p[0] > recuo_max:
                break
            t = p[0]                               # fala colada antes: inclui a frase anterior
        if t < x0 - 0.01 or self._frase_em(x0, folga=0.05):
            p = anterior(t)
            ant = p[1] if p else 0.0
            x = max(t - 0.35, (ant + t) / 2) if ant < t else t - 0.05
        q = self._quieto(x, "ini", recuo_max, pausa=0.4)
        if q is not None and x0 - q <= recuo_max and not self._frase_em(q):
            x = q            # (bug 2026-11-26: se q caísse dentro de outra frase longa, voltava 20 s; agora só aceita pausa)
        return round(max(0.0, x), 2)

    def fim(self, x, final=False):
        """fim de trecho, como um editor faria:
        1. anda pelas fronteiras de frase a partir de x e pega a 1ª PAUSA REAL (>= 0,7 s; 1,5 s no fim do
           episódio). Conversa encadeada fica inteira;
        2. se não houver pausa real dentro do limite (monólogo corrido), usa a pausa MAIS NATURAL encontrada,
           sem avançar demais sobre outro assunto;
        3. confirma no áudio (voz de personagem fora da transcrição): se houver voz logo depois, procura a pausa
           real à frente — até 4 s numa borda comum, até 40 s no fim do episódio — e repete o passo 1 de lá.
        Se nada resolver, devolve a melhor fronteira e o problema() continua acusando (o validador bloqueia e
        alguém decide)."""
        pausa = 1.5 if final else 0.7
        lim = 40.0 if final else 8.0
        lim_audio = 40.0 if final else 4.0
        x0 = x

        def fronteira(t_ini):
            t = self._sair_da_fala(t_ini)
            cand = []
            while t - x0 <= lim:
                prox = self._prox_inicio(t)
                cand.append((t, prox - t))
                if prox - t >= pausa:
                    break
                t = self._sair_da_fala(prox)
            if not cand:
                return t, self._prox_inicio(t) - t
            boas = [c for c in cand if c[1] >= pausa]
            return boas[0] if boas else max(cand, key=lambda c: c[1])

        b, gap = fronteira(x0)
        for _ in range(3):
            if not self.audio or not self._voz_em(b + 0.05, b + 0.35):
                break
            q = self._quieto(b, "fim", lim_audio, pausa=pausa)
            if q is None or q - b > lim_audio + 0.2:
                break
            b2, gap2 = fronteira(q)
            if b2 <= b + 0.01:
                b, gap = q, self._prox_inicio(q) - q
                return round(min(b, self.dur - 0.05), 2)
            b, gap = b2, gap2
        fim = min(b + 0.35, b + max(0.05, gap / 2))
        return round(min(fim, self.dur - 0.05), 2)

    def _voz_em(self, t0, t1):
        """há voz bem acima do fundo do jogo em [t0, t1]?"""
        if not self.audio:
            return False
        a0, ser = energia_voz(self.audio, t0, max(0.1, t1 - t0))
        fundo = self._fundo(t0)
        return bool(ser) and fundo is not None and max(ser) > fundo + self.margem + 3

    def problema(self, x, lado):
        """texto do problema se a borda corta fala; None se está limpa."""
        f = self._frase_em(x, folga=0.05)
        if f:
            return f"dentro da frase {f[0]:.2f}–{f[1]:.2f}"
        if self.audio:
            t0, ser = energia_voz(self.audio, x - 1, 2)
            fundo = self._fundo(x)
            if len(ser) > 10 and fundo is not None:
                i = int(round((x - t0) / JANELA))
                perto = ser[max(0, i - 3):i + 3]
                if perto and max(perto) > fundo + self.margem + 3:
                    return f"voz no áudio na borda ({max(perto) - fundo:+.0f} dB acima do fundo) — diálogo do jogo?"
        return None

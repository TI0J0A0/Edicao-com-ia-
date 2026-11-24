"""Transcreve um vídeo/áudio em português com faster-whisper (Whisper local).

Uso:
  python transcrever.py <arquivo> <pasta_saida> [--modelo turbo] [--idioma pt] [--pausa 0.7]

Gera em <pasta_saida>:
  <nome>_transcricao.json  -> frases com início/fim, palavras com tempo e lista de pausas
  <nome>_transcricao.txt   -> texto legível: [00:00:01.20 -> 00:00:04.00] frase
  <nome>_transcricao.srt   -> legenda padrão
"""
import argparse
import json
import os
import sys
import time
import warnings

warnings.filterwarnings("ignore")
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")


def ts(seg: float, sep: str = ".") -> str:
    h = int(seg // 3600)
    m = int(seg % 3600 // 60)
    s = seg % 60
    return f"{h:02d}:{m:02d}:{s:06.3f}".replace(".", sep)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("arquivo")
    ap.add_argument("saida")
    ap.add_argument("--modelo", default="turbo", help="tiny, base, small, medium, large-v3, turbo")
    ap.add_argument("--idioma", default="pt")
    ap.add_argument("--pausa", type=float, default=0.7, help="silêncio mínimo (s) para registrar pausa")
    ap.add_argument("--threads", type=int, default=0, help="threads de CPU (0 = automático)")
    a = ap.parse_args()

    import numpy as np
    from faster_whisper import WhisperModel, decode_audio

    if not os.path.isfile(a.arquivo):
        sys.exit(f"Arquivo não encontrado: {a.arquivo}")
    os.makedirs(a.saida, exist_ok=True)
    nome = os.path.splitext(os.path.basename(a.arquivo))[0]

    print(f"Carregando modelo '{a.modelo}' (na primeira vez ele é baixado)...", flush=True)
    modelo = WhisperModel(a.modelo, device="auto", compute_type="int8", cpu_threads=a.threads)
    t0 = time.time()
    # 1 s de silêncio no fim evita um erro do faster-whisper quando a fala vai até o último instante
    audio = decode_audio(a.arquivo, sampling_rate=16000)
    duracao_real = len(audio) / 16000
    audio = np.concatenate([audio, np.zeros(16000, dtype=audio.dtype)])
    segs, info = modelo.transcribe(
        audio,
        language=a.idioma,
        word_timestamps=True,
        vad_filter=False,  # mantém silêncios reais visíveis para detectar pausas
        condition_on_previous_text=False,  # reduz alucinação/repetição artificial
    )

    frases, palavras = [], []
    for s in segs:
        if s.start >= duracao_real - 0.15:  # frase que começa no silêncio acrescentado é invenção do Whisper
            break
        ws = [{"inicio": round(w.start, 2), "fim": round(min(w.end, duracao_real), 2), "palavra": w.word.strip()}
              for w in (s.words or []) if w.start < duracao_real]
        palavras.extend(ws)
        frases.append({"id": len(frases) + 1, "inicio": round(s.start, 2), "fim": round(s.end, 2),
                       "texto": s.text.strip(), "palavras": ws})
        print(f"[{ts(s.start)} -> {ts(s.end)}] {s.text.strip()}", flush=True)

    pausas = []
    for p, q in zip(palavras, palavras[1:]):
        gap = q["inicio"] - p["fim"]
        if gap >= a.pausa:
            pausas.append({"inicio": p["fim"], "fim": q["inicio"], "duracao": round(gap, 2),
                           "depois_de": p["palavra"], "antes_de": q["palavra"]})

    dados = {
        "arquivo": os.path.abspath(a.arquivo),
        "idioma": info.language,
        "duracao": round(duracao_real, 2),
        "modelo": a.modelo,
        "frases": frases,
        "pausas": pausas,
    }
    base = os.path.join(a.saida, f"{nome}_transcricao")
    with open(base + ".json", "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)
    with open(base + ".txt", "w", encoding="utf-8") as f:
        for fr in frases:
            f.write(f"[{ts(fr['inicio'])} -> {ts(fr['fim'])}] {fr['texto']}\n")
    with open(base + ".srt", "w", encoding="utf-8") as f:
        for fr in frases:
            f.write(f"{fr['id']}\n{ts(fr['inicio'], ',')} --> {ts(fr['fim'], ',')}\n{fr['texto']}\n\n")

    print(f"\nPronto em {time.time() - t0:.0f}s: {len(frases)} frases, {len(pausas)} pausas >= {a.pausa}s")
    print(f"Arquivos: {base}.json | .txt | .srt")


if __name__ == "__main__":
    main()

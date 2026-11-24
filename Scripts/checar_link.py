"""Diz se um link (Twitch, YouTube, TikTok...) ou arquivo já foi processado, consultando Scripts/links_processados.json.

Uso: python Scripts/checar_link.py <link ou arquivo> [<outro> ...]
Sai com código 1 se algum já foi processado (para o fluxo parar e avisar o João).
"""
import json
import os
import re
import sys

REG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "links_processados.json")


def normalizar(s):
    s = s.strip()
    m = re.search(r"twitch\.tv/(?:\w+/)?videos?/(\d+)", s) or re.search(r"twitch\.tv/.*[?&]video=v?(\d+)", s)
    if m:
        return "twitch:" + m.group(1)
    m = re.search(r"(?:youtu\.be/|youtube\.com/(?:watch\?(?:.*&)?v=|shorts/|live/|embed/))([\w-]{11})", s)
    if m:
        return "youtube:" + m.group(1)
    m = re.search(r"tiktok\.com/.*/video/(\d+)", s)
    if m:
        return "tiktok:" + m.group(1)
    if re.match(r"^https?://", s):
        return "url:" + s.split("#")[0].rstrip("/").lower()
    return "arquivo:" + os.path.basename(s).lower()


reg = json.load(open(REG, encoding="utf-8"))
por_id = {e["id"].lower(): e for e in reg["processados"]}
repetido = False
for arg in sys.argv[1:]:
    chave = normalizar(arg).lower()
    e = por_id.get(chave)
    if e:
        repetido = True
        print(f"JÁ PROCESSADO: {arg}")
        print(f"  live de {e.get('data_vod', '?')}, editado em {e.get('processado_em', '?')} ({e.get('tipo', '')})")
        print(f"  entrega: {e.get('entrega', '?')}")
        if e.get("relatorio"):
            print(f"  relatório: {e['relatorio']}")
    else:
        print(f"NOVO: {arg} ({chave})")
sys.exit(1 if repetido else 0)

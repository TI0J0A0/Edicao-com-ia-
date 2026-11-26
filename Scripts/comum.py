"""Base compartilhada dos scripts (V4): caminhos, configuração central, perfis por jogo e utilitários de mídia.

Tudo que é regra/limiar numérico mora em Scripts/config/ (projeto.json e perfis.json) — os scripts leem
daqui em vez de repetir números. Rodar sempre da raiz do projeto.
"""
import json
import os
import subprocess

SCRIPTS = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(SCRIPTS)
CONFIG = os.path.join(SCRIPTS, "config")


def carregar_json(caminho, padrao=None):
    if not os.path.exists(caminho):
        return padrao
    with open(caminho, encoding="utf-8") as f:
        return json.load(f)


def salvar_json(caminho, dados):
    os.makedirs(os.path.dirname(os.path.abspath(caminho)), exist_ok=True)
    tmp = caminho + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=1)
    os.replace(tmp, caminho)          # gravação atômica: nunca deixa JSON pela metade (checkpoint seguro)


def projeto():
    return carregar_json(os.path.join(CONFIG, "projeto.json"), {})


def perfil(nomes):
    """Combina um ou mais perfis editoriais (ex.: ["mundo_aberto", "narrativo"]).
    Regra de combinação: para cada parâmetro vale o valor MAIS PROTETOR (preserva mais conteúdo):
    limites de tempo morto/menu/pausa -> o maior; booleanos de preservação -> OR."""
    P = carregar_json(os.path.join(CONFIG, "perfis.json"), {})
    if isinstance(nomes, str):
        nomes = [nomes]
    nomes = [n for n in (nomes or []) if n in P.get("perfis", {})] or [P.get("padrao", "mundo_aberto")]
    base, vistos = dict(P["base"]), set()
    for n in nomes:
        for k, v in P["perfis"][n].items():
            if k.startswith("_"):
                continue
            if k not in vistos:              # 1º perfil que define a chave substitui a base
                base[k] = v
                vistos.add(k)
            elif isinstance(v, bool):
                base[k] = base[k] or v
            elif isinstance(v, (int, float)) and k in P.get("menor_e_mais_protetor", []):
                base[k] = min(base[k], v)
            elif isinstance(v, (int, float)):
                base[k] = max(base[k], v)
            else:
                base[k] = v
    base["_perfis"] = nomes
    return base


def sh(cmd, check=False):
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="ignore")
    if check and r.returncode != 0:
        raise RuntimeError(f"falhou: {' '.join(map(str, cmd[:10]))}…\n{r.stderr[-1500:]}")
    return r


def sonda(video):
    """resolução, fps (racional exato), duração e se tem áudio."""
    pr = json.loads(sh(["ffprobe", "-v", "error", "-show_entries",
                        "stream=codec_type,width,height,r_frame_rate,avg_frame_rate:format=duration",
                        "-of", "json", video]).stdout or "{}")
    v = next((s for s in pr.get("streams", []) if s["codec_type"] == "video"), None)
    if not v:
        raise RuntimeError(f"sem vídeo: {video}")
    num, den = map(int, v["r_frame_rate"].split("/"))
    return {"w": v["width"], "h": v["height"], "fps_str": f"{num}/{den}", "fps": num / den,
            "dur": float(pr["format"]["duration"]),
            "audio": any(s["codec_type"] == "audio" for s in pr["streams"])}


def hms(s, dec=False):
    s = max(0.0, float(s))
    h, r = divmod(s, 3600)
    m, x = divmod(r, 60)
    return f"{int(h)}:{int(m):02d}:{x:05.2f}" if dec else f"{int(h)}:{int(m):02d}:{int(x):02d}"


def hwaccel_args():
    """decodificação na GPU se o benchmark provou ganho (projeto.json -> render.hwaccel_decode)."""
    hw = projeto().get("render", {}).get("hwaccel_decode")
    return ["-hwaccel", hw] if hw else []

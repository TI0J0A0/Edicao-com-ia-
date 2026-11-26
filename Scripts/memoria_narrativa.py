"""DIRETOR NARRATIVO (V4) — memória narrativa da live inteira, preenchida pela IA e CONFERIDA por script.

A IA lê o resumo multimodal (resumo_ia.txt) e a transcrição, e registra a história em narrativa.json:
história principal, objetivos/missões, personagens e uma lista de EVENTOS com dependências ("o evento E9 só
faz sentido se o espectador viu E3"). O validador do plano usa isso para não remover o contexto de algo que
ficou no vídeo, mesmo que horas depois.

Formato de narrativa.json:
{
 "historia": "1–3 frases", "objetivos": ["..."], "personagens": [{"nome": "Lucia", "papel": "..."}],
 "eventos": [
   {"id": "E1", "t_ini": 1234.0, "t_fim": 1290.0, "tipo": "missao|humor|confronto|revelacao|estrategia|
     climax|consequencia|contexto|setup|reacao", "importancia": 1|2|3, "descricao": "...",
    "evidencia": "trecho da fala que prova o evento (copiado da transcrição)", "depende_de": ["E0"]}
 ]
}
importancia 3 = obrigatório no vídeo; 2 = manter se couber/condensar; 1 = pode sair.
"evidencia" é obrigatória para importância >= 2: o script confere que ela existe na transcrição perto
do tempo informado (anti-invenção de eventos/timestamps). Eventos só visuais: "evidencia": "visual" e
"quadro": "<arquivo do painel>".

Uso:
  python Scripts/memoria_narrativa.py iniciar <transcricao.json> <analise.json> <narrativa.json>
  python Scripts/memoria_narrativa.py checar  <narrativa.json> <transcricao.json>
"""
import os
import re
import sys
import unicodedata

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import comum  # noqa: E402

TIPOS = {"missao", "humor", "confronto", "revelacao", "estrategia", "climax", "consequencia", "contexto", "setup",
         "reacao"}


def norm(t):
    t = unicodedata.normalize("NFKD", t.lower())
    return re.sub(r"[^a-z0-9 ]+", " ", "".join(c for c in t if not unicodedata.combining(c))).split()


def iniciar(tr_p, an_p, saida):
    if os.path.exists(saida):
        sys.exit(f"{saida} já existe — não sobrescrevo a memória narrativa (apague à mão se quiser recomeçar).")
    an = comum.carregar_json(an_p, {})
    blocos = []
    for j0 in range(0, len(an.get("janelas", [])), 60):          # blocos de 10 min
        js = an["janelas"][j0:j0 + 60]
        cont = {}
        for j in js:
            for t in j["tags"]:
                cont[t] = cont.get(t, 0) + 1
        blocos.append({"t_ini": js[0]["t"], "t_fim": js[-1]["t"] + 10, "etiquetas": cont,
                       "reacoes": [r for r in an["eventos"]["reacoes"] if js[0]["t"] <= r < js[-1]["t"] + 10],
                       "resumo": ""})
    comum.salvar_json(saida, {"_instrucoes": __doc__.split("Uso:")[0].strip(), "transcricao": tr_p,
                              "historia": "", "objetivos": [], "personagens": [], "blocos": blocos, "eventos": []})
    print(f"Memória narrativa criada: {saida} ({len(blocos)} blocos de 10 min para resumir)")


def checar(nar_p, tr_p):
    nar = comum.carregar_json(nar_p, {})
    tr = comum.carregar_json(tr_p, {})
    frases = [(f["inicio"], f["fim"], norm(f["texto"])) for f in tr.get("frases", [])]
    dur = tr.get("duracao", 1e9)
    erros, avisos = [], []
    ids = {}
    for e in nar.get("eventos", []):
        i = e.get("id")
        if not i or i in ids:
            erros.append(f"evento sem id ou id repetido: {e}")
            continue
        ids[i] = e
        if not (0 <= e.get("t_ini", -1) <= e.get("t_fim", -1) <= dur + 1):
            erros.append(f"{i}: tempos inválidos {e.get('t_ini')}–{e.get('t_fim')}")
        if e.get("tipo") not in TIPOS:
            avisos.append(f"{i}: tipo '{e.get('tipo')}' fora da lista {sorted(TIPOS)}")
        if e.get("importancia") not in (1, 2, 3):
            erros.append(f"{i}: importancia deve ser 1, 2 ou 3")
        ev = e.get("evidencia", "")
        if e.get("importancia", 1) >= 2 and not ev:
            erros.append(f"{i}: importância {e.get('importancia')} sem evidência")
        elif ev and ev != "visual":
            alvo = norm(ev)
            perto = [w for a, b, ws in frases if a <= e["t_fim"] + 60 and b >= e["t_ini"] - 60 for w in ws]
            achou = sum(1 for w in alvo if w in set(perto)) / max(1, len(alvo))
            if achou < 0.6:
                erros.append(f"{i}: evidência '{ev[:60]}' não aparece na transcrição perto de "
                             f"{comum.hms(e['t_ini'])} ({achou:.0%} das palavras) — evento/tempo pode estar errado")
        elif ev == "visual" and not e.get("quadro"):
            avisos.append(f"{i}: evento visual sem 'quadro' de referência")
    for i, e in ids.items():
        for d in e.get("depende_de", []):
            if d not in ids:
                erros.append(f"{i}: depende de {d}, que não existe")
            elif ids[d]["t_ini"] > e["t_ini"]:
                erros.append(f"{i}: depende de {d}, que acontece DEPOIS")
    if not nar.get("historia"):
        avisos.append("história principal vazia")
    vazios = sum(1 for b in nar.get("blocos", []) if not b.get("resumo"))
    if vazios:
        avisos.append(f"{vazios} bloco(s) de 10 min sem resumo")
    for m in erros:
        print("  ERRO ", m)
    for m in avisos:
        print("  AVISO", m)
    print(f"{len(ids)} eventos | {len(erros)} erro(s) | {len(avisos)} aviso(s)")
    return 1 if erros else 0


if __name__ == "__main__":
    if len(sys.argv) >= 5 and sys.argv[1] == "iniciar":
        iniciar(*sys.argv[2:5])
    elif len(sys.argv) >= 4 and sys.argv[1] == "checar":
        raise SystemExit(checar(sys.argv[2], sys.argv[3]))
    else:
        print(__doc__)

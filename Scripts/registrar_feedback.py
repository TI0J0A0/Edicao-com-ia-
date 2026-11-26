"""MEMÓRIA EDITORIAL (V4) — registra feedback e aprendizados para os mesmos erros não voltarem.

Arquivo: Scripts/memoria_editorial.json (pasta permanente). Cada entrada tem uma "etiqueta" curta
(ex.: "fala_cortada_fim"). Quando a mesma etiqueta aparece 2+ vezes, o script avisa que é RECORRENTE e deve
virar regra verificável + teste de regressão (em Scripts/testes/). Nada muda sozinho nas regras fundamentais:
a entrada fica como "proposta" até o João confirmar.

Uso:
  python Scripts/registrar_feedback.py add --tipo negativo --etiqueta fala_cortada_fim --jogo "GTA 6" \
      --texto "episódios terminaram no meio da fala" [--citacao "palavras do João"] [--regra validar_plano:bordas]
  python Scripts/registrar_feedback.py listar [--etiqueta X]
  python Scripts/registrar_feedback.py resumo        (o que ler antes de editar uma live nova)
tipos: erro, positivo, negativo, corte_rejeitado, transicao_aprovada, preferencia_jogo, config_tecnica,
       problema_render, solucao
"""
import argparse
import datetime
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import comum  # noqa: E402

ARQ = os.path.join(comum.SCRIPTS, "memoria_editorial.json")
TIPOS = ["erro", "positivo", "negativo", "corte_rejeitado", "transicao_aprovada", "preferencia_jogo",
         "config_tecnica", "problema_render", "solucao"]


def carregar():
    return comum.carregar_json(ARQ, {"_sobre": __doc__.split("Uso:")[0].strip(), "entradas": []})


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd")
    a1 = sub.add_parser("add")
    a1.add_argument("--tipo", required=True, choices=TIPOS)
    a1.add_argument("--etiqueta", required=True)
    a1.add_argument("--texto", required=True)
    a1.add_argument("--jogo", default="")
    a1.add_argument("--citacao", default="")
    a1.add_argument("--regra", default="", help="checagem que já cobre isso (script:função)")
    a1.add_argument("--teste", default="", help="teste de regressão que cobre isso")
    a2 = sub.add_parser("listar")
    a2.add_argument("--etiqueta")
    sub.add_parser("resumo")
    a = ap.parse_args()
    m = carregar()
    E = m["entradas"]
    if a.cmd == "add":
        n = len([e for e in E if e["etiqueta"] == a.etiqueta])
        e = {"id": f"F{len(E) + 1:03d}", "data": datetime.date.today().isoformat(), "tipo": a.tipo,
             "etiqueta": a.etiqueta, "jogo": a.jogo, "texto": a.texto, "citacao": a.citacao,
             "regra_verificavel": a.regra, "teste": a.teste,
             "status": "ativo" if a.regra else ("proposta" if n >= 1 else "registrado")}
        E.append(e)
        comum.salvar_json(ARQ, m)
        print(f"Registrado {e['id']} ({a.etiqueta}).")
        if n >= 1 and not a.regra:
            print(f"RECORRENTE ({n + 1}x): transformar em regra verificável + teste de regressão e confirmar com o João.")
    elif a.cmd == "listar":
        for e in E:
            if not a.etiqueta or e["etiqueta"] == a.etiqueta:
                print(f"{e['id']} {e['data']} [{e['tipo']}] {e['etiqueta']} ({e['jogo'] or '-'}) — {e['texto']}"
                      f"{' | regra: ' + e['regra_verificavel'] if e['regra_verificavel'] else ''}")
    elif a.cmd == "resumo":
        por = {}
        for e in E:
            por.setdefault(e["etiqueta"], []).append(e)
        print("# Memória editorial — ler antes de editar\n")
        for tipo in ("negativo", "erro", "corte_rejeitado", "problema_render", "preferencia_jogo", "positivo",
                     "transicao_aprovada", "config_tecnica", "solucao"):
            itens = [es[-1] for es in por.values() if es[-1]["tipo"] == tipo]
            if itens:
                print(f"## {tipo}")
                for e in itens:
                    rec = f" (x{len(por[e['etiqueta']])})" if len(por[e['etiqueta']]) > 1 else ""
                    print(f"- {e['etiqueta']}{rec}: {e['texto']}"
                          f"{' — coberto por ' + e['regra_verificavel'] if e['regra_verificavel'] else ' — SEM checagem automática'}")
                print()
    else:
        print(__doc__)


if __name__ == "__main__":
    main()

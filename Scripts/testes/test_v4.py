"""Testes de regressão do sistema de edição V4 — rodam sem nenhuma live: geram o próprio material.

Material sintético (criado uma vez em Trabalho/_testes_v4/, pode ser apagado):
- "live" de 60 s a 59,94 fps (60000/1001) com uma "facecam" que se mexe no canto e o "jogo" trocando de cena;
- falas REAIS geradas pela voz do Windows (System.Speech) em tempos conhecidos:
  S1 10 s + S2 encadeada (conversa), S3 30 s, S4 40 s = fala de personagem em INGLÊS que NÃO está na
  transcrição (simula diálogo do jogo), S5 50 s;
- transcrição sintética com S1, S2, S3, S5 (sem S4).

Rodar da raiz:  python -m unittest Scripts/testes/test_v4.py -v
Cada feedback recorrente do João deve ganhar um teste aqui (ver Scripts/memoria_editorial.json).
"""
import json
import os
import shutil
import subprocess
import sys
import unittest

AQUI = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.dirname(AQUI)
RAIZ = os.path.dirname(SCRIPTS)
sys.path.insert(0, SCRIPTS)
os.chdir(RAIZ)
import comum  # noqa: E402
from bordas import Bordas, energia_voz  # noqa: E402

TMP = os.path.join(RAIZ, "Trabalho", "_testes_v4")
SRC = os.path.join(TMP, "live_sintetica.mp4")
TR = os.path.join(TMP, "transcricao.json")
FALAS = [("S1", 10.0, "Mano, olha esse carro ali na frente, vamos pegar ele agora.", True),
         ("S2", None, "Depois a gente passa no mecânico pra arrumar tudo.", True),
         ("S3", 30.0, "Essa missão é muito difícil, eu não acredito nisso.", True),
         ("S4", 40.0, "Lucia, you need to listen to me right now, this is serious.", False),
         ("S5", 50.0, "Agora sim, terminamos a missão.", True)]
PY = sys.executable


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="ignore",
                          env={**os.environ, "PYTHONIOENCODING": "utf-8"}, **kw)


def dur(arq):
    return float(run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", arq]).stdout)


def tts(texto, saida):
    ps = ("Add-Type -AssemblyName System.Speech; $s=New-Object System.Speech.Synthesis.SpeechSynthesizer; "
          f"$s.Rate=1; $s.SetOutputToWaveFile('{saida}'); $s.Speak(\"{texto}\"); $s.Dispose()")
    run(["powershell", "-NoProfile", "-Command", ps])


def fala_real(wav):
    """início/fim da voz dentro do wav (o TTS deixa silêncio nas pontas)."""
    r = run(["ffmpeg", "-hide_banner", "-i", wav, "-af", "silencedetect=n=-40dB:d=0.25", "-f", "null", "-"])
    import re
    ss = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", r.stderr)]
    se = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", r.stderr)]
    d = dur(wav)
    ini = se[0] if ss and ss[0] < 0.05 and se else 0.0
    fim = ss[-1] if ss and ss[-1] > d - 1.0 and ss[-1] > ini else d
    return ini, fim


def preparar():
    if os.path.exists(TR) and os.path.exists(SRC):
        return json.load(open(os.path.join(TMP, "falas.json"), encoding="utf-8"))
    shutil.rmtree(TMP, ignore_errors=True)
    os.makedirs(TMP)
    tempos, inputs, filt = {}, [], []
    t_prox = None
    for k, (nome, t0, texto, _) in enumerate(FALAS):
        wav = os.path.join(TMP, f"{nome}.wav")
        tts(texto, wav)
        a, b = fala_real(wav)
        t = t0 if t0 is not None else t_prox
        ini = t                                   # a voz começa em t (corta o silêncio inicial do wav)
        tempos[nome] = (round(ini, 2), round(ini + (b - a), 2))
        t_prox = ini + (b - a) + 0.3              # S2 encadeada: 0,3 s depois de S1
        inputs += ["-ss", f"{a:.3f}", "-t", f"{b - a:.3f}", "-i", wav]
        filt.append(f"[{k + 1}:a]aresample=48000,volume=2.0,adelay={int(ini * 1000)}:all=1[f{k}]")
    n = len(FALAS)
    fc = (";".join(filt) + f";[0:a]volume=1[bg];[bg]" + "".join(f"[f{k}]" for k in range(n))
          + f"amix=inputs={n + 1}:normalize=0:duration=first[a]")
    jogo = ("color=c=black:s=1280x720:r=60000/1001:d=60,geq=lum='mod(floor(T/1.5)*97+(X+Y)*(1+mod(floor(T/1.5),5)),256)'"
            ":cb=128:cr='128+40*sin(floor(T/1.5))'[g];testsrc2=s=320x180:r=60000/1001:d=60[cam];"
            "[g][cam]overlay=40:40,format=yuv420p[v]")
    r = run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi", "-i",
             "anoisesrc=color=pink:amplitude=0.015:d=60:r=48000", *inputs, "-f", "lavfi", "-i", "nullsrc",
             "-filter_complex", jogo + ";" + fc, "-map", "[v]", "-map", "[a]", "-c:v", "h264_amf", "-qp_i", "20",
             "-qp_p", "22", "-rc", "cqp", "-c:a", "aac", "-b:a", "192k", "-t", "60", SRC])
    assert r.returncode == 0, r.stderr[-800:]
    frases = [{"id": i + 1, "inicio": tempos[n_][0], "fim": tempos[n_][1], "texto": tx, "palavras": []}
              for i, (n_, _, tx, na_tr) in enumerate(FALAS) if na_tr]
    json.dump({"duracao": 60.0, "frases": frases, "pausas": []}, open(TR, "w", encoding="utf-8"), ensure_ascii=False)
    json.dump(tempos, open(os.path.join(TMP, "falas.json"), "w", encoding="utf-8"))
    return tempos


def plano_base(trechos, nome="plano_teste", **extra):
    p = {"video": SRC, "jogo": "Teste", "status": "aprovado", "transcricao": TR, "audio": SRC, "perfil": ["narrativo"],
         "facecam": [40, 40, 320, 180],
         "episodios": [{"parte": 1, "titulo": "TESTE | Parte 1", "arquivo": os.path.join(TMP, f"{nome}.mp4"),
                        "montagem": [{"capitulo": "Teste", "origem_inicio": a, "origem_fim": b, "decisao": "MANTER",
                                      "motivo": "teste", "transicao": t, **kw} for a, b, t, kw in trechos]}], **extra}
    arq = os.path.join(TMP, f"{nome}.json")
    comum.salvar_json(arq, p)
    return arq


class TesteV4(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.t = preparar()
        cls.B = Bordas(TR, SRC)

    # ---------------- proteção de diálogo
    def test_bordas_fim_no_meio_da_frase_vai_para_depois_da_conversa(self):
        s1, s2 = self.t["S1"], self.t["S2"]
        meio = (s1[0] + s1[1]) / 2
        self.assertIsNotNone(self.B.problema(meio, "fim"))
        fim = self.B.fim(meio)
        self.assertGreaterEqual(fim, s2[1], "conversa encadeada (S1+S2) tem que ficar inteira")
        self.assertIsNone(self.B.problema(fim, "fim"))

    def test_bordas_dialogo_do_jogo_fora_da_transcricao(self):
        s4 = self.t["S4"]
        meio = (s4[0] + s4[1]) / 2
        self.assertIsNotNone(self.B.problema(meio, "fim"), "fala em inglês sem transcrição precisa ser detectada pelo áudio")
        self.assertGreaterEqual(self.B.fim(meio), s4[1] - 0.15)

    def test_bordas_ponto_limpo_nao_mexe(self):
        self.assertIsNone(self.B.problema(25.0, "fim"))
        self.assertAlmostEqual(self.B.fim(25.0), 25.35, delta=0.4)

    def test_bordas_fim_de_episodio_pede_pausa_longa(self):
        s5 = self.t["S5"]
        f = self.B.fim((s5[0] + s5[1]) / 2, final=True)
        self.assertGreaterEqual(f, s5[1])

    # ---------------- validador
    def test_validar_bloqueia_revisar_e_borda_ruim(self):
        import validar_plano
        s3 = self.t["S3"]
        arq = plano_base([(0.0, (s3[0] + s3[1]) / 2, "corte", {}), (52.0, 58.0, "corte", {"decisao": "REVISAR"})],
                         "plano_ruim")
        erros, _ = validar_plano.validar(comum.carregar_json(arq), TR, SRC)
        txt = " ".join(erros)
        self.assertIn("REVISAR", txt)
        self.assertTrue(any("frase" in e or "voz" in e for e in erros), erros)

    def test_validar_contexto_ausente_pela_narrativa(self):
        import validar_plano
        nar = os.path.join(TMP, "narrativa.json")
        comum.salvar_json(nar, {"eventos": [
            {"id": "E1", "t_ini": 10.0, "t_fim": 14.0, "tipo": "setup", "importancia": 2, "descricao": "acha o carro",
             "evidencia": "olha esse carro"},
            {"id": "E2", "t_ini": 50.0, "t_fim": 53.0, "tipo": "consequencia", "importancia": 2,
             "descricao": "termina a missão", "evidencia": "terminamos a missão", "depende_de": ["E1"]}]})
        arq = plano_base([(20.0, 26.0, "corte", {}), (48.0, 56.0, "corte", {})], "plano_ctx")
        erros, _ = validar_plano.validar(comum.carregar_json(arq), TR, SRC, None, nar)
        self.assertTrue(any("contexto ausente" in e for e in erros), erros)

    def test_memoria_narrativa_recusa_evidencia_inventada(self):
        nar = os.path.join(TMP, "narrativa_falsa.json")
        comum.salvar_json(nar, {"historia": "x", "eventos": [
            {"id": "E1", "t_ini": 10.0, "t_fim": 14.0, "tipo": "humor", "importancia": 3,
             "descricao": "x", "evidencia": "o dragão voou sobre o castelo"}]})
        r = run([PY, os.path.join(SCRIPTS, "memoria_narrativa.py"), "checar", nar, TR])
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("não aparece na transcrição", r.stdout)

    def test_perfis_combinam_pelo_mais_protetor(self):
        self.assertEqual(comum.perfil("competitivo")["tempo_morto_max_s"], 12)
        self.assertEqual(comum.perfil(["competitivo", "terror"])["tempo_morto_max_s"], 45)
        self.assertTrue(comum.perfil(["mundo_aberto", "terror"])["evitar_efeitos"])

    # ---------------- transições
    def test_transicoes_escolhe_L_cut_quando_a_fala_continua(self):
        import transicoes
        s3 = self.t["S3"]
        corte = s3[1] - 0.5                      # A termina 0,5 s antes do fim da fala; B começa em silêncio
        p = comum.carregar_json(plano_base([(20.0, corte, "corte", {}), (44.5, 49.0, "corte", {})], "plano_jl"))
        transicoes.escolher(p)
        self.assertGreater(p["episodios"][0]["montagem"][1]["audio_desloc"], 0, p["episodios"][0]["montagem"][1])

    # ---------------- render + QC (ponta a ponta)
    def _render(self, arq, extra=()):
        r = run([PY, os.path.join(SCRIPTS, "validar_plano.py"), arq])
        r2 = run([PY, os.path.join(SCRIPTS, "montar_episodios.py"), "--plano", arq, "--pasta", os.path.join(TMP, "ep"), *extra])
        self.assertEqual(r2.returncode, 0, r.stdout + r2.stdout + r2.stderr)
        return comum.carregar_json(arq)["episodios"][0]["arquivo"]

    def test_render_fps_exato_e_sincronia(self):
        arq = plano_base([(20.5, 28.0, "corte", {}), (44.6, 48.0, "corte", {})], "plano_fps")
        out = self._render(arq)
        info = comum.sonda(out)
        self.assertEqual(info["fps_str"], "60000/1001", "o render tem que manter 59,94 exato (sem quadro duplicado)")
        r = run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,duration", "-of", "csv=p=0", out])
        d = {l.split(",")[0]: float(l.split(",")[1]) for l in r.stdout.split() if "," in l}
        self.assertLess(abs(d["video"] - d["audio"]), 0.05)
        self.assertAlmostEqual(d["video"], (28.0 - 20.5) + (48.0 - 44.6) - 0.2, delta=0.1)
        qc = run([PY, os.path.join(SCRIPTS, "verificar_episodio.py"), out,
                  os.path.join(TMP, "ep", "parte_01", "juncoes.json"), "--rapido"])
        self.assertNotIn("TRAVAMENTO", qc.stdout, "jogo parado 1,5 s com facecam mexendo NÃO é travamento: " + qc.stdout)
        self.assertNotIn("não rodou", qc.stdout, qc.stdout)

    def test_render_bloqueia_plano_sem_validacao(self):
        arq = plano_base([(20.5, 28.0, "corte", {})], "plano_sem_val")
        r = run([PY, os.path.join(SCRIPTS, "montar_episodios.py"), "--plano", arq, "--pasta", os.path.join(TMP, "ep2")])
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("não validado", r.stdout + r.stderr)

    def test_L_cut_mantem_a_fala_inteira_no_render(self):
        s3 = self.t["S3"]
        corte = round(s3[1] - 0.5, 2)
        arq = plano_base([(20.5, corte, "corte", {}), (44.6, 49.5, "corte", {"audio_desloc": 0.7})], "plano_lcut")
        p = comum.carregar_json(arq)
        p["transcricao"] = None                  # aqui o teste é do motor de áudio, não das bordas
        comum.salvar_json(arq, p)
        out = self._render(arq, ["--sem-validacao"])
        jun = comum.carregar_json(os.path.join(TMP, "ep", "parte_01", "juncoes.json"))["juncoes"][0]["t"]
        t0, ser = energia_voz(out, jun - 4, 6)
        fundo = sorted(ser)[len(ser) // 5]
        i = int(round((jun + 0.3 - t0) / 0.05))
        self.assertGreater(max(ser[i:i + 4]), fundo + 10, "com L-cut a voz de A continua depois do corte de imagem")

    def test_previa_de_emendas(self):
        arq = plano_base([(20.5, 28.0, "corte", {}), (44.6, 49.5, "corte", {})], "plano_previa")
        r = run([PY, os.path.join(SCRIPTS, "montar_episodios.py"), "--plano", arq, "--pasta", os.path.join(TMP, "ep3"),
                 "--previa-emendas"])
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        prev = os.path.join(TMP, "ep3", "parte_01", "previas")
        arqs = [f for f in os.listdir(prev) if f.endswith(".mp4")]
        self.assertEqual(len(arqs), 1)
        info = comum.sonda(os.path.join(prev, arqs[0]))
        self.assertEqual((info["w"], info["h"]), (640, 360))
        self.assertAlmostEqual(info["dur"], 5.8, delta=0.3)

    def test_qc_detecta_congelado_e_fala_cortada_no_fim(self):
        s3 = self.t["S3"]
        out = os.path.join(TMP, "congelado.mp4")
        fim = (s3[0] + s3[1]) / 2
        fc = (f"[0:v]trim=20:26,setpts=PTS-STARTPTS,tpad=stop_mode=clone:stop_duration=1.2[a];"
              f"[0:v]trim=27.2:{fim:.2f},setpts=PTS-STARTPTS[b];[a][b]concat=n=2:v=1:a=0[v];"
              f"[0:a]atrim=20:{fim:.2f},asetpts=PTS-STARTPTS[au]")
        r = run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", SRC, "-filter_complex", fc, "-map", "[v]",
                 "-map", "[au]", "-c:v", "h264_amf", "-c:a", "aac", out])
        self.assertEqual(r.returncode, 0, r.stderr)
        j = os.path.join(TMP, "jun_vazio.json")
        comum.salvar_json(j, {"parte": 1, "duracao_encerramento": 0, "juncoes": []})
        qc = run([PY, os.path.join(SCRIPTS, "verificar_episodio.py"), out, j, "--rapido"])
        self.assertIn("TRAVAMENTO", qc.stdout, qc.stdout)
        self.assertIn("FALA CORTADA no FIM", qc.stdout, qc.stdout)

    def test_qc_pessoa_parada_em_webcam_30fps_nao_e_travamento(self):
        """bug achado em 2026-11-26 num vídeo real: webcam de 30 fps dentro de 60 fps repete quadros e pessoa
        parada quase não muda os pixels — com jogo parado isso virava 'travamento' falso."""
        out = os.path.join(TMP, "webcam30.mp4")
        fc = ("color=c=0x404040:s=1280x720:r=60000/1001:d=6[g];"
              "testsrc2=s=320x180:r=30000/1001:d=6,fps=60000/1001[cam];"
              "[g][cam]overlay=40:40,format=yuv420p[v]")
        r = run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo",
                 "-filter_complex", fc, "-map", "[v]", "-map", "0:a", "-t", "6", "-c:v", "h264_amf", "-rc", "cqp",
                 "-qp_i", "16", "-qp_p", "16", "-c:a", "aac", out])
        self.assertEqual(r.returncode, 0, r.stderr)
        j = os.path.join(TMP, "jun_cam.json")
        comum.salvar_json(j, {"parte": 1, "duracao_encerramento": 0, "juncoes": [], "facecam": [40, 40, 320, 180]})
        qc = run([PY, os.path.join(SCRIPTS, "verificar_episodio.py"), out, j, "--rapido"])
        self.assertNotIn("TRAVAMENTO", qc.stdout, qc.stdout)
        self.assertNotIn("não rodou", qc.stdout, qc.stdout)

    def test_analise_pega_travamento_da_live_de_1s(self):
        congelado = os.path.join(TMP, "congelado.mp4")
        if not os.path.exists(congelado):
            self.test_qc_detecta_congelado_e_fala_cortada_no_fim()
        cache = os.path.join(TMP, "analise_cong")
        shutil.rmtree(cache, ignore_errors=True)
        r = run([PY, os.path.join(SCRIPTS, "analisar_live.py"), congelado, cache, "--facecam", "40,40,320,180"])
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        trav = comum.carregar_json(os.path.join(cache, "analise.json"))["eventos"]["travamentos"]
        self.assertTrue(any(a <= 6.6 and b >= 6.4 for a, b in trav), trav)   # congelado de 6,0 a 7,2 s

    # ---------------- análise
    def test_analise_acha_facecam_e_cortes(self):
        cache = os.path.join(TMP, "analise")
        r = run([PY, os.path.join(SCRIPTS, "analisar_live.py"), SRC, cache, "--facecam", "auto", "--transcricao", TR])
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        an = comum.carregar_json(os.path.join(cache, "analise.json"))
        import analisar_live
        self.assertIn("facecam", an, an.get("facecam_detectada"))
        self.assertGreater(analisar_live.iou(an["facecam"], [40, 40, 320, 180]), 0.5, an["facecam"])
        self.assertGreater(len(an["eventos"]["cortes_cena"]), 15)
        self.assertTrue(os.path.exists(os.path.join(cache, "resumo_ia.txt")))

    # ---------------- revisor
    def test_revisor_pega_fim_cortando_fala_e_fica_pendente_sem_qc(self):
        import revisor_editorial
        s5 = self.t["S5"]
        arq = plano_base([(20.5, 28.0, "corte", {}), (44.6, (s5[0] + s5[1]) / 2, "corte", {})], "plano_rev")
        r = revisor_editorial.Revisor(arq, os.path.join(TMP, "ep_inexistente"))
        r.tecnico()
        r.editorial()
        veredito, txt = r.relatorio()
        self.assertEqual(veredito, "REPROVADO", txt)
        self.assertIn("FIM DO EPISÓDIO", txt)
        self.assertTrue(r.pendencias)


if __name__ == "__main__":
    unittest.main(verbosity=2)

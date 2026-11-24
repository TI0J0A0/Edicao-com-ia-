---
name: plano-de-edicao
description: Lê a transcrição em trabalho/ e o guia estilo/ESTILO.md, entende o assunto do vídeo e monta um plano de edição — cortes (pausas longas, repetições, retomadas/erros) e onde entram letreiros, gráficos, listas e zooms, cada um com início, fim e descrição — salvo em trabalho/plano.json e mostrado ao usuário para aprovação antes de qualquer criação. Use sempre que o usuário pedir plano de edição, roteiro de cortes, "o que cortar", "onde colocar letreiro/zoom/gráfico", ou quiser começar a editar um vídeo já transcrito.
---

# Plano de edição

O objetivo é transformar a transcrição em um roteiro de edição concreto que o usuário (um criador de YouTube) aprova antes de qualquer coisa ser produzida. O plano é uma proposta: o usuário decide. Por isso esta skill **só planeja** — não renderiza, não corta vídeo, não cria animações nem arquivos além do plano. Criar algo antes da aprovação desperdiça tempo do usuário e pode gerar trabalho no estilo errado.

## 1. Reunir o material

- Transcrição: o `*_transcricao.json` mais recente em `trabalho/` (se houver vários, pergunte qual). Se não houver nenhum, rode antes a skill `transcricao`.
- Estilo: `estilo/ESTILO.md`. Leia inteiro — ele manda no ritmo dos cortes, frequência de zooms, tom dos letreiros, cores e o que evitar. Se não existir ou estiver vazio, avise e use padrões moderados (os valores abaixo), deixando claro no plano que foram suposições.

## 2. Entender o vídeo

Leia a transcrição toda antes de decidir qualquer coisa. Identifique: assunto, público, estrutura (gancho, partes, conclusão), os momentos-chave (números, nomes, listas faladas, comparações, frases de impacto). Os elementos visuais devem servir ao conteúdo — um letreiro reforça uma ideia importante, um gráfico mostra um número que foi falado, uma lista aparece quando o apresentador enumera itens.

## 3. Sugerir cortes

Use `pausas` e as `palavras` com tempo do JSON:

- **pausa** — silêncio longo (padrão: > 0,8 s, ou o que o ESTILO.md disser). Corte o miolo, deixando ~0,15 s de respiro de cada lado para não ficar robótico.
- **repeticao** — a mesma ideia/frase dita duas vezes seguidas. Mantenha a melhor versão (normalmente a última, mais fluida) e corte a outra.
- **retomada** — erro e recomeço ("ou melhor", "deixa eu falar de novo", frase interrompida e reiniciada, gaguejo). Corte do início da tentativa errada até o início da tentativa boa.
- Vícios ("é...", "né", "tipo") só se o ESTILO.md pedir ou se estiverem em excesso.

Os tempos de corte precisam cair entre palavras (use o `fim` de uma palavra e o `inicio` da próxima), nunca no meio de uma palavra. Na dúvida, prefira não cortar e marque `"confianca": "baixa"`.

## 4. Sugerir elementos visuais

Tipos: `letreiro` (texto na tela: título, destaque, nome), `grafico` (números, comparações, evolução), `lista` (itens enumerados), `zoom` (ênfase em frase de impacto ou para quebrar monotonia). Cada um com início/fim alinhados à fala que ele acompanha, descrição clara do que aparece e o conteúdo exato (texto, itens, dados). Não sobreponha dois elementos no mesmo trecho, a menos que seja zoom + letreiro. Sem ESTILO.md, mire em algo como um elemento a cada 20–40 s.

Os tempos dos elementos são do **vídeo original** (antes dos cortes); não coloque elementos dentro de trechos que serão cortados.

## 5. Salvar `trabalho/plano.json`

```json
{
  "video": "bruto/nome.mp4",
  "transcricao": "trabalho/nome_transcricao.json",
  "status": "aguardando_aprovacao",
  "assunto": "Resumo em 1–2 frases",
  "estrutura": [{"inicio": 0.0, "fim": 25.4, "parte": "Gancho"}],
  "cortes": [
    {"id": "C1", "tipo": "pausa", "inicio": 12.34, "fim": 14.10, "descricao": "Pausa de 1,8 s antes de 'então'", "confianca": "alta"}
  ],
  "elementos": [
    {"id": "E1", "tipo": "letreiro", "inicio": 3.20, "fim": 6.00, "descricao": "Título do vídeo no gancho", "conteudo": "3 erros que todo iniciante comete"}
  ],
  "duracao_original": 600.0,
  "duracao_estimada_apos_cortes": 540.0,
  "observacoes": ["Suposições feitas, dúvidas para o usuário"]
}
```

Tempos em segundos com 2 casas. Se já existir um `plano.json`, renomeie o antigo para `plano_anterior.json` antes de salvar.

## 6. Mostrar para aprovação (sempre)

Apresente o plano no chat em português simples, com tempos no formato `mm:ss`:

1. Assunto e duração: original → estimada após cortes.
2. Tabela de **cortes**: id, início, fim, tipo, o que é cortado (trecho do texto).
3. Tabela de **elementos**: id, início, fim, tipo, descrição/conteúdo.
4. Dúvidas e suposições.

Termine perguntando se aprova, ou o que mudar (ex.: "tira o C3", "troca o E2 por uma lista"). Ajuste o `plano.json` a cada pedido e mostre de novo o que mudou. Só quando o usuário aprovar explicitamente, mude `status` para `"aprovado"` — e só então qualquer outra etapa (HyperFrames, cortes no FFmpeg etc.) pode começar.

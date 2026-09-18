# TS SE Tool Python Harness
Harness econômico para Codex CLI + RTK redesenvolver o TS SE Tool em Python para ATS/ETS2 1.61+.

## Preparação
1. Coloque/extrai o source C# 0.3.11.0 em `reference/legacy/` (este pacote já inclui o ZIP de referência quando disponível).
2. Coloque cópias de perfis/saves em `samples/ats/` e/ou `samples/ets2/`.
3. No Windows: `rtk init -g --codex` (se ainda não configurado).
4. Abra a raiz no terminal e peça ao Codex para executar `PROJECT.md`.

## Fluxo
Análise legado → fundação → descoberta de perfis → decoder → parser → clonagem → editores → GUI → testes 1.61 → build EXE.

Não use saves reais sem backup. As fixtures devem ser cópias descartáveis.

## Continuidade quando créditos/tokens estiverem acabando
O projeto possui um protocolo obrigatório de encerramento seguro. Se Codex, Claude Code ou GitHub Copilot indicar que créditos, tokens, contexto ou sessão estão próximos do limite, o agente não deve iniciar uma nova task. Ele deve testar o estado atual, salvar o trabalho e gerar `tasks/reports/CONTINUATION_REPORT.md` com data/hora real, progresso verificável, pendências e a próxima ação exata.

Na sessão seguinte, esse relatório deve ser lido antes de qualquer nova task. O modelo está em `tasks/reports/CONTINUATION_REPORT.template.md`. Se a plataforma não informar saldo/percentual de créditos, o agente deve registrar `não informado`, nunca estimar ou inventar o valor.

## Estimativa de consumo e custo por IA

> **Estimativa, não orçamento garantido.** Este projeto é grande: envolve análise do legado C# 0.3.11.0, reimplementação em Python, parser/writer de saves, clonagem de perfis, GUI, testes ATS/ETS2 1.61+ e empacotamento em um único EXE. O consumo real depende de retrabalho, cache, modelo escolhido e quantidade de saída gerada.

Para planejamento, o Harness considera **1,8 a 3,2 milhões de tokens totais de trabalho**, com alvo central de aproximadamente **2,5 milhões** usando RTK e as tasks incrementais. Para converter valores abaixo foi usada uma referência de planejamento de **US$ 1 = R$ 5,13**; atualize o câmbio antes de executar se quiser uma projeção mais precisa.

| IA / forma de uso | Referência de preço | Estimativa para este projeto | Estimativa em R$ | Observação |
|---|---:|---:|---:|---|
| GitHub Copilot Pro | US$ 10/mês + US$ 15/mês de créditos incluídos | pode exigir mais de um ciclo/créditos extras | **a partir de ~R$ 51/mês** | O custo final depende do modelo e dos AI credits consumidos. |
| GitHub Copilot Pro+ | US$ 39/mês, com uso incluído maior | melhor margem para agentes/modelos premium | **a partir de ~R$ 200/mês** | Pode haver cobrança adicional se os créditos incluídos acabarem. |
| Claude Code / Claude Sonnet 5 | US$ 2/M entrada + US$ 10/M saída | ~US$ 7,9 a US$ 14,1* | **~R$ 41 a R$ 72*** | Estimativa tokenizada; assinatura/limites do Claude Code podem alterar o valor efetivo. |
| Codex / GPT-5.3-Codex | US$ 1,75/M entrada + US$ 14/M saída | ~US$ 9,8 a US$ 17,4* | **~R$ 50 a R$ 89*** | Estimativa tokenizada; créditos/uso incluído no plano podem reduzir o desembolso adicional. |

\* Para tornar a comparação reproduzível, a faixa tokenizada assume aproximadamente **80% de tokens de entrada e 20% de saída**, sem descontar cache. O RTK e cache efetivo podem reduzir o custo; retrabalho e saídas maiores podem aumentá-lo.

### Como atualizar a estimativa

Use estas fórmulas para Claude/Codex quando os preços ou o câmbio mudarem:

```text
custo_USD = (entrada_em_milhoes × preço_entrada) + (saida_em_milhoes × preço_saida)
custo_BRL = custo_USD × cotacao_USD_BRL
```

No GitHub Copilot, acompanhe os **AI credits** da conta, porque a cobrança atual depende do modelo e dos tokens consumidos. Não trate o valor mensal do plano como garantia de que todo o projeto caberá no uso incluído.

## Como iniciar o projeto em cada IA

Antes de começar, abra o terminal na raiz deste repositório. Não peça para a IA “fazer tudo de uma vez”: o Harness foi desenhado para executar `tasks/` em ordem e registrar continuidade quando a sessão ou os créditos estiverem próximos do limite.

### Codex CLI + RTK — recomendado para este Harness

Se ainda não configurou o RTK:

```powershell
rtk init -g --codex
```

Depois inicie o Codex na raiz do projeto e envie:

```text
Leia primeiro AGENTS.md e depois PROJECT.md.

Execute o projeto seguindo rigorosamente as tasks em tasks/, na ordem definida pelo PROJECT.md.
Use RTK sempre que possível para reduzir o consumo de tokens.
Não implemente o projeto inteiro de uma vez e não pule quality gates.
Use projeto_atual somente como referência/fixture e nunca altere os arquivos originais.
O objetivo final é redesenvolver o TS SE Tool em Python para ATS/ETS2 1.61+, preservando as funcionalidades relevantes do legado e gerando um único executável Windows em dist/TS-SE-Tool.exe.
Antes de escrever qualquer save/perfil, implemente backup e gravação segura.
Execute Ruff, mypy e pytest conforme definido nas tasks.
Se houver indicação de limite próximo de créditos, tokens, contexto ou sessão, não inicie uma nova task. Execute o protocolo de encerramento seguro do AGENTS.md e gere/atualize tasks/reports/CONTINUATION_REPORT.md com data/hora, estado atual, pendências, testes e próxima ação.
Se CONTINUATION_REPORT.md já existir, leia-o antes de qualquer task e retome exatamente do ponto registrado, sem repetir trabalho concluído.
Comece agora pela Task 00, salvo se o relatório de continuidade indicar outro ponto.
```

### Claude Code

Abra o Claude Code na raiz do repositório e envie:

```text
Leia AGENTS.md, PROJECT.md e verifique tasks/reports/CONTINUATION_REPORT.md antes de alterar qualquer arquivo.

Trabalhe somente na task atual definida pelo PROJECT.md ou pelo relatório de continuidade. Analise o legado C# e as fixtures em projeto_atual sem modificá-las. Reimplemente o comportamento em Python de forma incremental, com testes e preservação segura dos saves.
Não avance enquanto os quality gates da task atual não passarem.
O resultado final deve suportar ATS/ETS2 1.61+ e gerar um único dist/TS-SE-Tool.exe que não exija Python instalado.
Mantenha o contexto econômico: leia apenas os arquivos necessários para a task e reutilize os relatórios/documentação já produzidos.
Se a sessão, contexto, rate limit ou créditos estiverem próximos do limite, pare antes da próxima task e gere/atualize tasks/reports/CONTINUATION_REPORT.md com data/hora, trabalho concluído, trabalho pendente, arquivos alterados, testes, erros e próxima ação exata.
Comece pela Task 00 se não houver um relatório válido de continuidade.
```

### GitHub Copilot / Copilot Agent

Abra este repositório no VS Code com GitHub Copilot e use o modo Agent. Envie:

```text
Use AGENTS.md e PROJECT.md como instruções obrigatórias deste repositório.
Antes de começar, verifique se existe tasks/reports/CONTINUATION_REPORT.md e, se existir, retome desse ponto.
Execute somente uma task de tasks/ por vez. Não tente gerar todo o projeto em uma única execução.
Use projeto_atual apenas como referência para o TS SE Tool 0.3.11.0 e para os perfis ATS/ETS2; nunca modifique os originais.
Implemente a versão Python incrementalmente, execute os quality gates e só marque uma task como concluída quando os testes passarem.
O objetivo final é ATS/ETS2 1.61+ e um único executável Windows dist/TS-SE-Tool.exe sem dependência de Python instalado.
Se os AI credits, contexto ou sessão estiverem próximos do limite, não inicie outra task. Gere/atualize tasks/reports/CONTINUATION_REPORT.md seguindo AGENTS.md e encerre em um estado seguro para que Copilot, Codex ou Claude Code possam continuar depois.
Comece pela Task 00 se não houver continuidade pendente.
```

## Troca de IA durante o desenvolvimento

O projeto foi preparado para permitir **Codex → Claude Code → Copilot** (ou outra ordem). Antes de trocar de ferramenta, confirme que `tasks/reports/CONTINUATION_REPORT.md` está atualizado. A nova IA deve ler esse arquivo, `AGENTS.md` e `PROJECT.md` antes de modificar o código. Assim, o estado do projeto fica no repositório e não depende da memória da conversa anterior.

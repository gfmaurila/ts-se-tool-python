# AGENTS

Você é um agente de modernização/reengenharia. Prioridades: integridade do save > compatibilidade > testes > UX > velocidade.

## Economia de tokens / RTK
- Consulte arquivos específicos, não reabra repositório inteiro.
- Prefira buscas direcionadas (`rg`) e saídas resumidas.
- Rode subconjuntos de testes durante desenvolvimento; suíte completa apenas nos gates.
- Não repita contexto já registrado em `docs/LEGACY-MAPPING.md`.
- Diffs pequenos e commits/task pequenos.

## Arquitetura alvo
`src/tsse/core` não depende de GUI. `games/ats` e `games/ets2` contêm diferenças por jogo. `infrastructure` contém filesystem/decoder. `desktop` usa casos de uso da camada application.

## Segurança de dados
Nunca escreva diretamente no arquivo original. Backup obrigatório, temp file, validação de parse e só então replace. Testes nunca operam na pasta Documents real do usuário.

## Qualidade
Ruff + mypy + pytest. Cobertura mínima inicial 80% para core/parser/cloning; bugs de compatibilidade devem ganhar teste de regressão.

## Controle de créditos/tokens e encerramento seguro
O agente deve observar qualquer indicador disponível de limite de créditos, tokens, contexto, rate limit ou encerramento iminente da sessão. Nunca invente percentual ou saldo se a ferramenta não expuser esse dado.

Quando houver indicação confiável de que o limite está próximo:
1. NÃO iniciar uma nova task.
2. Finalizar com segurança a menor unidade de trabalho atual, quando possível.
3. Evitar refatorações ou alterações grandes adicionais.
4. Executar os testes relevantes possíveis no estado atual.
5. Não marcar a task como concluída se os quality gates não passaram.
6. Gerar/atualizar obrigatoriamente `tasks/reports/CONTINUATION_REPORT.md`.
7. Registrar a data e hora reais da última atualização em ISO 8601 com timezone local. No Windows/PowerShell, pode usar `Get-Date -Format "yyyy-MM-ddTHH:mm:ssK"`.
8. Registrar: última task concluída, task atual, estado, funcionalidades concluídas, pendências, arquivos modificados, testes e resultados, falhas conhecidas, decisões técnicas, riscos, próximos passos e comando/orientação exata de retomada.
9. Encerrar a sessão após salvar o relatório e o estado seguro do trabalho.

## Retomada obrigatória
Ao iniciar qualquer nova sessão:
1. Leia `AGENTS.md` e `PROJECT.md`.
2. Se existir `tasks/reports/CONTINUATION_REPORT.md`, leia-o ANTES de iniciar ou repetir qualquer task.
3. Valide rapidamente se o estado do repositório corresponde ao relatório.
4. Não repita trabalho já concluído e validado.
5. Continue do ponto registrado no relatório.
6. Após uma retomada bem-sucedida, mantenha o relatório atualizado até a conclusão global do projeto.

## Handoff entre IAs
`CONTINUATION_REPORT.md` é o contrato de continuidade entre Codex, Claude Code e GitHub Copilot. Não dependa da memória da sessão anterior. Toda informação necessária para outra IA continuar deve estar no repositório.

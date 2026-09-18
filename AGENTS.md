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

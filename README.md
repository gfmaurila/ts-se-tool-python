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

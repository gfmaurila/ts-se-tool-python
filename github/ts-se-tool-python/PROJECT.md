# PROJECT — TS SE Tool Python 1.61+

## Objetivo
Redesenvolver o TS SE Tool 0.3.11.0 em Python usando o source e o build legado em `../../projeto_atual/` como referência comportamental. Suportar ATS/ETS2 1.61+ e produzir um único executável Windows.

## Stack
Python 3.13+, PySide6, pytest, pytest-cov, Ruff, mypy e PyInstaller.

## Entradas obrigatórias
- `../../projeto_atual/ATS/`
- `../../projeto_atual/ETS/`
- `../../projeto_atual/TS.SE.Tool.0.3.11.0/`
- `../../projeto_atual/TS.SE.Tool.vs.0.3.11.0/`

## Resultado
`dist/TS-SE-Tool.exe` (one-file, windowed), sem instalação de Python e sem pastas auxiliares obrigatórias ao lado do exe.

## Regras
1. Execute `tasks/00` a `tasks/13` em ordem.
2. Não traduza C# linha por linha; mapeie comportamento e reimplemente.
3. Não altere arquivos em `projeto_atual`.
4. Preserve conteúdo SII desconhecido em round-trip sempre que possível.
5. Toda escrita real: backup + temp + validação + replace atômico.
6. Decoder deve ficar atrás de `SiiDecoder`; nunca espalhar chamadas nativas pelo domínio.
7. Se uma dependência nativa for necessária e sua licença permitir redistribuição, empacote-a no one-file e resolva o caminho em runtime. Caso contrário, documente o bloqueio e não invente compatibilidade.
8. Ao final de cada task: Ruff + mypy + testes relevantes.
9. Registre relatório curto em `tasks/reports/NN.md`.
10. Use RTK para reduzir tokens/logs.

## Definition of Done
- Detecta ATS/ETS2 e perfis.
- Abre cópias dos perfis reais de referência.
- Clona perfil com identidade independente.
- Implementa os editores priorizados nas tasks.
- GUI funcional.
- Unit + integration + regressão ATS/ETS 1.61+.
- `scripts/build-onefile.ps1` gera `dist/TS-SE-Tool.exe`.
- `scripts/smoke-onefile.ps1` valida inicialização do exe.

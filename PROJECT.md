# PROJECT — TS SE Tool Python 1.61+

## Objetivo
Redesenvolver em Python o TS SE Tool 0.3.11.0 usando o source legado em `reference/` apenas como referência comportamental. Alvo: American Truck Simulator e Euro Truck Simulator 2 1.61+, priorizando clonagem segura de perfil e leitura/escrita de saves.

## Stack obrigatória
Python 3.13+, PySide6, pytest/pytest-cov, Ruff, mypy, PyInstaller. Código tipado, modular e testável.

## Regras de execução (Codex + RTK)
1. Leia `AGENTS.md` uma vez. Execute as tasks em ordem; não carregue todas no contexto simultaneamente.
2. Antes de implementar uma task, leia somente os arquivos do legado citados/mapeados como necessários e os módulos Python diretamente envolvidos.
3. Use RTK para reduzir saída de comandos, testes e logs. Não despeje árvores, diffs ou logs completos se um resumo/grep for suficiente.
4. Não traduza C# linha a linha. Preserve comportamento útil e redesenhe interfaces Python.
5. Nunca altere um save/profile de amostra in-place: copie para diretório temporário.
6. Preserve campos/blocos SII desconhecidos sempre que possível. Escrita deve ser lossless para conteúdo não editado.
7. Toda escrita cria backup e usa gravação atômica (temporário + validação + replace).
8. Ao fim de cada task: Ruff, mypy e testes relevantes. Só avance com gate verde.
9. Registre decisões em `docs/` e resultados curtos em `tasks/reports/`.
10. Não invente suporte a formato criptografado. Se decoder externo for necessário, encapsule-o atrás de uma interface e documente licença/origem.
11. Antes de iniciar uma nova task, verifique se há indicação de limite próximo de créditos/tokens/contexto/sessão. Se houver, não inicie a task: execute o protocolo de encerramento seguro definido em `AGENTS.md`.
12. Quando interromper por limite, gere/atualize `tasks/reports/CONTINUATION_REPORT.md` com data/hora real, estado verificável e próximos passos.
13. Em toda nova sessão, se `CONTINUATION_REPORT.md` existir, ele deve ser lido antes de qualquer task e usado como ponto de retomada.
14. Nunca invente saldo, percentual ou quantidade de créditos restantes se a plataforma não fornecer essa informação.

## Definition of Done global
- Descobre perfis ATS/ETS2.
- Lê profile.sii/info.sii/game.sii suportados.
- Clona perfil com identidade independente sem alterar origem.
- Edita funcionalidades selecionadas do legado com round-trip seguro.
- Testes unitários + integração + fixtures 1.61.
- GUI desktop funcional.
- `scripts/build.ps1` produz pacote Windows via PyInstaller.

## Fluxo de execução e continuidade
```text
INÍCIO/RETOMADA
      ↓
AGENTS.md + PROJECT.md
      ↓
CONTINUATION_REPORT existe? ── SIM → validar estado → retomar ponto registrado
      │ NÃO
      ↓
TASK atual
      ↓
IMPLEMENTAÇÃO
      ↓
QUALITY GATES
      ↓
Limite de créditos/tokens/contexto próximo?
      ├── NÃO → próxima task
      └── SIM → testes possíveis → CONTINUATION_REPORT.md → STOP seguro
```

Sequência após a auditoria de paridade: `11a-decoder-parity` →
`11b-safe-save-io` → `11c-profile-identity-io` →
`11d-player-company-parity` → `11e-vehicle-trailer-parity` →
`11f-garage-market-parity` → `11g-convoy-settings-ui` → Tasks 11–13 de
compatibilidade/build. Nunca avance enquanto o decoder ou os gates da task
atual estiverem bloqueados.

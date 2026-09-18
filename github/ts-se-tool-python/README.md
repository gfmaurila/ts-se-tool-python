# TS SE Tool Python

Reimplementação em Python do TS SE Tool, orientada por comportamento do projeto C# 0.3.11.0 e por perfis reais de ATS/ETS2 presentes apenas no ambiente local de desenvolvimento.

## Objetivos
- ATS e ETS2 1.61+
- clonagem segura de perfil
- leitura/edição de saves
- GUI PySide6
- testes unitários e integração
- distribuição Windows em **um único arquivo `.exe`** via PyInstaller `--onefile`

## Referências locais
O material legado e os perfis reais NÃO ficam no repositório Git. O agente deve lê-los em `../../projeto_atual/` a partir deste repositório:
- `ATS/` — perfil ATS real para fixture derivada
- `ETS/` — perfil ETS2 real para fixture derivada
- `TS.SE.Tool.0.3.11.0/` — distribuição compilada funcional
- `TS.SE.Tool.vs.0.3.11.0/` — código-fonte C# legado

Nunca modifique os perfis de referência in-place.

## Desenvolvimento
Leia `AGENTS.md` e depois `PROJECT.md`. Execute as tasks em ordem.

## Build
No PowerShell:

```powershell
./scripts/build-onefile.ps1
```

Saída esperada:

```text
dist/TS-SE-Tool.exe
```

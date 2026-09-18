# Task 13 — Windows one-file EXE

## Objetivo
Gerar um único `dist/TS-SE-Tool.exe` com PyInstaller `--onefile --windowed`.

## Requisitos
1. Criar helper `runtime_resources.py` para resolver recursos tanto no source quanto em `sys._MEIPASS`.
2. Remover dependência de diretórios `img/`, `lang/`, `gameref/` ao lado do exe; migrar recursos necessários para `src/tsse/resources` ou gerá-los internamente.
3. Se houver DLL/exe nativo indispensável, validar licença e empacotar via spec/hook `--add-binary`; em runtime usar caminho extraído pelo PyInstaller. Não deixar dependência externa obrigatória ao lado do exe.
4. Atualizar `scripts/build-onefile.ps1` se recursos/binaries exigirem `.spec` gerado e versionado (o `.gitignore` deve então liberar apenas esse spec).
5. Executar smoke test do exe em máquina Windows.
6. Validar abertura e leitura de CÓPIAS dos perfis ATS e ETS em `../../projeto_atual`.
7. Registrar tamanho final, tempo de startup e resultado dos testes em `tasks/reports/13.md`.

## Gate
Ruff, mypy, pytest, build one-file, smoke test e regressão de leitura/clonagem verdes.

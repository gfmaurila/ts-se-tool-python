# Arquitetura alvo

```text
src/
  tsse/
    core/{profiles,saves,sii,backup,cloning}/
    games/{ats,ets2}/
    application/
    infrastructure/{filesystem,decoder}/
    desktop/{windows,widgets,resources}/
tests/{unit,integration,fixtures}/
```

Dependências apontam para dentro: GUI/infrastructure → application/core. Core não conhece PySide6 nem PyInstaller.

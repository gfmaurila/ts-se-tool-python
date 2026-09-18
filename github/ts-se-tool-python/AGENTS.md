# AGENTS

## Missão
Reimplementar o comportamento útil do TS SE Tool 0.3.11.0 em Python, sem tradução mecânica de C#.

## Economia de contexto / RTK
- Leia somente a task atual e os arquivos diretamente necessários.
- Prefira `rtk`/saídas resumidas para buscas, testes e diffs.
- Não recarregue toda a árvore do legado a cada task.
- Registre mapeamentos descobertos em `docs/LEGACY-MAPPING.md` para reutilização.
- Execute testes focados durante desenvolvimento e suíte completa somente nos gates.

## Fontes locais
`../../projeto_atual/TS.SE.Tool.vs.0.3.11.0` = source C#.
`../../projeto_atual/TS.SE.Tool.0.3.11.0` = build antigo funcional.
`../../projeto_atual/ATS` e `../../projeto_atual/ETS` = perfis reais.

## Segurança de saves
Nunca escreva em `projeto_atual`. Copie fixtures para diretório temporário. Antes de gravar um perfil do usuário: backup, escrita temporária, validação e replace atômico.

## Build final
O produto final para Windows deve ser UM arquivo: `TS-SE-Tool.exe`. Não exigir Python instalado. Recursos próprios devem ser empacotados. Dependências nativas permitidas devem ser incorporadas ao bundle e acessadas por helper de runtime compatível com `sys._MEIPASS`.

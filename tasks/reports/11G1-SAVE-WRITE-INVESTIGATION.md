# Task 11G.1 — Save write pipeline investigation

Date: 2026-09-18

## Legacy TS SE Tool 0.3.11.0

The legacy save entry point is `Forms/FormMainControlsMethods.cs`, method
`buttonWriteSave_Click`. It copies the selected `game.sii` to
`game_backup.sii`, then calls `NewWrireSaveFile()`.

`MethodsReadWrite.cs:939-969` performs a last-write-time check, prepares the
in-memory model, and writes `SiiNunitData.PrintOut(0)` with:

```csharp
using (StreamWriter writer = new StreamWriter(SiiSavePath, false))
    writer.Write(SiiNunitData.PrintOut(0));
```

No encrypt, encode, ScsC, BSII, or external encoder call was found in this
write path. The legacy therefore writes plaintext SiiN directly and leaves any
later game-side conversion outside the tool. Its backup is a single fixed
`game_backup.sii` copy, overwritten by `File.Copy(..., true)`.

The legacy does have concurrent-modification detection through
`LastModifiedTimestamp`/`File.GetLastWriteTime` before writing, but its actual
write is not atomic and does not stage/reparse the candidate.

## SII_Decrypt evidence

The repository source artifact is
`.upstream-sii-decrypt/SII_Decrypt-v1.4.2-rc0`; the runtime adapter uses the
project-packaged SII_Decrypt 1.5.3 executable. The available upstream source
documents and exports provide:

- encrypted/plaintext/binary/3nK detection;
- `Decrypt*`, `Decode*`, and combined `DecryptAndDecode*` operations;
- output-file support for decoded/decrypted plaintext.

The exported API in `Headers/SII_Decrypt_Header.pas` and
`Library/SII_Decrypt_Library.pas` contains no `Encrypt*`, `Encode*`,
`ScsCCreate`, or `BSIIWrite` operation. `program_readme.txt` describes the
utility as decrypt/decode and says it converts binary saves to human-readable
text; it does not document a reverse encoder.

| Capability | Finding |
| --- | --- |
| decrypt | SUPPORTED |
| SiiN output | SUPPORTED as decoded/decrypted output |
| encrypt | NOT PROVIDED by inspected API |
| BSII encode | NOT PROVIDED |
| ScsC encode | NOT PROVIDED |

## ATS/ETS2 1.61 plaintext acceptance

The legacy writer is direct evidence that its own save workflow emits
plaintext SiiN. The SII_Decrypt documentation also describes plaintext output
and says users no longer need to change `g_save_format` merely to decode binary
saves. Neither source proves that an unmodified ATS/ETS2 1.61 game will load a
manually replaced plaintext `game.sii` under every profile/configuration.

Classification: **NOT ESTABLISHED**. No real save or game profile was changed
in this investigation, and no controlled game launch was performed.

## `g_save_format`

The inspected sources identify result families (plaintext, encrypted, binary,
3nK) but do not establish a reliable local mapping of configuration values
`0`, `1`, and `2` to those families. The upstream README only states that
older workflows required changing `g_save_format`; it does not define the
numeric table. Therefore:

- `g_save_format = 0`: NOT ESTABLISHED from repository evidence;
- `g_save_format = 1`: NOT ESTABLISHED from repository evidence;
- `g_save_format = 2`: NOT ESTABLISHED from repository evidence.

No `config.cfg` was modified.

## Proposed safe pipeline (design only)

For a future opt-in write operation:

1. Acquire an exclusive/read snapshot of the original `game.sii`.
2. Create a uniquely named backup without overwriting prior backups.
3. Decode through `LegacySiiDecryptAdapter` into a local staging area.
4. Parse and edit the AST.
5. Serialize SiiN to a staging file.
6. Reparse the staging file and run domain/invariant validation.
7. Flush and `fsync` the staging file and directory where supported.
8. Recheck the original bytes/metadata for concurrent modification.
9. Atomically replace only after all checks pass.

The existing `SafeSaveWriter` supplies validated staged textual writing for
SiiN, but it currently targets known textual save files and does not establish
that replacing a ScsC/BSII original with plaintext is game-compatible. A
future game-save writer must preserve the original bytes until replacement is
approved and must expose the source format explicitly.

## Backup and rollback

Use a unique sibling backup such as `game.sii.tsse-backup-<timestamp>-<nonce>`;
never overwrite the only previous backup. On serialize, validation, reparse, or
concurrent-change failure, delete only the uncommitted staging file and leave
the original untouched. On replace failure, retain both original and staging
for recovery; do not silently retry over the original.

## Concurrent modification

Reuse the existing optimistic protection concept from `SafeSaveWriter`:
capture original bytes (and preferably mtime/size), validate the candidate,
then compare the source again immediately before replacement. Do not create a
second incompatible concurrency mechanism.

## QA profile plan

Future end-to-end validation must use dedicated `TSSE_TEST_ATS` and
`TSSE_TEST_ETS2` profiles, never the primary profiles: close the game, create or
copy a QA profile, record hashes, back up, change one easily visible field,
write only the QA save, launch the game, confirm load and the field, then
restore/remove the QA profile. This remains a future controlled test.

## Risks and unknowns

- Game acceptance of plaintext replacement is not proven for ATS/ETS2 1.61.
- Numeric `g_save_format` mapping is not established by the checked-in sources.
- No reverse ScsC/BSII encoder is available in SII_Decrypt artifacts.
- The legacy backup is fixed-name and overwrite-based, so it is not a safe
  model for the Python writer.

## Architectural decision

**NOT ESTABLISHED — further controlled game test required.**

No encoder was implemented, no real save/profile was written, and no
configuration was changed.
